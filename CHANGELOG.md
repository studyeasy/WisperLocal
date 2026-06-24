# Changelog

All notable changes to WisperLocal are documented here.
This project follows [Semantic Versioning](https://semver.org).

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
