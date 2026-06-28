<#
.SYNOPSIS
  Authenticode-sign a file with the local WisperLocal code-signing certificate.

.DESCRIPTION
  Finds a code-signing certificate whose subject contains "WisperLocal" in the
  current user's personal store (Cert:\CurrentUser\My) and signs the given file
  (SHA-256, RFC-3161 timestamp). If no such certificate exists, it warns and
  exits 0 so unsigned builds still succeed.

  This uses a SELF-SIGNED certificate: the signature is trusted only on machines
  that have imported WisperLocal-CodeSigning.cer into Trusted Root + Trusted
  Publishers. See docs/CODE_SIGNING.md. For public distribution use a real
  (Azure Trusted Signing / EV) certificate instead.

.EXAMPLE
  pwsh -File scripts\sign.ps1 ..\WisperLocal-Setup-0.6.2.exe
#>
param(
    [Parameter(Mandatory = $true)][string]$Path,
    [string]$TimestampServer = "http://timestamp.digicert.com"
)

if (-not (Test-Path $Path)) {
    Write-Error "File not found: $Path"
    exit 1
}

$cert = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert -ErrorAction SilentlyContinue |
    Where-Object { $_.Subject -like "*WisperLocal*" } |
    Sort-Object NotAfter -Descending | Select-Object -First 1

if (-not $cert) {
    Write-Warning "No WisperLocal code-signing certificate in Cert:\CurrentUser\My - skipping signing. (See docs/CODE_SIGNING.md to create one.)"
    exit 0
}

$sig = Set-AuthenticodeSignature -FilePath $Path -Certificate $cert `
    -HashAlgorithm SHA256 -TimestampServer $TimestampServer
Write-Host "Signed '$Path'"
Write-Host "  cert:   $($cert.Subject)  [$($cert.Thumbprint)]"
Write-Host "  status: $($sig.Status)  (UnknownError = signed but cert not yet trusted on this machine - expected)"
