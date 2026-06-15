$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot/..

if (-not (Test-Path ".venv")) {
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
} else {
    .\.venv\Scripts\Activate.ps1
}

if (-not (Test-Path ".env")) {
    throw ".env bulunamadi. Tum ortam degiskenlerini .env dosyasinda tanimlayin."
}

uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
