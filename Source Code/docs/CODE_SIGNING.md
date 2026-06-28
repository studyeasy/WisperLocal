# Code signing

The `WisperLocal-Setup-*.exe` installer is **self-signed**. That removes the
"Unknown publisher" warning **only on machines that trust the certificate** —
i.e. your own PCs, after a one-time import. For machines you don't control
(public download), self-signing does nothing; use a real certificate (see
[Public distribution](#public-distribution)).

## Why you see "Windows protected your PC"

Microsoft Defender SmartScreen flags any executable signed by a publisher it
doesn't recognise. An unsigned build shows **Unknown publisher**; a self-signed
build shows your name but is still untrusted until the certificate is imported.

To run it once without importing anything: on the SmartScreen dialog click
**More info → Run anyway**.

## Trust it on your own PCs (removes the warning)

Do this once per machine. It imports the **public** certificate
(`WisperLocal-CodeSigning.cer`, no private key) into the trust stores.

Open **PowerShell as Administrator** and run:

```powershell
Import-Certificate -FilePath "WisperLocal-CodeSigning.cer" -CertStoreLocation Cert:\LocalMachine\Root
Import-Certificate -FilePath "WisperLocal-CodeSigning.cer" -CertStoreLocation Cert:\LocalMachine\TrustedPublisher
```

After this, the signed installer (and any future signed build) runs without the
"Unknown publisher" warning on that machine. To undo it later, delete the
"WisperLocal" entries from those two stores (`certlm.msc`).

## Signing a build

`scripts\build-installer.bat` signs the installer automatically if a matching
certificate is present (it calls `scripts\sign.ps1`). To sign manually:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\sign.ps1 ..\WisperLocal-Setup-0.6.2.exe
```

### Creating the signing certificate (one time, on the build machine)

```powershell
$cert = New-SelfSignedCertificate -Type CodeSigningCert `
  -Subject "CN=WisperLocal, O=StudyEasy, E=studyeasyteam@gmail.com" `
  -KeyExportPolicy Exportable -KeyUsage DigitalSignature `
  -CertStoreLocation Cert:\CurrentUser\My -NotAfter (Get-Date).AddYears(5)
Export-Certificate -Cert $cert -FilePath WisperLocal-CodeSigning.cer   # public cert to share
```

The private key stays in `Cert:\CurrentUser\My` and is **never** committed. Only
the public `.cer` is distributed (so users can trust your signature).

## Public distribution

Self-signing can't earn SmartScreen trust for strangers. For that, sign with a
real certificate — the signing step is the same, only the certificate differs:

- **Azure Trusted Signing** (~$10/month) — cloud signing, good SmartScreen trust;
  best value for a small project.
- **EV code-signing certificate** (~$300–600/yr, hardware token) — instant
  SmartScreen reputation, no warnings.
- **OV code-signing certificate** — cheaper, but SmartScreen may still warn until
  the app builds download reputation.
