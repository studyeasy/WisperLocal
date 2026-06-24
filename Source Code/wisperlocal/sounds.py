"""Tiny non-blocking audio cues (Windows winsound)."""

import threading


def _beep(freq: int, dur_ms: int) -> None:
    def _run():
        try:
            import winsound

            winsound.Beep(freq, dur_ms)
        except Exception:
            pass

    threading.Thread(target=_run, daemon=True).start()


def start() -> None:
    _beep(880, 90)


def stop() -> None:
    _beep(620, 90)


def done() -> None:
    _beep(1040, 70)


def error() -> None:
    _beep(300, 200)
