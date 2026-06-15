from pathlib import Path


def test_deployment_artifacts_exist():
    root = Path(__file__).resolve().parents[1]
    required = [
        "Dockerfile",
        "docker-compose.deploy.yml",
        "requirements.txt",
        "infra/terraform/main.tf",
        "infra/terraform/ecs.tf",
        "infra/terraform/rds.tf",
        ".github/workflows/ci.yml",
        ".github/workflows/deploy.yml",
        "scripts/local-test.ps1",
        "scripts/deploy-compose.ps1",
        "scripts/deploy-aws.ps1",
    ]
    missing = [path for path in required if not (root / path).exists()]
    assert not missing, f"Missing deployment artifacts: {missing}"


def test_dockerfile_contains_healthcheck_and_uvicorn():
    dockerfile = (Path(__file__).resolve().parents[1] / "Dockerfile").read_text(encoding="utf-8")
    assert "HEALTHCHECK" in dockerfile
    assert "src.api.main:app" in dockerfile


def test_compose_deploy_has_api_and_postgres():
    compose = (Path(__file__).resolve().parents[1] / "docker-compose.deploy.yml").read_text(encoding="utf-8")
    assert "services:" in compose
    assert "api:" in compose
    assert "postgres:" in compose
    assert "/health" in compose
