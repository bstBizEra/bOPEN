param(
  [Parameter(Mandatory = $true)][string]$Target,
  [Parameter(Mandatory = $true)][string]$EvidenceRoot,
  [Parameter(Mandatory = $true)][string]$OperatorId,
  [string]$NpmVersion = "10.9.2"
)
$ErrorActionPreference = "Stop"
$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..\..")).Path
$ApprovedRoot = [IO.Path]::GetFullPath("C:\laragon\www\bopen-research")
$Target = [IO.Path]::GetFullPath($Target)
$EvidenceRoot = [IO.Path]::GetFullPath($EvidenceRoot)
& python (Join-Path $RepositoryRoot "tools\validate_research_r0.py") paths `
  --target $Target --evidence-root $EvidenceRoot --approved-root $ApprovedRoot
if ($LASTEXITCODE -ne 0) { throw "Research workspace boundary validation failed" }
New-Item -ItemType Directory -Force $EvidenceRoot | Out-Null
& (Join-Path $PSScriptRoot "verify-upstream-pin.ps1") -Target $Target
if ($LASTEXITCODE -ne 0) { throw "Pinned source verification failed" }
$CloneMetadata = Join-Path $EvidenceRoot "clone-metadata.json"
if (-not (Test-Path $CloneMetadata)) { throw "Clone metadata is required in EvidenceRoot" }
& python (Join-Path $RepositoryRoot "tools\validate_research_r0.py") metadata --record $CloneMetadata
if ($LASTEXITCODE -ne 0) { throw "Clone metadata validation failed" }

$ClearedCredentialVariables = @(
  Get-ChildItem Env: | Where-Object Name -Match "(?i)(npm.*token|node_auth_token)" | Select-Object -ExpandProperty Name
)
foreach ($Name in $ClearedCredentialVariables) { Remove-Item "Env:$Name" -ErrorAction SilentlyContinue }
$NpmConfig = Join-Path $EvidenceRoot "npmrc"
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllText(
  $NpmConfig,
  "registry=https://registry.npmjs.org/`nalways-auth=false`naudit=false`nfund=false`n",
  $Utf8NoBom
)
$env:NPM_CONFIG_USERCONFIG = $NpmConfig
$env:NPM_CONFIG_REGISTRY = "https://registry.npmjs.org/"
$env:NPM_CONFIG_ALWAYS_AUTH = "false"

$ResolvedHosts = @(
  & python (Join-Path $RepositoryRoot "tools\validate_research_r0.py") lock-hosts `
    --lock (Join-Path $Target "package-lock.json")
)
if ($LASTEXITCODE -ne 0 -or $ResolvedHosts.Count -ne 1 -or $ResolvedHosts[0] -ne "registry.npmjs.org") {
  throw "Lockfile contains a non-allowlisted dependency host"
}
[ordered]@{
  schema_version = "1.0"
  registry_allowlist = @("registry.npmjs.org")
  lock_resolved_hosts = $ResolvedHosts
  credential_variable_names_cleared = $ClearedCredentialVariables
  credential_values_recorded = $false
  npm_user_config = "isolated"
} | ConvertTo-Json -Depth 4 | ForEach-Object {
  [IO.File]::WriteAllText((Join-Path $EvidenceRoot "network-credential-receipt.json"), "$_`n", $Utf8NoBom)
}

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
  $EnvironmentJson = $Environment | ConvertTo-Json
  [IO.File]::WriteAllText(
    (Join-Path $EvidenceRoot "environment-manifest.json"), "$EnvironmentJson`n", $Utf8NoBom
  )

  $Results = @()
  $Results += Invoke-Recorded "npm-ci" "npx.cmd" @("--yes", "npm@$NpmVersion", "ci", "--ignore-scripts", "--no-audit") 0
  $Results += Invoke-Recorded "prisma-generate" "node.exe" @("node_modules/prisma/build/index.js", "generate") 0
  $Results += Invoke-Recorded "check-format" "npx.cmd" @("--yes", "npm@$NpmVersion", "run", "check-format") 1
  $Results += Invoke-Recorded "check-lint" "npx.cmd" @("--yes", "npm@$NpmVersion", "run", "check-lint") 0
  $Results += Invoke-Recorded "check-types" "npx.cmd" @("--yes", "npm@$NpmVersion", "run", "check-types") 0
  $Results += Invoke-Recorded "unit-tests" "npx.cmd" @("--yes", "npm@$NpmVersion", "test", "--", "--runInBand") 0
  $Results += Invoke-Recorded "build-ci" "npx.cmd" @("--yes", "npm@$NpmVersion", "run", "build-ci") 0

  $Dirty = & git status --porcelain
  if ($LASTEXITCODE -ne 0 -or $Dirty) { throw "Baseline modified the pinned source tree" }
  $ResultJson = [ordered]@{
    schema_version = "1.0"
    operator_id = $OperatorId
    outcome = "reproduced_with_known_format_failure"
    results = $Results
  } | ConvertTo-Json -Depth 5
  [IO.File]::WriteAllText(
    (Join-Path $EvidenceRoot "baseline-result.json"), "$ResultJson`n", $Utf8NoBom
  )
  Write-Host "PASS: baseline matched declared outcomes"
} finally {
  Pop-Location
}
