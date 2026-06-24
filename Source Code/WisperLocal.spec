# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec: bundles WisperLocal into dist/WisperLocal/."""

from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = [], [], []

# Heavy native packages that need their DLLs/data collected explicitly.
for pkg in ("faster_whisper", "ctranslate2", "onnxruntime", "av", "sounddevice"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

hiddenimports += ["pynput.keyboard._win32", "pynput.mouse._win32"]

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
    icon="assets/icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="WisperLocal",
)
