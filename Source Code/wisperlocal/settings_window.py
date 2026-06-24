"""Settings dialog: model, hotkey, device, mic and behaviour options."""

import threading

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QKeySequenceEdit,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from . import startup
from .transcriber import MODEL_CHOICES, cuda_available

DEVICE_CHOICES = [("CPU", "cpu"), ("GPU (CUDA)", "cuda"), ("Auto", "auto")]
RECORD_MODES = [("Toggle (press to start, press to stop)", "toggle"),
                ("Push-to-talk (hold the hotkey)", "push_to_talk")]
OUTPUT_MODES = [("Paste (clipboard + Ctrl+V)", "paste"),
                ("Type characters", "type")]
LANGUAGES = [
    ("Auto detect", "auto"), ("English", "en"), ("Spanish", "es"), ("French", "fr"),
    ("German", "de"), ("Hindi", "hi"), ("Italian", "it"), ("Portuguese", "pt"),
    ("Dutch", "nl"), ("Japanese", "ja"), ("Chinese", "zh"), ("Korean", "ko"),
    ("Russian", "ru"), ("Arabic", "ar"),
]
AI_DEVICE_CHOICES = [("Auto (Ollama decides)", "auto"), ("CPU", "cpu"), ("GPU", "gpu")]


def _seq_to_combo(seq: QKeySequence) -> str:
    text = seq.toString(QKeySequence.PortableText)
    if not text:
        return ""
    # QKeySequenceEdit can hold a multi-chord sequence; keep the first chord.
    text = text.split(",")[0].strip().lower()
    text = text.replace("meta", "win")
    return text


def _combo_to_seq(combo: str) -> QKeySequence:
    parts = [p for p in combo.lower().replace(" ", "").split("+") if p]
    parts = ["Meta" if p == "win" else p.capitalize() for p in parts]
    return QKeySequence("+".join(parts))


def _list_input_devices() -> list[tuple[str, object]]:
    devices: list[tuple[str, object]] = [("System default", None)]
    try:
        import sounddevice as sd

        for idx, dev in enumerate(sd.query_devices()):
            if dev.get("max_input_channels", 0) > 0:
                devices.append((f"{idx}: {dev['name']}", idx))
    except Exception as exc:
        print(f"[settings] could not list audio devices: {exc}")
    return devices


def _fill(combo: QComboBox, choices: list[tuple[str, object]], current) -> None:
    combo.clear()
    select = 0
    for i, (label, value) in enumerate(choices):
        combo.addItem(label, value)
        if value == current:
            select = i
    combo.setCurrentIndex(select)


