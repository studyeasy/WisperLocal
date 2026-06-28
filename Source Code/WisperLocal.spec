# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec: bundles WisperLocal into dist/WisperLocal/.

Cross-platform: builds on Windows (.exe + Inno Setup installer) and is
structured so a macOS build (Metal) can be produced in CI. Platform-specific
hidden imports and the app icon are selected per OS.
"""

import os
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

# Bundle the Vulkan loader next to the GPU backend so it loads even on machines
# whose GPU driver didn't install one. With no GPU, Vulkan reports 0 devices and
# llama.cpp falls back to the (portable) CPU backend - so the build runs on any
# hardware: GPU-accelerated where a GPU is present, CPU everywhere else.
if sys.platform == "win32":
    for _cand in (
        os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "vulkan-1.dll"),
        os.path.join(os.environ.get("VULKAN_SDK", ""), "Bin", "vulkan-1.dll"),
    ):
        if _cand and os.path.exists(_cand):
            binaries += [(_cand, "llama_cpp/lib")]
            break

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
