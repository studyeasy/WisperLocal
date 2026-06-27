"""Download Whisper models from the Hugging Face Hub with real progress.

faster-whisper downloads models silently on first use, which makes the app look
frozen for large models. This module pre-downloads a model with a byte-level
progress callback so the UI can show a percentage, then faster-whisper loads it
straight from the cache.
"""

import io
import os
import threading

import huggingface_hub
from faster_whisper.utils import _MODELS

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

# Same file set faster-whisper itself fetches (avoids pulling extra repo files).
_ALLOW = ["config.json", "preprocessor_config.json", "model.bin", "tokenizer.json", "vocabulary.*"]


def repo_for(name: str) -> str:
    return _MODELS.get(name, name)


def is_cached(name: str) -> bool:
    """True if the model is already in the local cache (no network)."""
    try:
        from faster_whisper import download_model

        download_model(name, local_files_only=True)
        return True
    except Exception:
        return False


class _Null(io.StringIO):
    def write(self, *_a, **_k):
        return 0

    def flush(self):
        pass


from tqdm import tqdm as _tqdm  # noqa: E402  (after _Null so the subclass can use it)


class _CallbackTqdm(_tqdm):
    """tqdm subclass that aggregates byte progress across all of a snapshot's
    per-file bars and forwards (downloaded, total) to a shared callback."""

    _lock = threading.Lock()
    _live: list = []
    _cb = None

    def __init__(self, *args, **kwargs):
        kwargs["disable"] = False     # must stay enabled so .n advances
        kwargs["file"] = _Null()      # ...but don't print to any console
        kwargs["mininterval"] = 0
        super().__init__(*args, **kwargs)
        with _CallbackTqdm._lock:
            _CallbackTqdm._live.append(self)

    def update(self, n=1):
        ret = super().update(n)
        self._emit()
        return ret

    def _emit(self):
        cb = _CallbackTqdm._cb
        if cb is None:
            return
        with _CallbackTqdm._lock:
            byte_bars = [t for t in _CallbackTqdm._live if getattr(t, "unit", "") == "B"]
            # Focus on substantial files (the weights) so the percentage isn't
            # skewed by tiny config files finishing first.
            big = [t for t in byte_bars if (t.total or 0) >= 524288]
            bars = big or byte_bars or _CallbackTqdm._live
            total = sum((t.total or 0) for t in bars)
            done = sum((t.n or 0) for t in bars)
        try:
            cb(done, total)
        except Exception:
            pass


def download(name: str, callback=None) -> None:
    """Download `name` (model size or repo id), reporting (done, total) bytes."""
    with _CallbackTqdm._lock:
        _CallbackTqdm._live = []
        _CallbackTqdm._cb = callback
    try:
        huggingface_hub.snapshot_download(
            repo_for(name),
            allow_patterns=_ALLOW,
            tqdm_class=_CallbackTqdm,
        )
    finally:
        with _CallbackTqdm._lock:
            _CallbackTqdm._cb = None
            _CallbackTqdm._live = []


def download_file(repo_id: str, filename: str, cache_dir: str, callback=None) -> None:
    """Download a single file from `repo_id` into `cache_dir`, reporting
    (done, total) bytes. Used for in-process LLM GGUF weights."""
    with _CallbackTqdm._lock:
        _CallbackTqdm._live = []
        _CallbackTqdm._cb = callback
    try:
        huggingface_hub.snapshot_download(
            repo_id,
            allow_patterns=[filename],
            cache_dir=cache_dir,
            tqdm_class=_CallbackTqdm,
        )
    finally:
        with _CallbackTqdm._lock:
            _CallbackTqdm._cb = None
            _CallbackTqdm._live = []
