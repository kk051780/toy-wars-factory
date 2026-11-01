# TOY WARS A14 Studio edit-mode local file probe. Manual on a trusted Windows host.
# IMPORTANT: This does NOT prove Play, client, two-client or mobile.
[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$StudioExe,
  [Parameter(Mandatory=$true)][string]$PlaceFile,
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [Parameter(Mandatory=$true)][string]$ProbeRoot
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$studioPath = [IO.Path]::GetFullPath($StudioExe)
$placePath  = [IO.Path]::GetFullPath($PlaceFile)
$root = [IO.Path]::GetFullPath($ProbeRoot)
if ([IO.Path]::GetFileName($studioPath) -ne 'RobloxStudioBeta.exe') { throw 'Not RobloxStudioBeta.exe' }
if (-not (Test-Path -LiteralPath $studioPath -PathType Leaf)) { throw 'Studio executable not found' }
if (-not (Test-Path -LiteralPath $placePath -PathType Leaf)) { throw 'Source-pinned local place not found' }
if (-not (Test-Path -LiteralPath $PythonExe -PathType Leaf)) { throw 'Explicit trusted Python executable not found' }
# The caller-supplied path and signature are checked before any untrusted file is loaded.
$signature = Get-AuthenticodeSignature -LiteralPath $studioPath
if ($signature.Status -ne 'Valid' -or $null -eq $signature.SignerCertificate -or
    $signature.SignerCertificate.Subject -notmatch '(^|,\s*)O=Roblox Corporation(\s*,|$)') { throw 'Roblox Studio Authenticode verification failed' }
$gate=Join-Path $root 'tools\studio_host_gate.py'
$probe=Join-Path $root 'tools\twf_local_place_probe.luau'
if (-not (Test-Path -LiteralPath $gate -PathType Leaf) -or -not (Test-Path -LiteralPath $probe -PathType Leaf)) {
    throw 'Reviewed Studio gate or Luau script missing'
}
& $PythonExe $gate --run --studio $studioPath --place $placePath --script $probe
if ($LASTEXITCODE -ne 0) { throw 'Studio validation did not pass' }
