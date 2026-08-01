$ErrorActionPreference = "Stop"

Get-Content (Join-Path $PSScriptRoot "..\..\.env.local") | ForEach-Object {
    if ($_ -match '^\s*([^#=\s]+)\s*=\s*(.*)\s*$') {
        $name = $matches[1]
        $value = $matches[2].Trim()
        if (($value.StartsWith('"') -and $value.EndsWith('"')) -or
            ($value.StartsWith("'") -and $value.EndsWith("'"))) {
            $value = $value.Substring(1, $value.Length - 2)
        }
        Set-Item -Path "Env:$name" -Value $value
    }
}

& "C:\Users\ounkh\AppData\Local\Programs\Python\Python313\python.exe" `
    (Join-Path $PSScriptRoot "probe_wp_p35_05a_r5_codex.py")
exit $LASTEXITCODE
