param(
  [string]$WorkspaceRoot = "C:\laragon\www\bopen-research"
)
$ErrorActionPreference = "Stop"
$RepoUrl = "https://github.com/boxyhq/saas-starter-kit.git"
$Pin = "abc9b686823cbfb4973c79bc36fea37a3244be6c"
$Target = Join-Path $WorkspaceRoot "01-boxyhq\upstream"
$Meta = Join-Path $WorkspaceRoot "01-boxyhq\clone-metadata.txt"

if (Test-Path $Target) { throw "Target already exists: $Target" }
New-Item -ItemType Directory -Force -Path (Split-Path $Target) | Out-Null
git clone --no-checkout $RepoUrl $Target
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