class SettingsWindow(QWidget):
    saved = Signal()
    _sigAiStatus = Signal(str, bool)
    _sigAiDone = Signal()

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setWindowTitle("WisperLocal Settings")
        self.setMinimumWidth(460)

        form = QFormLayout()

        self.model_combo = QComboBox()
        _fill(self.model_combo, MODEL_CHOICES, config.get("model"))
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
        form.addRow("Whisper model", self.model_combo)

        self.device_combo = QComboBox()
        gpu_note = "" if cuda_available() else "  (no CUDA GPU detected - will use CPU)"
        _fill(self.device_combo, DEVICE_CHOICES, config.get("device"))
        form.addRow("Processing", self.device_combo)
        if gpu_note:
            note = QLabel(gpu_note.strip())
            note.setStyleSheet("color: #888; font-size: 11px;")
            form.addRow("", note)

        self.lang_combo = QComboBox()
        _fill(self.lang_combo, LANGUAGES, config.get("language"))
        form.addRow("Language", self.lang_combo)

        self.mic_combo = QComboBox()
        _fill(self.mic_combo, _list_input_devices(), config.get("input_device"))
        form.addRow("Microphone", self.mic_combo)

        self.hotkey_edit = QKeySequenceEdit()
        self.hotkey_edit.setKeySequence(_combo_to_seq(config.get("hotkey")))
        try:
            self.hotkey_edit.setMaximumSequenceLength(1)  # single combo, not a chord
        except (AttributeError, TypeError):
            pass  # older Qt without this method
        form.addRow("Hotkey", self.hotkey_edit)

        self.mode_combo = QComboBox()
        _fill(self.mode_combo, RECORD_MODES, config.get("record_mode"))
        form.addRow("Record mode", self.mode_combo)

        self.output_combo = QComboBox()
        _fill(self.output_combo, OUTPUT_MODES, config.get("output_mode"))
        form.addRow("Insert via", self.output_combo)

        self.prompt_edit = QLineEdit(config.get("initial_prompt") or "")
        self.prompt_edit.setPlaceholderText("Optional: names/jargon to spell correctly")
        form.addRow("Vocabulary hint", self.prompt_edit)

        self.cb_vad = QCheckBox("Trim silence (voice activity filter)")
        self.cb_vad.setChecked(bool(config.get("vad_filter")))
        self.cb_space = QCheckBox("Add a trailing space after text")
        self.cb_space.setChecked(bool(config.get("trailing_space")))
        self.cb_restore = QCheckBox("Restore clipboard after pasting")
        self.cb_restore.setChecked(bool(config.get("restore_clipboard")))
        self.cb_sounds = QCheckBox("Play start/stop sounds")
        self.cb_sounds.setChecked(bool(config.get("play_sounds")))
        self.cb_overlay = QCheckBox("Show the floating listening overlay")
        self.cb_overlay.setChecked(bool(config.get("show_overlay")))
        self.cb_startup = QCheckBox("Start WisperLocal when Windows starts")
        self.cb_startup.setChecked(startup.is_enabled())
        self.cb_save_transcripts = QCheckBox("Save transcripts to Data/Raw Speech-to-Text Dictation/")
        self.cb_save_transcripts.setChecked(bool(config.get("save_transcripts")))

        self.cb_capitalize = QCheckBox('Auto-capitalize sentences and "I"')
        self.cb_capitalize.setChecked(bool(config.get("auto_capitalize")))
        self.cb_commands = QCheckBox('Spoken commands: "new line", "new paragraph", "bullet point"')
        self.cb_commands.setChecked(bool(config.get("spoken_commands")))
        self.cb_fillers = QCheckBox("Remove filler words (um, uh, erm)")
        self.cb_fillers.setChecked(bool(config.get("remove_fillers")))

        self._on_model_changed()

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        for cb in (self.cb_vad, self.cb_space, self.cb_restore, self.cb_sounds,
                   self.cb_overlay, self.cb_startup, self.cb_save_transcripts):
            layout.addWidget(cb)
        fmt_label = QLabel("Formatting")
        fmt_label.setStyleSheet("font-weight: 600; margin-top: 6px;")
        layout.addWidget(fmt_label)
        for cb in (self.cb_capitalize, self.cb_commands, self.cb_fillers):
            layout.addWidget(cb)

        layout.addWidget(self._build_ai_group(config))
        self._sigAiStatus.connect(self._on_ai_status)
        self._sigAiDone.connect(self._on_ai_done)

        hint = QLabel("The selected model downloads automatically the first time it is used.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(hint)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.close)
        save = QPushButton("Save")
        save.setDefault(True)
        save.clicked.connect(self._on_save)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)

    def _on_model_changed(self) -> None:
        model = self.model_combo.currentData()
        is_english_only = bool(model) and model.endswith(".en")
        self.lang_combo.setEnabled(not is_english_only)
        self.lang_combo.setToolTip(
            "English-only model: language is fixed to English." if is_english_only else ""
        )

    def _build_ai_group(self, config) -> QGroupBox:
        group = QGroupBox("Enhanced writing (AI) - optional, runs locally")
        ai_form = QFormLayout(group)

        self.cb_ai = QCheckBox("Enable enhanced writing (polish text with a local LLM)")
        self.cb_ai.setChecked(bool(config.get("ai_format")))
        ai_form.addRow(self.cb_ai)

        self.ai_model_edit = QLineEdit(config.get("ai_model") or "gemma3:1b")
        ai_form.addRow("Model", self.ai_model_edit)

        self.ai_device_combo = QComboBox()
        _fill(self.ai_device_combo, AI_DEVICE_CHOICES, config.get("ai_device"))
        ai_form.addRow("Run on", self.ai_device_combo)

        self.ai_url_edit = QLineEdit(config.get("ai_url") or "http://localhost:11434")
        ai_form.addRow("Ollama URL", self.ai_url_edit)

        self.ai_instr_edit = QLineEdit(config.get("ai_instructions") or "")
        self.ai_instr_edit.setPlaceholderText("Optional extra style instructions")
        ai_form.addRow("Style note", self.ai_instr_edit)

        test_row = QHBoxLayout()
        self.ai_test_btn = QPushButton("Test")
        self.ai_test_btn.clicked.connect(self._test_ai)
        test_row.addWidget(self.ai_test_btn)
        self.ai_dl_btn = QPushButton("Download model")
        self.ai_dl_btn.clicked.connect(self._download_model)
        test_row.addWidget(self.ai_dl_btn)
        self.ai_status = QLabel("")
        self.ai_status.setWordWrap(True)
        test_row.addWidget(self.ai_status, 1)
        ai_form.addRow(test_row)

        help_lbl = QLabel(
            'Needs <a href="https://ollama.com">Ollama</a>: install it, then run '
            "<code>ollama pull gemma3:1b</code>. Off by default - set it up and test here first."
        )
        help_lbl.setOpenExternalLinks(True)
        help_lbl.setWordWrap(True)
        help_lbl.setStyleSheet("color:#888; font-size:11px;")
        ai_form.addRow(help_lbl)
        return group

    def _set_ai_busy(self, busy: bool) -> None:
        self.ai_test_btn.setEnabled(not busy)
        self.ai_dl_btn.setEnabled(not busy)

    def _test_ai(self) -> None:
        self._set_ai_busy(True)
        self.ai_status.setStyleSheet("color:#555;")
        self.ai_status.setText("Testing...")
        url = self.ai_url_edit.text().strip() or None
        model = self.ai_model_edit.text().strip() or None
        device = self.ai_device_combo.currentData()
        threading.Thread(target=self._test_ai_worker, args=(url, model, device), daemon=True).start()

    def _test_ai_worker(self, url, model, device) -> None:
        from . import enhancer

        try:
            eng = enhancer.OllamaEnhancer(url=url, model=model, device=device)
            ok, msg = eng.available()
            if not ok:
                self._sigAiStatus.emit(msg, False)
                return
            out = eng.enhance("so basically um i think we should ship this on friday and tell the team")
            self._sigAiStatus.emit(f"OK - sample: {out}", True)
        except Exception as exc:
            self._sigAiStatus.emit(f"Failed: {exc}", False)
        finally:
            self._sigAiDone.emit()

    def _download_model(self) -> None:
        self._set_ai_busy(True)
        self.ai_status.setStyleSheet("color:#555;")
        self.ai_status.setText("Preparing download...")
        url = self.ai_url_edit.text().strip() or None
        model = self.ai_model_edit.text().strip() or None
        threading.Thread(target=self._download_model_worker, args=(url, model), daemon=True).start()

    def _download_model_worker(self, url, model) -> None:
        from . import enhancer

        eng = enhancer.OllamaEnhancer(url=url, model=model)
        if not eng.server_reachable():
            self._sigAiStatus.emit(
                "Ollama isn't running. Install it (the WisperLocal installer can) and start it, then retry.",
                False,
            )
            self._sigAiDone.emit()
            return

        last = [-1]

        def _progress(obj):
            total = obj.get("total") or 0
            done = obj.get("completed") or 0
            if total > 0:
                pct = int(done * 100 / total)
                if pct != last[0]:
                    last[0] = pct
                    self._sigAiStatus.emit(f"Downloading {model}... {pct}%", True)
            else:
                self._sigAiStatus.emit(f"{model}: {obj.get('status') or 'working'}", True)

        try:
            eng.pull_model(progress=_progress)
            self._sigAiStatus.emit(f"Model {model} is ready. Tick Enable, then Save.", True)
        except Exception as exc:
            self._sigAiStatus.emit(f"Download failed: {exc}", False)
        finally:
            self._sigAiDone.emit()

    def _on_ai_status(self, message: str, ok: bool) -> None:
        self.ai_status.setStyleSheet("color:#16A34A;" if ok else "color:#DC2626;")
        self.ai_status.setText(message)

    def _on_ai_done(self) -> None:
        self._set_ai_busy(False)

    def _on_save(self) -> None:
        combo = _seq_to_combo(self.hotkey_edit.keySequence())
        if not combo:
            combo = self.config.get("hotkey")  # keep previous if cleared

        self.config.update({
            "model": self.model_combo.currentData(),
            "device": self.device_combo.currentData(),
            "language": self.lang_combo.currentData(),
            "input_device": self.mic_combo.currentData(),
            "hotkey": combo,
            "record_mode": self.mode_combo.currentData(),
            "output_mode": self.output_combo.currentData(),
            "initial_prompt": self.prompt_edit.text().strip(),
            "vad_filter": self.cb_vad.isChecked(),
            "trailing_space": self.cb_space.isChecked(),
            "restore_clipboard": self.cb_restore.isChecked(),
            "play_sounds": self.cb_sounds.isChecked(),
            "launch_at_startup": self.cb_startup.isChecked(),
            "save_transcripts": self.cb_save_transcripts.isChecked(),
            "show_overlay": self.cb_overlay.isChecked(),
            "auto_capitalize": self.cb_capitalize.isChecked(),
            "spoken_commands": self.cb_commands.isChecked(),
            "remove_fillers": self.cb_fillers.isChecked(),
            "ai_format": self.cb_ai.isChecked(),
            "ai_model": self.ai_model_edit.text().strip() or "gemma3:1b",
            "ai_device": self.ai_device_combo.currentData(),
            "ai_url": self.ai_url_edit.text().strip() or "http://localhost:11434",
            "ai_instructions": self.ai_instr_edit.text().strip(),
        })
        self.config.save()

        try:
            startup.set_enabled(self.cb_startup.isChecked())
        except Exception as exc:
            print(f"[settings] startup toggle failed: {exc}")

        self.saved.emit()
        self.close()
