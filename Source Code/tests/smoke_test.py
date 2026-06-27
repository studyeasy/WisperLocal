"""Non-interactive validation of the WisperLocal pipeline.

Run from the project root with the venv python:
    .venv\\Scripts\\python.exe tests\\smoke_test.py
"""

import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ok = True


def phase(name):
    print(f"\n=== {name} ===", flush=True)


def check(label, got, expected):
    global ok
    status = "OK " if got == expected else "FAIL"
    if got != expected:
        ok = False
    print(f"  [{status}] {label}: {got!r}")


phase("1. import all modules")
try:
    from wisperlocal import (  # noqa: F401
        app, audio, config, controller, enhancer, formatting, hotkey, icons,
        main_window, output, overlay, settings_window, sounds, startup,
        transcriber, tray,
    )
    print("all modules imported OK")
except Exception:
    ok = False
    traceback.print_exc()

phase("2. config, hotkey, formatting")
try:
    from wisperlocal.config import Config
    from wisperlocal.formatting import format_text
    from wisperlocal.hotkey import parse_combo

    cfg = Config()
    print("hotkey:", cfg.get("hotkey"), "->", sorted(parse_combo(cfg.get("hotkey"))))
    check("capitalize+period", format_text("hello world. this is a test"),
          "Hello world. This is a test")
    check("spoken new line", format_text("first line new line second line"),
          "First line\nSecond line")
    check("filler + I", format_text("um i think it is good", remove_fillers=True),
          "I think it is good")

    from wisperlocal import enhancer
    cfg.set("ai_format", False)  # deterministic regardless of the saved user config
    check("enhance disabled = passthrough", enhancer.enhance_with_config("hello", cfg), "hello")
    cfg.set("ai_format", True)
    try:
        out = enhancer.enhance_with_config("hello there friend", cfg)
        print(f"  [OK ] enhancer ran (local model available): {out!r}")
    except enhancer.EnhancerError as exc:
        print(f"  [OK ] enhancer fell back (model not downloaded): {str(exc)[:50]}")
except Exception:
    ok = False
    traceback.print_exc()

phase("3. Qt app: controller + overlay + main window + tray")
try:
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication, QSystemTrayIcon

    from wisperlocal.controller import Controller
    from wisperlocal.main_window import MainWindow
    from wisperlocal.overlay import ListeningOverlay
    from wisperlocal.tray import TrayApp

    a = QApplication.instance() or QApplication(sys.argv)
    a.setQuitOnLastWindowClosed(False)
    print("system tray available:", QSystemTrayIcon.isSystemTrayAvailable())
    cfg = Config()
    ctl = Controller(cfg)
    ovl = ListeningOverlay(level_provider=lambda: 0.3)
    ovl.enabled = True
    win = MainWindow(cfg, ctl)
    tray_app = TrayApp(a, cfg, ctl, win)

    # exercise every overlay paint state through the event loop
    ovl.on_status("recording")
    QTimer.singleShot(200, lambda: ovl.on_status("transcribing"))
    QTimer.singleShot(350, lambda: ovl.on_status("enhancing"))
    QTimer.singleShot(550, lambda: ovl.on_status("idle"))
    QTimer.singleShot(800, lambda: (ctl.shutdown(), a.quit()))
    a.exec()
    print("Qt construct + overlay paint + teardown OK")
except Exception:
    ok = False
    traceback.print_exc()

phase("4. transcriber pipeline (tiny.en, synthetic audio)")
try:
    import numpy as np

    from wisperlocal.transcriber import Transcriber, cuda_available

    print("cuda_available:", cuda_available())
    tr = Transcriber(model="tiny.en", device="cpu", compute_type="int8")
    text = tr.transcribe(np.zeros(16000, dtype=np.float32), language="en")
    print("transcribe ran; output =", repr(text))
except Exception:
    ok = False
    traceback.print_exc()

print("\nRESULT:", "PASS" if ok else "FAIL", flush=True)
sys.exit(0 if ok else 1)
