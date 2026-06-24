"""Core orchestration: hotkey -> record -> transcribe -> paste.

Runs as a QObject so it can emit Qt signals to update the tray UI safely from
worker threads. Hotkey callbacks (on pynput's thread) only kick off quick
actions; the blocking transcription runs on a dedicated worker thread.
"""

import threading

from PySide6.QtCore import QObject, Signal

from . import downloads, enhancer, formatting, sounds
from .audio import Recorder
from .hotkey import HotkeyManager
from .output import deliver, save_transcript
from .transcriber import Transcriber


class Controller(QObject):
    # recording lifecycle: idle | recording | transcribing | error
    statusChanged = Signal(str)
    # model lifecycle: loading | downloading | ready | error
    modelStatusChanged = Signal(str)
    # download progress text while a model is being fetched
    modelProgress = Signal(str)
    # transient human-readable messages for balloon tips / logging
    info = Signal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.recorder = Recorder(device=config.get("input_device"))
        self.transcriber = Transcriber(
            model=config.get("model"),
            device=config.get("device"),
            compute_type=config.get("compute_type"),
        )
        self.state = "idle"
        self.model_ready = False
        self._lock = threading.Lock()
        self._preload_lock = threading.Lock()
        self._last_dl_pct = -1
        self.hotkey: HotkeyManager | None = None
        self._install_hotkey()

    # ------------------------------------------------------------------ setup
    def _install_hotkey(self) -> None:
        if self.hotkey is not None:
            self.hotkey.stop()
        combo = self.config.get("hotkey")
        if self.config.get("record_mode") == "push_to_talk":
            self.hotkey = HotkeyManager(combo, on_activate=self._ptt_start, on_deactivate=self._ptt_stop)
        else:
            self.hotkey = HotkeyManager(combo, on_activate=self._toggle)
        self.hotkey.start()

    def apply_settings(self) -> None:
        """Re-read config after the settings dialog saves."""
        self.recorder.device = self.config.get("input_device")
        self.transcriber.configure(
            self.config.get("model"),
            self.config.get("device"),
            self.config.get("compute_type"),
        )
        self.model_ready = False
        self._install_hotkey()
        self.preload_model()

    def preload_model(self) -> None:
        threading.Thread(target=self._preload_worker, daemon=True).start()

    def _preload_worker(self) -> None:
        with self._preload_lock:
            name = self.config.get("model")
            self.model_ready = False
            if not downloads.is_cached(name):
                self._last_dl_pct = -1
                self.modelStatusChanged.emit("downloading")
                self.modelProgress.emit(f"Downloading {name}...")
                try:
                    downloads.download(name, self._on_dl_progress)
                except Exception as exc:
                    self.modelStatusChanged.emit("error")
                    self.info.emit(f"Model download failed: {exc}")
                    return
            self.modelStatusChanged.emit("loading")
            try:
                self.transcriber.load()
                self.model_ready = True
                dev = self.transcriber.active_device or "cpu"
                self.modelStatusChanged.emit("ready")
                self.info.emit(f"Model '{name}' ready ({dev}).")
                self._prewarm_enhancer()
            except Exception as exc:
                self.model_ready = False
                self.modelStatusChanged.emit("error")
                self.info.emit(f"Model load failed: {exc}")

    def _on_dl_progress(self, done, total) -> None:
        if total:
            pct = int(done * 100 / total)
            if pct == self._last_dl_pct:
                return
            self._last_dl_pct = pct
            mb = 1048576
            self.modelProgress.emit(
                f"Downloading {self.config.get('model')}... {pct}% ({done // mb}/{total // mb} MB)"
            )
        else:
            self.modelProgress.emit(f"Downloading {self.config.get('model')}...")

    def _prewarm_enhancer(self) -> None:
        """Load the LLM into memory in the background so the first enhanced
        dictation isn't delayed by a cold model load."""
        if not self.config.get("ai_format"):
            return

        def _warm():
            try:
                enhancer.OllamaEnhancer(
                    url=self.config.get("ai_url"),
                    model=self.config.get("ai_model"),
                    device=self.config.get("ai_device"),
                    timeout=self.config.get("ai_timeout"),
                ).enhance("ok")
            except Exception:
                pass

        threading.Thread(target=_warm, daemon=True).start()

    # ------------------------------------------------------------- hotkey API
    def _toggle(self) -> None:
        with self._lock:
            state = self.state
        if state == "recording":
            self._stop_and_transcribe()
        elif state == "idle":
            self._start()
        # transcribing -> ignore (busy)

    def _ptt_start(self) -> None:
        with self._lock:
            idle = self.state == "idle"
        if idle:
            self._start()

    def _ptt_stop(self) -> None:
        with self._lock:
            recording = self.state == "recording"
        if recording:
            self._stop_and_transcribe()

    def toggle(self) -> None:
        """Public entry point (tray menu)."""
        self._toggle()

    def confirm(self) -> None:
        """Stop recording and transcribe now (overlay insert button)."""
        with self._lock:
            recording = self.state == "recording"
        if recording:
            self._stop_and_transcribe()

    def cancel(self) -> None:
        """Discard the current recording without transcribing (overlay cancel)."""
        with self._lock:
            recording = self.state == "recording"
        if not recording:
            return
        self.recorder.stop()
        if self.config.get("play_sounds"):
            sounds.stop()
        self.info.emit("Canceled.")
        self._set_state("idle")

    def current_language(self):
        """Language code to pass to Whisper, or None for auto-detect."""
        model = self.config.get("model")
        if model.endswith(".en"):
            return "en"
        lang = self.config.get("language")
        return None if lang in (None, "", "auto") else lang

    # --------------------------------------------------------------- internals
    def _set_state(self, state: str) -> None:
        with self._lock:
            self.state = state
        self.statusChanged.emit(state)

    def _start(self) -> None:
        try:
            self.recorder.start()
        except Exception as exc:
            self.info.emit(f"Microphone error: {exc}")
            self._set_state("error")
            if self.config.get("play_sounds"):
                sounds.error()
            return
        self._set_state("recording")
        if self.config.get("play_sounds"):
            sounds.start()

    def _stop_and_transcribe(self) -> None:
        audio = self.recorder.stop()
        if self.config.get("play_sounds"):
            sounds.stop()

        min_samples = int(self.config.get("min_record_ms", 250) / 1000.0 * 16000)
        if len(audio) < min_samples:
            self.info.emit("Recording too short - ignored.")
            self._set_state("idle")
            return

        if not self.model_ready:
            self.info.emit("Model is still preparing - please wait for 'Ready'.")
            self._set_state("idle")
            return

        self._set_state("transcribing")
        threading.Thread(target=self._transcribe_worker, args=(audio,), daemon=True).start()

    def _transcribe_worker(self, audio) -> None:
        try:
            text = self.transcriber.transcribe(
                audio,
                language=self.current_language(),
                vad_filter=self.config.get("vad_filter"),
                initial_prompt=self.config.get("initial_prompt"),
            )
            self.model_ready = True
            text = formatting.format_with_config(text, self.config)

            if text and self.config.get("ai_format"):
                self._set_state("enhancing")
                try:
                    text = enhancer.enhance_with_config(text, self.config)
                except enhancer.EnhancerError as exc:
                    self.info.emit(f"Enhance skipped: {exc}")

            if text:
                deliver(
                    text,
                    mode=self.config.get("output_mode"),
                    restore_clipboard=self.config.get("restore_clipboard"),
                    trailing_space=self.config.get("trailing_space"),
                )
                if self.config.get("save_transcripts"):
                    save_transcript(text)
                self.info.emit(f"Inserted: {text[:80]}")
                if self.config.get("play_sounds"):
                    sounds.done()
            else:
                self.info.emit("No speech detected.")
            self._set_state("idle")
        except Exception as exc:
            self.info.emit(f"Transcription error: {exc}")
            if self.config.get("play_sounds"):
                sounds.error()
            self._set_state("error")

    def shutdown(self) -> None:
        if self.hotkey is not None:
            self.hotkey.stop()
        if self.recorder.is_recording:
            self.recorder.stop()
