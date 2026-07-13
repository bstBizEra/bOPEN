param(
  [Parameter(Mandatory = $true)][string]$WorkspaceRoot,
  [Parameter(Mandatory = $true)][string]$OperatorId,
  [string]$EvidenceRoot
)
$ErrorActionPreference = "Stop"

function Invoke-Native([string]$File, [string[]]$Arguments) {
  & $File @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "$File failed with exit code $LASTEXITCODE"
  }
}

$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..\..")).Path
$PinContractPath = Join-Path $RepositoryRoot "research\sources\boxyhq-upstream-pin.json"
$PinContract = Get-Content $PinContractPath -Raw | ConvertFrom-Json
$ApprovedRoot = [IO.Path]::GetFullPath("C:\laragon\www\bopen-research")
$ResolvedWorkspace = [IO.Path]::GetFullPath($WorkspaceRoot)
if ($ResolvedWorkspace -ne $ApprovedRoot -and -not $ResolvedWorkspace.StartsWith("$ApprovedRoot\")) {
  throw "Workspace must be under $ApprovedRoot"
}
if ($ResolvedWorkspace.StartsWith("$RepositoryRoot\")) {
  throw "Physical upstream clones must remain outside the bOPEN worktree"
}
if ($OperatorId -notmatch "^[A-Za-z0-9._-]+$") {
  throw "OperatorId contains unsupported characters"
}

$Target = Join-Path $ResolvedWorkspace "01-boxyhq\upstream"
if (-not $EvidenceRoot) { $EvidenceRoot = Join-Path $ResolvedWorkspace "evidence" }
$ResolvedEvidence = [IO.Path]::GetFullPath($EvidenceRoot)
if ($ResolvedEvidence -ne $ApprovedRoot -and -not $ResolvedEvidence.StartsWith("$ApprovedRoot\")) {
  throw "EvidenceRoot must be under $ApprovedRoot"
}
if (Test-Path $Target) { throw "Target already exists: $Target" }

$env:GIT_TERMINAL_PROMPT = "0"
$env:GCM_INTERACTIVE = "never"
New-Item -ItemType Directory -Force -Path $Target, $ResolvedEvidence | Out-Null

Invoke-Native git @("-C", $Target, "init")
Invoke-Native git @("-C", $Target, "remote", "add", "origin", $PinContract.repository_url)
Invoke-Native git @("-C", $Target, "-c", "credential.helper=", "fetch", "--depth", "1", "origin", $PinContract.commit)
Invoke-Native git @("-C", $Target, "checkout", "--detach", "FETCH_HEAD")

$Actual = (& git -C $Target rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $Actual -ne $PinContract.commit) {
  throw "Pin mismatch: expected $($PinContract.commit), got $Actual"
}
$Origin = (& git -C $Target remote get-url origin).Trim()
if ($LASTEXITCODE -ne 0 -or $Origin -ne $PinContract.repository_url) {
  throw "Origin mismatch: $Origin"
}
$Dirty = & git -C $Target status --porcelain
if ($LASTEXITCODE -ne 0 -or $Dirty) { throw "Pinned checkout is not clean" }

$LicenseHash = (Get-FileHash (Join-Path $Target "LICENSE") -Algorithm SHA256).Hash.ToLower()
if ($LicenseHash -ne $PinContract.license_sha256) { throw "License checksum mismatch" }
$LockPath = Join-Path $Target $PinContract.lockfile
if (-not (Test-Path $LockPath)) { throw "Required lockfile missing: $($PinContract.lockfile)" }
$LockHash = (Get-FileHash $LockPath -Algorithm SHA256).Hash.ToLower()
if ($LockHash -ne $PinContract.lock_sha256) { throw "Lockfile checksum mismatch" }

$Metadata = [ordered]@{
  schema_version = "1.0"
  source_id = $PinContract.source_id
  repository = $PinContract.repository_url
  upstream_owner = "boxyhq"
  default_branch = $PinContract.default_branch
  pinned_commit = $PinContract.commit
  actual_commit = $Actual
  reference_release = $PinContract.reference_release
  archived_observed = [bool]$PinContract.archived_observed
  license = $PinContract.license_observed
  license_sha256 = $LicenseHash
  lockfile = $PinContract.lockfile
  lock_sha256 = $LockHash
  local_patches = @()
  operator_id = $OperatorId
  captured_at_utc = [DateTime]::UtcNow.ToString("o")
  workstation = [Environment]::MachineName
  os = [Environment]::OSVersion.VersionString
  powershell = $PSVersionTable.PSVersion.ToString()
  git = (& git --version).Trim()
  credential_prompting = "disabled"
  target = $Target
}
$MetadataPath = Join-Path $ResolvedEvidence "clone-metadata.json"
$Metadata | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 $MetadataPath
Write-Host "Pinned study clone created at $Target"
Write-Host "Metadata written to $MetadataPath"
