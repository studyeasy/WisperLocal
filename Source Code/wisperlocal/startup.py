"""Enable/disable 'start with Windows' by dropping a launcher in the user's
Startup folder. Uses a hidden VBS shim so no console window appears."""

import os
import sys
from pathlib import Path

from . import APP_NAME


def _startup_dir() -> Path:
    appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
    return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def _launcher_path() -> Path:
    return _startup_dir() / f"{APP_NAME}.vbs"


def _pythonw() -> str:
    exe = Path(sys.executable)
    candidate = exe.with_name("pythonw.exe")
    return str(candidate if candidate.exists() else exe)


def _project_dir() -> str:
    # parent of the `wisperlocal` package directory
    return str(Path(__file__).resolve().parent.parent)


def is_enabled() -> bool:
    return _launcher_path().exists()


def set_enabled(enable: bool) -> None:
    launcher = _launcher_path()
    if enable:
        launcher.parent.mkdir(parents=True, exist_ok=True)
        pythonw = _pythonw().replace("\\", "\\\\")
        project = _project_dir().replace("\\", "\\\\")
        vbs = (
            'Set sh = CreateObject("WScript.Shell")\r\n'
            f'sh.CurrentDirectory = "{project}"\r\n'
            f'sh.Run """{pythonw}"" -m wisperlocal", 0, False\r\n'
        )
        launcher.write_text(vbs, encoding="utf-8")
    else:
        try:
            if launcher.exists():
                launcher.unlink()
        except Exception as exc:
            print(f"[startup] failed to remove launcher: {exc}")
