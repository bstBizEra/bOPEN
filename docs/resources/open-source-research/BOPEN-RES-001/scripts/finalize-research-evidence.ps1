param(
  [Parameter(Mandatory = $true)][string]$EvidenceRoot,
  [Parameter(Mandatory = $true)][string]$OperatorId,
  [switch]$Verify
)
$ErrorActionPreference = "Stop"
$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..\..")).Path
$Python = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
if (-not $Python) { $Python = "C:\laragon\bin\python\python-3.13\python.exe" }
$ApprovedRoot = [IO.Path]::GetFullPath("C:\laragon\www\bopen-research")
$EvidenceRoot = [IO.Path]::GetFullPath($EvidenceRoot)
& $Python (Join-Path $RepositoryRoot "tools\validate_research_r0.py") paths `
  --target (Join-Path $EvidenceRoot "..\01-boxyhq\upstream") `
  --evidence-root $EvidenceRoot --approved-root $ApprovedRoot
if ($LASTEXITCODE -ne 0) { throw "Evidence path validation failed" }
$ManifestPath = Join-Path $EvidenceRoot "evidence-manifest.json"

function Get-EvidenceRecords {
  $RootPrefix = $EvidenceRoot.TrimEnd("\", "/")
  @(
    Get-ChildItem $EvidenceRoot -File -Recurse |
      Where-Object FullName -ne $ManifestPath |
      ForEach-Object {
        $RelativeName = $_.FullName.Substring($RootPrefix.Length).TrimStart("\", "/").Replace("\", "/")
        [ordered]@{
          name = $RelativeName
          bytes = $_.Length
          sha256 = (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower()
        }
      } |
      Sort-Object name
  )
}

if (-not $Verify) {
  $SecretReceipt = Join-Path $EvidenceRoot "secret-scan-receipt.json"
  & $Python (Join-Path $RepositoryRoot "tools\check_secrets.py") `
    --root $EvidenceRoot --receipt $SecretReceipt
  if ($LASTEXITCODE -ne 0) { throw "Evidence secret scan failed" }
  $Records = Get-EvidenceRecords
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
  Get-EvidenceRecords |
    ForEach-Object name |
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
