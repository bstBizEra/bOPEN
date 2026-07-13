param(
  [Parameter(Mandatory = $true)][string]$EvidenceRoot,
  [Parameter(Mandatory = $true)][string]$OperatorId,
  [switch]$Verify
)
$ErrorActionPreference = "Stop"
$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..\..")).Path
$ApprovedRoot = [IO.Path]::GetFullPath("C:\laragon\www\bopen-research")
$EvidenceRoot = [IO.Path]::GetFullPath($EvidenceRoot)
& python (Join-Path $RepositoryRoot "tools\validate_research_r0.py") paths `
  --target (Join-Path $EvidenceRoot "..\01-boxyhq\upstream") `
  --evidence-root $EvidenceRoot --approved-root $ApprovedRoot
if ($LASTEXITCODE -ne 0) { throw "Evidence path validation failed" }
$ManifestPath = Join-Path $EvidenceRoot "evidence-manifest.json"

if (-not $Verify) {
  $SecretReceipt = Join-Path $EvidenceRoot "secret-scan-receipt.json"
  & python (Join-Path $RepositoryRoot "tools\check_secrets.py") `
    --root $EvidenceRoot --receipt $SecretReceipt
  if ($LASTEXITCODE -ne 0) { throw "Evidence secret scan failed" }
  $Records = @(
    Get-ChildItem $EvidenceRoot -File |
      Where-Object Name -ne "evidence-manifest.json" |
      Sort-Object Name |
      ForEach-Object {
        [ordered]@{
          name = $_.Name
          bytes = $_.Length
          sha256 = (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower()
        }
      }
  )
  $Json = [ordered]@{
    schema_version = "1.0"
    operator_id = $OperatorId
    files = $Records
  } | ConvertTo-Json -Depth 5
  $Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [IO.File]::WriteAllText($ManifestPath, "$Json`n", $Utf8NoBom)
}

if (-not (Test-Path $ManifestPath)) { throw "Evidence manifest missing" }
$Manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json
if ($Manifest.operator_id -ne $OperatorId) { throw "Evidence operator mismatch" }
$ExpectedNames = @($Manifest.files | ForEach-Object name | Sort-Object)
$ActualNames = @(
  Get-ChildItem $EvidenceRoot -File |
    Where-Object Name -ne "evidence-manifest.json" |
    ForEach-Object Name |
    Sort-Object
)
if ((Compare-Object $ExpectedNames $ActualNames).Count -ne 0) { throw "Evidence file set mismatch" }
foreach ($Record in $Manifest.files) {
  $Path = Join-Path $EvidenceRoot $Record.name
  $Item = Get-Item $Path
  $Hash = (Get-FileHash $Path -Algorithm SHA256).Hash.ToLower()
  if ($Item.Length -ne $Record.bytes -or $Hash -ne $Record.sha256) {
    throw "Evidence integrity mismatch: $($Record.name)"
  }
}
Write-Host "PASS: evidence manifest and secret-scan receipt verified"
