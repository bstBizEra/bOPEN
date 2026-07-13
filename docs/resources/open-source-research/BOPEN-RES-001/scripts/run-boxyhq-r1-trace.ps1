param(
  [Parameter(Mandatory = $true)][string]$Target,
  [Parameter(Mandatory = $true)][string]$EvidenceRoot,
  [Parameter(Mandatory = $true)][string]$OperatorId
)
$ErrorActionPreference = "Stop"
$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..\..")).Path
$ApprovedRoot = [IO.Path]::GetFullPath("C:\laragon\www\bopen-research")
$Target = [IO.Path]::GetFullPath($Target)
$EvidenceRoot = [IO.Path]::GetFullPath($EvidenceRoot)
$env:GIT_TERMINAL_PROMPT = "0"
$env:GCM_INTERACTIVE = "never"

& python (Join-Path $RepositoryRoot "tools\validate_research_r0.py") paths `
  --target $Target --evidence-root $EvidenceRoot --approved-root $ApprovedRoot
if ($LASTEXITCODE -ne 0) { throw "R1 path validation failed before evidence creation" }
New-Item -ItemType Directory -Force -Path $EvidenceRoot | Out-Null

& python (Join-Path $RepositoryRoot "tools\validate_research_r1.py") `
  --target $Target --evidence-root $EvidenceRoot --approved-root $ApprovedRoot `
  --operator-id $OperatorId `
  --receipt (Join-Path $EvidenceRoot "r1-trace-receipt.json") `
  --test-receipt (Join-Path $EvidenceRoot "test-declaration-receipt.json")
if ($LASTEXITCODE -ne 0) { throw "R1 source trace validation failed" }

& (Join-Path $PSScriptRoot "finalize-research-evidence.ps1") `
  -EvidenceRoot $EvidenceRoot -OperatorId $OperatorId
if ($LASTEXITCODE -ne 0) { throw "R1 evidence finalization failed" }
Write-Host "PASS: R1 static trace and tracked test declaration inventory complete; G3 remains open"
