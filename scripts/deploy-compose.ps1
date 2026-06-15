param(
    [string]$AppVersion = "0.1.0"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot/..

if (-not (Test-Path ".env")) {
    throw ".env bulunamadi. Tum ortam degiskenlerini .env dosyasinda tanimlayin."
}

(Get-Content .env) -replace '^APP_VERSION=.*', "APP_VERSION=$AppVersion" -replace '^APP_ENV=.*', "APP_ENV=staging" | Set-Content .env

Write-Host "Running local test gate before compose deploy..."
.\scripts\local-test.ps1

docker compose -f docker-compose.deploy.yml up --build -d

for ($i = 1; $i -le 20; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing
        if ($resp.StatusCode -eq 200) {
            Write-Host "Deploy healthy: http://127.0.0.1:8000/health"
            exit 0
        }
    } catch {
        Start-Sleep -Seconds 3
    }
}

docker compose -f docker-compose.deploy.yml logs api
throw "Compose deploy healthcheck failed"
