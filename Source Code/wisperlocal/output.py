"""Insert transcribed text wherever the cursor currently is.

Default mode copies the text to the clipboard and sends Ctrl+V, which works in
virtually every app and keeps focus in the user's target window (WisperLocal
never shows a focused window during dictation). The previous clipboard contents
are restored shortly afterwards.

To guarantee that *only* the freshly transcribed text is pasted, we confirm the
clipboard actually holds exactly that text before sending Ctrl+V (otherwise a
slow clipboard write could let the previous clipboard contents be pasted). If
the clipboard can't be confirmed, we type the text directly instead of risking
a stale paste.
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


def _set_clipboard(text: str, attempts: int = 12, interval: float = 0.03) -> bool:
    """Put *text* on the clipboard and confirm it reads back exactly.

    Returns True once the clipboard holds our text, False if it never does.
    This is what stops a slow clipboard write from letting the *previous*
    clipboard contents be pasted instead of (or alongside) the transcription.
    """
    for _ in range(attempts):
        try:
            pyperclip.copy(text)
            if pyperclip.paste() == text:
                return True
        except Exception:
            return False
        time.sleep(interval)
    return False


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

    # Only paste once we've confirmed the clipboard holds EXACTLY our text. If
    # we can't confirm it, type the text instead of risking a stale paste that
    # would insert the previous clipboard contents.
    if not _set_clipboard(text):
        _kb.type(text)
        return

    _send_ctrl_v()

    if restore_clipboard:
        def _restore():
            time.sleep(0.6)  # give the target app time to consume the paste
            try:
                # Only restore if our text is still on the clipboard. If the user
                # copied something new in the meantime, leave it untouched.
                if pyperclip.paste() == text:
                    pyperclip.copy(previous if previous is not None else "")
            except Exception:
                pass

        threading.Thread(target=_restore, daemon=True).start()
