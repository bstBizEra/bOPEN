param(
  [Parameter(Mandatory = $true)][string]$Target,
  [Parameter(Mandatory = $true)][string]$EvidenceRoot,
  [Parameter(Mandatory = $true)][string]$OperatorId,
  [string]$NpmVersion = "10.9.2"
)
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force $EvidenceRoot | Out-Null

function Invoke-Recorded(
  [string]$Name,
  [string]$Executable,
  [string[]]$Arguments,
  [int]$ExpectedExit
) {
  $Log = Join-Path $EvidenceRoot "$Name.log"
  $Stdout = Join-Path $EvidenceRoot "$Name.stdout.log"
  $Stderr = Join-Path $EvidenceRoot "$Name.stderr.log"
  $Process = Start-Process -FilePath $Executable -ArgumentList $Arguments -WorkingDirectory $Target `
    -Wait -PassThru -NoNewWindow -RedirectStandardOutput $Stdout -RedirectStandardError $Stderr
  $Code = $Process.ExitCode
  @(
    "# stdout"
    (Get-Content $Stdout -ErrorAction SilentlyContinue)
    "# stderr"
    (Get-Content $Stderr -ErrorAction SilentlyContinue)
  ) | Set-Content -Encoding UTF8 $Log
  "exit_code=$Code" | Add-Content $Log
  if ($Code -ne $ExpectedExit) {
    throw "$Name returned $Code; expected $ExpectedExit"
  }
  [ordered]@{ name = $Name; expected_exit = $ExpectedExit; actual_exit = $Code; status = "matched" }
}

Push-Location $Target
try {
  $Environment = [ordered]@{
    schema_version = "1.0"
    operator_id = $OperatorId
    captured_at_utc = [DateTime]::UtcNow.ToString("o")
    node = (& node --version).Trim()
    npm_host = (& npm --version).Trim()
    npm_baseline = $NpmVersion
    git = (& git --version).Trim()
    commit = (& git rev-parse HEAD).Trim()
  }
  $Environment | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $EvidenceRoot "environment-manifest.json")

  $Results = @()
  $Results += Invoke-Recorded "npm-ci" "npx.cmd" @("--yes", "npm@$NpmVersion", "ci", "--ignore-scripts", "--no-audit") 0
  $Results += Invoke-Recorded "prisma-generate" "npx.cmd" @("prisma", "generate") 0
  $Results += Invoke-Recorded "check-format" "npm.cmd" @("run", "check-format") 1
  $Results += Invoke-Recorded "check-lint" "npm.cmd" @("run", "check-lint") 0
  $Results += Invoke-Recorded "check-types" "npm.cmd" @("run", "check-types") 0
  $Results += Invoke-Recorded "unit-tests" "npm.cmd" @("test", "--", "--runInBand") 0
  $Results += Invoke-Recorded "build-ci" "npm.cmd" @("run", "build-ci") 0

  $Dirty = & git status --porcelain
  if ($LASTEXITCODE -ne 0 -or $Dirty) { throw "Baseline modified the pinned source tree" }
  [ordered]@{
    schema_version = "1.0"
    operator_id = $OperatorId
    outcome = "reproduced_with_known_format_failure"
    results = $Results
  } | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $EvidenceRoot "baseline-result.json")
  Write-Host "PASS: baseline matched declared outcomes"
} finally {
  Pop-Location
}
