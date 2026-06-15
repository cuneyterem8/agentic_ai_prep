param(
    [switch]$VerboseTests
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot/..

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

if ($VerboseTests) {
    pytest -v
} else {
    pytest -q
}

python -m src.evals.run_evals
Write-Host "Local test gate passed."
