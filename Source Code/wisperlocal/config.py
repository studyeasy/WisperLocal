"""Persistent settings stored in %APPDATA%\\WisperLocal\\config.json."""

import copy
import json
import os
from pathlib import Path

from . import APP_NAME

DEFAULTS = {
    "model": "small.en",          # Whisper model name (see transcriber.MODEL_CHOICES)
    "device": "cpu",              # cpu | cuda | auto
    "compute_type": "auto",       # auto | int8 | int8_float16 | float16 | float32
    "language": "en",             # language code, or "auto" for detection
    "input_device": None,         # sounddevice input index, or None for system default
    "hotkey": "ctrl+alt+w",       # global hotkey combo
    "record_mode": "toggle",      # toggle | push_to_talk
    "output_mode": "paste",       # paste (clipboard+Ctrl+V) | type (char-by-char)
    "restore_clipboard": True,    # restore previous clipboard after pasting
    "trailing_space": True,       # append a space after inserted text
    "play_sounds": True,          # beep on start/stop
    "vad_filter": True,           # voice-activity filter to trim silence
    "initial_prompt": "",         # bias vocabulary / spelling (e.g. product names)
    "min_record_ms": 250,         # ignore recordings shorter than this
    "launch_at_startup": False,   # start with Windows
    "save_transcripts": False,    # append each dictation to Data/Raw Speech-to-Text Dictation/

    # UI
    "show_overlay": True,         # floating listening pill (waveform + cancel/insert)
    "first_run_done": False,      # has the welcome window been shown once

    # Formatting (post-processing applied to the raw transcript)
    "format_enabled": True,
    "auto_capitalize": True,      # sentence-start + standalone "I" capitalization
    "spoken_commands": True,      # "new line" / "new paragraph" / "bullet point"
    "remove_fillers": False,      # strip um / uh / erm ...
    # Enhanced writing - optional local-LLM polish (OFF by default).
    # Runs fully in-process via llama-cpp-python; no server/Ollama needed.
    "ai_format": False,           # master on/off
    "ai_model": "qwen2.5-0.5b",   # key into enhancer.MODELS (downloaded on demand)
    "ai_instructions": "",        # optional extra style guidance
}


def config_dir() -> Path:
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    path = Path(base) / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


class Config:
    """Dict-backed settings with JSON persistence and default fallback."""

    def __init__(self, path: Path | None = None):
        self.path = path or (config_dir() / "config.json")
        self._data = copy.deepcopy(DEFAULTS)
        self.load()

    def load(self) -> "Config":
        try:
            if self.path.exists():
                with open(self.path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                for key, value in data.items():
                    if key in DEFAULTS:
                        self._data[key] = value
        except Exception as exc:  # corrupt file -> fall back to defaults
            print(f"[config] failed to load, using defaults: {exc}")
        return self

    def save(self) -> None:
        try:
            with open(self.path, "w", encoding="utf-8") as fh:
                json.dump(self._data, fh, indent=2)
        except Exception as exc:
            print(f"[config] failed to save: {exc}")

    def get(self, key, default=None):
        return self._data.get(key, DEFAULTS.get(key, default))

    def set(self, key, value) -> None:
        self._data[key] = value

    def update(self, mapping: dict) -> None:
        for key, value in mapping.items():
            if key in DEFAULTS:
                self._data[key] = value

    def as_dict(self) -> dict:
        return copy.deepcopy(self._data)
