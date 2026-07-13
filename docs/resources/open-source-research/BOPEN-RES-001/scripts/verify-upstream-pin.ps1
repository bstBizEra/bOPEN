param([Parameter(Mandatory = $true)][string]$Target)
$ErrorActionPreference = "Stop"
$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..\..")).Path
$Pin = Get-Content (Join-Path $RepositoryRoot "research\sources\boxyhq-upstream-pin.json") -Raw | ConvertFrom-Json

$Actual = (& git -C $Target rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $Actual -ne $Pin.commit) {
  throw "Expected $($Pin.commit), got $Actual"
}
$Origin = (& git -C $Target remote get-url origin).Trim()
if ($LASTEXITCODE -ne 0 -or $Origin -ne $Pin.repository_url) { throw "Origin mismatch: $Origin" }
& git -C $Target symbolic-ref -q HEAD *> $null
if ($LASTEXITCODE -eq 0) { throw "Checkout must be detached" }
$Dirty = & git -C $Target status --porcelain
if ($LASTEXITCODE -ne 0 -or $Dirty) { throw "Working tree is modified" }

$LicenseHash = (Get-FileHash (Join-Path $Target "LICENSE") -Algorithm SHA256).Hash.ToLower()
if ($LicenseHash -ne $Pin.license_sha256) { throw "License checksum mismatch" }
$LockPath = Join-Path $Target $Pin.lockfile
if (-not (Test-Path $LockPath)) { throw "Required lockfile missing: $($Pin.lockfile)" }
$LockHash = (Get-FileHash $LockPath -Algorithm SHA256).Hash.ToLower()
if ($LockHash -ne $Pin.lock_sha256) { throw "Lockfile checksum mismatch" }
Write-Host "PASS: origin, detached pin, clean tree, license, and lockfile verified"
