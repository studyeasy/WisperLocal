# Changelog

All notable changes to WisperLocal are documented here.
This project follows [Semantic Versioning](https://semver.org).

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
