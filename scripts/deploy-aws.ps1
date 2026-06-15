param(
    [string]$AppVersion = "0.1.0",
    [ValidateSet("staging", "production")]
    [string]$Environment = "staging",
    [switch]$PlanOnly
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot/..

$tfDir = Join-Path $PWD "infra/terraform"
if (-not (Test-Path (Join-Path $tfDir "terraform.tfvars"))) {
    Copy-Item (Join-Path $tfDir "terraform.tfvars.example") (Join-Path $tfDir "terraform.tfvars")
    Write-Host "Created terraform.tfvars from example. Set db_password before apply."
}

Write-Host "Running local test gate before AWS deploy..."
.\scripts\local-test.ps1

Push-Location $tfDir
try {
    terraform init -input=false
    $args = @(
        "-var=app_version=$AppVersion",
        "-var=environment=$Environment"
    )
    if ($PlanOnly) {
        terraform plan @args
    } else {
        terraform apply -auto-approve @args
        terraform output
    }
} finally {
    Pop-Location
}
