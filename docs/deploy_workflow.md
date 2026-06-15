# Local Development and Deploy Workflow

## Günlük geliştirme (Docker gerekmez)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# .env dosyasini duzenle (tek kaynak)
pytest -q
uvicorn src.api.main:app --reload
```

## Version control akışı

1. Feature branch aç → local `pytest`
2. PR aç → GitHub Actions `CI` çalışır
3. Merge sonrası deploy:
   - **Staging VM / test sunucu:** `deploy-compose.ps1` (`.env` kullanır)
   - **AWS:** tag `v1.2.3` push veya GitHub `Deploy` workflow (`target=aws`)

## Staging deploy (Docker Compose)

`.env` icinde deploy alanlarini ayarla (`POSTGRES_*`, `API_PORT`, `APP_ENV=staging`), sonra:

```powershell
.\scripts\deploy-compose.ps1
```

## AWS deploy (Terraform + ECS)

```powershell
copy infra\terraform\terraform.tfvars.example infra\terraform\terraform.tfvars
# terraform.tfvars icinde db_password ve gerekirse openai_api_key doldur
.\scripts\deploy-aws.ps1 -AppVersion 0.1.0 -Environment staging
```

Tek komutta image build + push + terraform apply için GitHub Actions `Deploy` workflow kullanılır.

## Ortam matrisi

| Ortam | Çalıştırma | DB | LLM |
| --- | --- | --- | --- |
| local | terminal `uvicorn` | SQLite | mock (default) |
| staging-compose | docker compose deploy | PostgreSQL container | mock/openai |
| aws | ECS Fargate + ALB | RDS PostgreSQL | Secrets Manager |

## Rollback

- Compose: önceki image tag ile `docker compose -f docker-compose.deploy.yml up -d`
- AWS: önceki `app_version` ile `terraform apply -var="app_version=..."`
