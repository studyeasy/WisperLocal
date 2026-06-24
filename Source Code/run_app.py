"""Frozen-app entry point (used by PyInstaller).

Installs a crash logger first so that a windowed (no-console) build still
records startup failures to %APPDATA%\\WisperLocal\\error.log.
"""

import os
import sys
import traceback
from pathlib import Path


def _log_path() -> Path:
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    return Path(base) / "WisperLocal" / "error.log"


def _excepthook(exctype, value, tb):
    try:
        path = _log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            traceback.print_exception(exctype, value, tb, file=fh)
    except Exception:
        pass
    sys.__excepthook__(exctype, value, tb)


sys.excepthook = _excepthook


def _selftest() -> int:
    """Headless validation of the frozen transcription pipeline (model load +
    CTranslate2 inference + ONNX VAD). Writes the outcome to selftest.log."""
    log = _log_path().with_name("selftest.log")
    try:
        import numpy as np

        from wisperlocal.transcriber import Transcriber, cuda_available

        tr = Transcriber("tiny.en", "cpu", "int8")
        text = tr.transcribe(np.zeros(16000, dtype=np.float32), language="en", vad_filter=True)
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(
            f"OK cuda={cuda_available()} device={tr.active_device} "
            f"compute={tr.active_compute} out={text!r}\n",
            encoding="utf-8",
        )
        return 0
    except Exception:
        log.parent.mkdir(parents=True, exist_ok=True)
        with open(log, "w", encoding="utf-8") as fh:
            fh.write("FAIL\n")
            traceback.print_exc(file=fh)
        return 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    try:
        from wisperlocal.app import main

        sys.exit(main())
    except SystemExit:
        raise
    except BaseException:
        _excepthook(*sys.exc_info())
        sys.exit(1)
