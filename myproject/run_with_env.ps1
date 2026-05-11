param(
    [string]$Command = "python manage.py runserver"
)

$ErrorActionPreference = "Stop"
$envFile = Join-Path $PSScriptRoot "..\.env"
$venvPython = Join-Path $PSScriptRoot "..\venv\Scripts\python.exe"

if (-not (Test-Path $envFile)) {
    Write-Error ".env not found at $envFile"
}

Get-Content $envFile | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith("#")) {
        return
    }

    $parts = $line -split "=", 2
    if ($parts.Count -ne 2) {
        return
    }

    $name = $parts[0].Trim()
    $value = $parts[1].Trim()
    [System.Environment]::SetEnvironmentVariable($name, $value, "Process")
}

Write-Host "Loaded environment from .env and running: $Command" -ForegroundColor Green

if (Test-Path $venvPython) {
    if ($Command -match '^(python|python\.exe)\s+(.*)$') {
        $Command = $venvPython
        $Arguments = $matches[2] -split ' '
    }
}

if ($Arguments) {
    & $Command @Arguments
} else {
    Invoke-Expression $Command
}
