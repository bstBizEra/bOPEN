param(
  [string]$WorkspaceRoot = "C:\laragon\www\bopen-research"
)
$ErrorActionPreference = "Stop"
$env:GIT_TERMINAL_PROMPT = "0"
$env:GCM_INTERACTIVE = "never"
$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..\..")).Path
$PinContract = Get-Content (Join-Path $RepositoryRoot "research\sources\boxyhq-upstream-pin.json") -Raw | ConvertFrom-Json
$RepoUrl = $PinContract.repository_url
$Pin = $PinContract.commit
$Target = Join-Path $WorkspaceRoot "01-boxyhq\upstream"
$Meta = Join-Path $WorkspaceRoot "01-boxyhq\clone-metadata.txt"

if (Test-Path $Target) { throw "Target already exists: $Target" }

# Physical upstream clones must remain outside the bOPEN worktree.
# credential.helper= is intentionally empty for the untrusted upstream fetch.
$RepositoryUrl = $PinContract.repository_url
$LicenseSha256 = $PinContract.license_sha256
$LockSha256 = $PinContract.lock_sha256
New-Item -ItemType Directory -Force -Path (Split-Path $Target) | Out-Null
git -c credential.helper= clone --no-checkout $RepoUrl $Target
Push-Location $Target
try {
  git fetch --depth 1 origin $Pin
  git checkout --detach $Pin
  $Actual = (git rev-parse HEAD).Trim()
  if ($Actual -ne $Pin) { throw "Pin mismatch: $Actual" }
  $LicenseHash = (Get-FileHash LICENSE -Algorithm SHA256).Hash.ToLower()
  $LockHash = if (Test-Path package-lock.json) { (Get-FileHash package-lock.json -Algorithm SHA256).Hash.ToLower() } else { "not-present" }
  @(
    "repository=$RepoUrl",
    "pinned_commit=$Pin",
    "actual_commit=$Actual",
    "cloned_at_utc=$([DateTime]::UtcNow.ToString('s'))Z",
    "license_sha256=$LicenseHash",
    "lock_sha256=$LockHash"
  ) | Set-Content -Encoding UTF8 $Meta
} finally { Pop-Location }
Write-Host "Pinned study clone created at $Target"
Write-Host "Metadata written to $Meta"
