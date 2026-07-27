param([Parameter(Mandatory=$true)][string]$Target)
$ErrorActionPreference = "Stop"
$Expected = "abc9b686823cbfb4973c79bc36fea37a3244be6c"
Push-Location $Target
try {
  $Actual = (git rev-parse HEAD).Trim()
  if ($Actual -ne $Expected) { throw "Expected $Expected, got $Actual" }
  $Dirty = git status --porcelain
  if ($Dirty) { throw "Working tree is modified" }
  Write-Host "PASS: upstream pin and clean tree verified"
} finally { Pop-Location }
