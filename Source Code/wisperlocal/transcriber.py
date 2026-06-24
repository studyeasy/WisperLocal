"""faster-whisper wrapper with lazy model loading and CUDA->CPU fallback."""

import os
import threading

import numpy as np

# Quiet the benign "symlinks not supported" warning from huggingface_hub on
# Windows machines without Developer Mode (caching still works, just copies).
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

# Shown in the settings dropdown (label, value). ".en" models are English-only
# and noticeably faster/more accurate for English dictation.
MODEL_CHOICES = [
    ("Tiny (English, fastest)", "tiny.en"),
    ("Tiny (multilingual)", "tiny"),
    ("Base (English)", "base.en"),
    ("Base (multilingual)", "base"),
    ("Small (English, recommended)", "small.en"),
    ("Small (multilingual)", "small"),
    ("Medium (English)", "medium.en"),
    ("Medium (multilingual)", "medium"),
    ("Large v3 (most accurate)", "large-v3"),
    ("Large v3 Turbo (fast + accurate)", "large-v3-turbo"),
    ("Distil Large v3 (English, fast)", "distil-large-v3"),
]


def cuda_available() -> bool:
    try:
        import ctranslate2

        return ctranslate2.get_cuda_device_count() > 0
    except Exception:
        return False


def _resolve(device: str, compute_type: str) -> tuple[str, str]:
    if device == "auto":
        device = "cuda" if cuda_available() else "cpu"
    if compute_type == "auto":
        compute_type = "float16" if device == "cuda" else "int8"
    return device, compute_type


class Transcriber:
    def __init__(self, model="small.en", device="cpu", compute_type="auto", download_root=None):
        self.model_name = model
        self.device_pref = device
        self.compute_pref = compute_type
        self.download_root = download_root
        self._model = None
        self._lock = threading.RLock()
        self.active_device = None
        self.active_compute = None

    def configure(self, model: str, device: str, compute_type: str) -> None:
        """Update settings; drops the loaded model if anything relevant changed."""
        with self._lock:
            changed = (
                model != self.model_name
                or device != self.device_pref
                or compute_type != self.compute_pref
            )
            self.model_name = model
            self.device_pref = device
            self.compute_pref = compute_type
            if changed:
                self._model = None
                self.active_device = None
                self.active_compute = None

    def load(self) -> None:
        """Load the model, downloading on first use. Falls back to CPU if a GPU
        load fails (e.g. unsupported CUDA/driver combination)."""
        from faster_whisper import WhisperModel

        with self._lock:
            if self._model is not None:
                return
            device, compute_type = _resolve(self.device_pref, self.compute_pref)
            try:
                self._model = WhisperModel(
                    self.model_name,
                    device=device,
                    compute_type=compute_type,
                    download_root=self.download_root,
                )
                self.active_device, self.active_compute = device, compute_type
            except Exception as exc:
                if device != "cpu":
                    print(f"[transcriber] GPU load failed ({exc}); falling back to CPU.")
                    self._model = WhisperModel(
                        self.model_name,
                        device="cpu",
                        compute_type="int8",
                        download_root=self.download_root,
                    )
                    self.active_device, self.active_compute = "cpu", "int8"
                else:
                    raise

    def transcribe(
        self,
        audio: np.ndarray,
        language: str | None = None,
        vad_filter: bool = True,
        initial_prompt: str | None = None,
    ) -> str:
        if audio is None or len(audio) == 0:
            return ""
        self.load()
        with self._lock:
            model = self._model
        segments, _info = model.transcribe(
            audio,
            language=language,
            vad_filter=vad_filter,
            initial_prompt=initial_prompt or None,
            beam_size=5,
        )
        text = "".join(seg.text for seg in segments)
        return _clean(text)


def _clean(text: str) -> str:
    # Collapse whitespace/newlines into single spaces and trim.
    return " ".join(text.split()).strip()
