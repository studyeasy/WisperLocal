# Releasing

A WisperLocal release is the Windows installer (`WisperLocal-Setup-X.Y.Z.exe`)
attached to a GitHub Release. End users only ever download that one file.

## Automated (recommended)

1. **Bump the version** in both places (they must match):
   - `wisperlocal/__init__.py` → `__version__`
   - `installer/WisperLocal.iss` → `#define MyAppVersion`
2. Add a section to **[CHANGELOG.md](../CHANGELOG.md)**.
3. Commit, tag, and push:
   ```bash
   git commit -am "Release v0.5.1"
   git tag v0.5.1
   git push origin main --tags
   ```
4. The **[release workflow](../.github/workflows/release.yml)** runs on the tag: it builds
   the app (PyInstaller) and the installer (Inno Setup) on a Windows runner, then
   publishes a GitHub Release with `WisperLocal-Setup-0.5.1.exe` attached and
   auto-generated notes.

That's it — the [Download](../README.md#-download) button (`../../releases/latest`) now points at it.

## Manual (from your machine)

```bash
scripts\build.bat
scripts\build-installer.bat
gh release create v0.5.1 installer_output\WisperLocal-Setup-0.5.1.exe -t "WisperLocal 0.5.1" -F CHANGELOG.md
```

## Notes

- **Versioning** follows [SemVer](https://semver.org): `MAJOR.MINOR.PATCH`. The build
  output and installer filename derive from the version, so keep the two files in sync.
- The installer is a **release asset**, never committed to the repo (it's ~93 MB; `.gitignore`
  excludes `dist/`, `build/`, and `installer_output/`).
- Whisper models and the optional Gemma LLM are **downloaded by the app on demand** — they
  are never part of a release, which is why the installer stays small.
