"""Rolling history of recent transcriptions.

Every successful dictation is recorded here (independently of the optional
"save transcripts" setting) so users can recover text that failed to paste or
was lost when the clipboard got overwritten. Persisted as JSON in
%APPDATA%\\WisperLocal\\history.json, newest first, capped at MAX_ENTRIES.
"""

import json
import threading
import time

from .config import config_dir

MAX_ENTRIES = 50


class History:
    def __init__(self, path=None):
        self.path = path or (config_dir() / "history.json")
        self._lock = threading.Lock()
        self._entries: list[dict] = []  # newest first: {"ts": epoch-seconds, "text": str}
        self._load()

    def _load(self) -> None:
        try:
            if self.path.exists():
                with open(self.path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                if isinstance(data, list):
                    self._entries = [
                        e for e in data
                        if isinstance(e, dict) and isinstance(e.get("text"), str) and e["text"]
                    ][:MAX_ENTRIES]
        except Exception as exc:
            print(f"[history] failed to load: {exc}")

    def _save_locked(self) -> None:
        try:
            with open(self.path, "w", encoding="utf-8") as fh:
                json.dump(self._entries, fh, ensure_ascii=False, indent=1)
        except Exception as exc:
            print(f"[history] failed to save: {exc}")

    def add(self, text: str) -> None:
        text = (text or "").strip()
        if not text:
            return
        with self._lock:
            self._entries.insert(0, {"ts": time.time(), "text": text})
            del self._entries[MAX_ENTRIES:]
            self._save_locked()

    def entries(self) -> list[dict]:
        with self._lock:
            return list(self._entries)

    def clear(self) -> None:
        with self._lock:
            self._entries = []
            self._save_locked()
