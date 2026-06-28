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

## Public distribution (the permanent fix — no popups for anyone)

Self-signing can't earn SmartScreen trust for strangers. For a real public fix
you need a certificate Microsoft trusts. Options, easiest/cheapest first:

| Option | Cost | Removes warning for everyone? | Friction |
|---|---|---|---|
| **Azure Trusted Signing** | ~$10/month | Yes (good standing) | Azure account + identity check; CI-native. **Recommended.** |
| **EV code-signing cert** | ~$300–600/yr | Yes, instantly | Hardware token (USB/HSM); org validation. |
| **OV code-signing cert** | ~$200–400/yr | Eventually | Warns until download reputation builds. |

### Setting up Azure Trusted Signing (recommended)

This is built into the release pipeline already — `.github/workflows/release.yml`
signs the installer with Trusted Signing automatically once it's configured.

1. Create/sign in to an **Azure** subscription (pay-as-you-go).
2. In the portal, create a **Trusted Signing account** (search "Trusted Signing").
3. Complete **Identity Validation** (individual or organization). This is the
   gate — Microsoft verifies who you are; allow a few days.
4. Create a **Certificate Profile** under the account (this is your publisher
   identity that appears instead of "Unknown publisher").
5. Create an **App registration** (service principal) and grant it the
   **"Trusted Signing Certificate Profile Signer"** role on the account.
6. In GitHub → **Settings → Secrets and variables → Actions**, add:
   - **Variables:** `ENABLE_SIGNING=true`, `TRUSTED_SIGNING_ENDPOINT`
     (e.g. `https://eus.codesigning.azure.net`), `TRUSTED_SIGNING_ACCOUNT`,
     `TRUSTED_SIGNING_PROFILE`
   - **Secrets:** `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`
     (from the app registration)
7. Push a version tag (e.g. `v0.6.3`). CI builds, signs with Trusted Signing,
   and publishes a Release whose installer shows **your** publisher name with no
   SmartScreen warning for anyone.

Nothing else changes — the self-signed setup above stays as the free fallback
for local builds; Trusted Signing only kicks in when those values are present.
