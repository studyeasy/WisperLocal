# Changelog

All notable changes to WisperLocal are documented here.
This project follows [Semantic Versioning](https://semver.org).

## [0.6.4] - 2026-07-18
### Added
- **Transcription history (`Ctrl+Alt+V`)**: every dictation is now saved to a rolling 50-entry history (`%APPDATA%\WisperLocal\history.json`) — recorded *before* pasting, so text survives even a failed paste. Press `Ctrl+Alt+V` (configurable via `history_hotkey`) or use the tray menu to open a viewer that previews past transcriptions and copies any of them back to the clipboard.
### Fixed
- **Hotkey no longer goes unresponsive.** Hotkey callbacks used to run on the Windows keyboard-hook thread while doing slow work; when that exceeded the hook timeout, Windows silently dropped key-release events and the app believed the combo was still held — `Ctrl+Alt+W` then did nothing until you clicked the overlay's ✕. Callbacks now run on a dispatcher thread, and tracked key state self-heals against the real keyboard state (`GetAsyncKeyState`).
- **Paste no longer picks up old clipboard fragments.** The synthetic `Ctrl+V` is now sent only after you've physically released Ctrl/Alt/Shift/Win (so the target app doesn't receive `Ctrl+Alt+V` or Alt-menu keystrokes), and the previous clipboard is restored after 1.5s instead of 0.6s so slow apps can't read the old contents mid-paste.

## [0.6.3] - 2026-06-29
### Added
- **Publisher identity**: the installer and code-signing certificate now identify the publisher as **Chaand Sheikh**, and the home window shows a credit with a link to [linkedin.com/in/chand-sheikh](https://www.linkedin.com/in/chand-sheikh/).
### Changed
- **Faster, steadier transcription**: Whisper no longer conditions each window on previous text — for short dictation this removes a common cause of repeated/hallucinated phrases on pauses and shaves latency.
- **Faster, deterministic enhancement**: the punctuation LLM now decodes greedily (temperature 0) — same input, same output, slightly quicker, and fewer cases where a random drift made WisperLocal fall back to the raw text.
- The enhancer no longer re-scans the model cache on disk for every dictation (the model path is memoized).
### Fixed
- **Transcript history now saves to `%APPDATA%\WisperLocal\Data`** in the installed app instead of a folder buried inside the install directory — so saved dictations survive upgrades and uninstalls. (Running from source still uses the repo's `Data/` folder.)

## [0.6.2] - 2026-06-28
### Added
- **GPU acceleration with automatic CPU fallback.** Enhanced writing now runs on the GPU when one is present — via the cross-vendor **Vulkan** backend (NVIDIA, AMD, Intel) — and falls back to the CPU otherwise. The hardware is detected automatically: model layers are offloaded to the GPU, and if there's no GPU (or it can't initialize) it runs on the CPU. The CPU backend is still built portably (no AVX2), so the same installer runs on any x86-64 machine, with or without a GPU.

## [0.6.1] - 2026-06-28
### Fixed
- **Enhanced writing crashed on some PCs** with "Failed to load model: WinError -1073741795 (0xC000001D)". The bundled LLM library used a prebuilt wheel compiled for AVX2; CPUs without AVX2 hit an illegal instruction. The library is now built from source with AVX/AVX2/AVX-512 disabled, so it runs on **any x86-64 CPU**.
### Added
- The LLM now **auto-offloads to the GPU** when a GPU-capable build is installed (falls back to CPU otherwise), so the same model runs GPU-accelerated where a GPU is present and on CPU everywhere else. Cross-vendor GPU (Vulkan) and macOS (Metal) builds are produced per-target.

## [0.6.0] - 2026-06-25
### Changed
- **Enhanced writing now runs fully in-process — Ollama is no longer required.** The previous version depended on a separate Ollama server that often wasn't running, so enhancement silently failed. WisperLocal now runs a small quantized LLM directly inside the app via llama.cpp.
- **Pick your model in Settings.** A dropdown offers lightweight options — Qwen2.5 0.5B (default, fastest), Llama 3.2 1B, Qwen2.5 1.5B, and Google Gemma 2 2B. The chosen model downloads automatically from Hugging Face on first use, is cached locally, and then runs offline.
### Removed
- The Ollama install step in the installer and all Ollama-related settings (server URL, etc.).

## [0.5.2] - 2026-06-25
### Fixed
- **Enhanced writing no longer pastes extra text.** Small local models sometimes prepend a preamble (e.g. "Here is the corrected text: …") or add trailing commentary; WisperLocal now keeps only the words that match your transcription and discards anything the model added in front or after. If the model rewrites the words entirely, it falls back to your original text.
- **Paste inserts only the transcription.** The clipboard is now verified to hold exactly the transcribed text before pasting, so a slow clipboard write can no longer cause the previous clipboard contents to be pasted too. Falls back to typing if the clipboard can't be confirmed.

## [0.5.1] - 2026-06-24
### Changed
- **Enhanced writing is now conservative**: the local LLM (Gemma) only fixes punctuation and capitalization. It no longer rewrites, rephrases, or reorders your words — the speech-to-text output stays exactly as spoken, just with proper punctuation. If the model strays, WisperLocal falls back to your original text.

## [0.5.0] - 2026-06-24
### Added
- On-demand Whisper model downloads with a live **progress bar** in the home window and tray — switching to a larger model no longer looks frozen.
- LLM **pre-warming**: when enhanced writing is on, the model loads in the background so your first enhanced dictation isn't slow.
### Changed
- Enhanced-writing timeout raised to 120 s to absorb the first cold model load.
- Dictation now waits for the model to be ready instead of appearing to hang.

## [0.4.0] - 2026-06-24
### Added
- The installer can **download and install Ollama** during setup (optional, default-checked) for one-click AI enhancement.
- One-click **"Download model"** button in Settings (streams pull progress).

## [0.3.0] - 2026-06-23
### Added
- **Enhanced Writing**: optional polish of the transcript with a small local LLM (Gemma via Ollama), on CPU or GPU. Off by default, with a Settings "Test" button.

## [0.2.0] - 2026-06-23
### Added
- Floating **listening overlay** with a live waveform and cancel / insert buttons.
- **Home / onboarding window** with a one-click "Test my system".
- Built-in **offline formatting**: capitalization, spoken commands ("new line", "new paragraph", "bullet point"), and optional filler removal.

## [0.1.0] - 2026-06-23
### Added
- Initial release: global-hotkey dictation, local faster-whisper transcription, paste-at-cursor, system tray + settings, CPU/GPU, model picker, toggle / push-to-talk, start-with-Windows.
- PyInstaller build + per-user Inno Setup installer.
