"""Insert transcribed text wherever the cursor currently is.

Default mode copies the text to the clipboard and sends Ctrl+V, which works in
virtually every app and keeps focus in the user's target window (WisperLocal
never shows a focused window during dictation). The previous clipboard contents
are restored shortly afterwards.
"""

import datetime
import threading
import time
from pathlib import Path

import pyperclip
from pynput.keyboard import Controller, Key

_kb = Controller()

_TRANSCRIPT_DIR = Path(__file__).parent.parent / "Data" / "Raw Speech-to-Text Dictation"


def save_transcript(text: str) -> None:
    """Append *text* to today's transcript file in Data/Raw Speech-to-Text Dictation/."""
    try:
        _TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
        now = datetime.datetime.now()
        filename = now.strftime("%Y-%m-%d") + ".txt"
        timestamp = now.strftime("%H:%M:%S")
        with open(_TRANSCRIPT_DIR / filename, "a", encoding="utf-8") as fh:
            fh.write(f"[{timestamp}] {text.strip()}\n")
    except Exception as exc:
        print(f"[output] transcript save failed: {exc}")


def _send_ctrl_v() -> None:
    _kb.press(Key.ctrl)
    _kb.press("v")
    _kb.release("v")
    _kb.release(Key.ctrl)


def deliver(
    text: str,
    mode: str = "paste",
    restore_clipboard: bool = True,
    trailing_space: bool = True,
) -> None:
    if not text:
        return
    if trailing_space:
        text = text + " "

    if mode == "type":
        _kb.type(text)
        return

    # paste mode
    previous = None
    if restore_clipboard:
        try:
            previous = pyperclip.paste()
        except Exception:
            previous = None

    pyperclip.copy(text)
    time.sleep(0.05)  # let the clipboard settle before pasting
    _send_ctrl_v()

    if restore_clipboard:
        def _restore():
            time.sleep(0.4)  # wait until the paste has consumed the clipboard
            try:
                pyperclip.copy(previous if previous is not None else "")
            except Exception:
                pass

        threading.Thread(target=_restore, daemon=True).start()
