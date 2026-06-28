# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec: bundles WisperLocal into dist/WisperLocal/.

Cross-platform: builds on Windows (.exe + Inno Setup installer) and is
structured so a macOS build (Metal) can be produced in CI. Platform-specific
hidden imports and the app icon are selected per OS.
"""

import sys

from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = [], [], []

# Heavy native packages that need their DLLs/data collected explicitly.
# llama_cpp ships the llama.cpp shared library + chat-template data files.
for pkg in ("faster_whisper", "ctranslate2", "onnxruntime", "av", "sounddevice", "llama_cpp"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

# pynput's backend modules are platform-specific and must be hinted explicitly.
if sys.platform == "win32":
    hiddenimports += ["pynput.keyboard._win32", "pynput.mouse._win32"]
elif sys.platform == "darwin":
    hiddenimports += ["pynput.keyboard._darwin", "pynput.mouse._darwin"]

_icon = "assets/icon.ico" if sys.platform == "win32" else None

a = Analysis(
    ["run_app.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="WisperLocal",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon=_icon,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="WisperLocal",
)

# On macOS, wrap the collected app into a proper .app bundle.
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="WisperLocal.app",
        icon=None,
        bundle_identifier="com.studyeasy.wisperlocal",
    )
