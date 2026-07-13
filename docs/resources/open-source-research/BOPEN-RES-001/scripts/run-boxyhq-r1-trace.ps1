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
New-Item -ItemType Directory -Force -Path $EvidenceRoot | Out-Null

$SensitiveNames = @(
  "DATABASE_URL", "NEXTAUTH_SECRET", "SMTP_PASSWORD", "SVIX_API_KEY",
  "GITHUB_CLIENT_SECRET", "GOOGLE_CLIENT_SECRET", "RETRACED_API_KEY",
  "RECAPTCHA_SECRET_KEY", "SENTRY_AUTH_TOKEN", "SLACK_WEBHOOK_URL",
  "STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET", "NODE_AUTH_TOKEN",
  "NPM_TOKEN", "NPM_CONFIG__AUTH", "NPM_CONFIG__AUTH_TOKEN"
)
foreach ($Name in $SensitiveNames) { Remove-Item "Env:$Name" -ErrorAction SilentlyContinue }
$env:GIT_TERMINAL_PROMPT = "0"
$env:GCM_INTERACTIVE = "never"

& python (Join-Path $RepositoryRoot "tools\validate_research_r1.py") `
  --target $Target --evidence-root $EvidenceRoot --approved-root $ApprovedRoot `
  --operator-id $OperatorId --receipt (Join-Path $EvidenceRoot "r1-trace-receipt.json")
if ($LASTEXITCODE -ne 0) { throw "R1 source trace validation failed" }

$Playwright = Join-Path $Target "node_modules\.bin\playwright.cmd"
if (-not (Test-Path $Playwright)) { throw "Pinned Playwright CLI missing" }
Push-Location $Target
try {
  $Lines = @(& $Playwright test --list 2>&1 | ForEach-Object { $_.ToString() })
  $ExitCode = $LASTEXITCODE
} finally {
  Pop-Location
}
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllLines((Join-Path $EvidenceRoot "playwright-test-list.log"), $Lines, $Utf8NoBom)
$Summary = $Lines | Where-Object { $_ -match '^Total: (\d+) tests in (\d+) files$' } | Select-Object -Last 1
if ($ExitCode -ne 0 -or -not $Summary) { throw "Playwright test inventory failed" }
$null = $Summary -match '^Total: (\d+) tests in (\d+) files$'
$PlaywrightReceipt = [ordered]@{
  schema_version = "1.0"
  operator_id = $OperatorId
  runner_sha256 = (Get-FileHash $PSCommandPath -Algorithm SHA256).Hash.ToLower()
  playwright_config_sha256 = (Get-FileHash (Join-Path $Target "playwright.config.ts") -Algorithm SHA256).Hash.ToLower()
  command = "node_modules/.bin/playwright.cmd test --list"
  exit_code = $ExitCode
  test_count = [int]$Matches[1]
  file_count = [int]$Matches[2]
  runtime_executed = $false
  g3_status = "OPEN"
  status = "PASS"
}
[IO.File]::WriteAllText(
  (Join-Path $EvidenceRoot "playwright-list-receipt.json"),
  (($PlaywrightReceipt | ConvertTo-Json -Depth 4) + "`n"),
  $Utf8NoBom
)

& (Join-Path $PSScriptRoot "finalize-research-evidence.ps1") `
  -EvidenceRoot $EvidenceRoot -OperatorId $OperatorId
if ($LASTEXITCODE -ne 0) { throw "R1 evidence finalization failed" }
Write-Host "PASS: R1 static trace and test inventory complete; G3 remains open"
