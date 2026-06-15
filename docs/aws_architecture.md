# AWS Architecture — Agentic AI Prep

## Hedef

Local terminal geliştirmeyi bozmadan, aynı kod tabanını tek seferde AWS'e taşıyabilmek.

## Bileşenler

```text
Internet
  -> ALB (public subnets)
    -> ECS Fargate service (private subnets)
      -> FastAPI container (/health)
      -> CloudWatch Logs
      -> Secrets Manager (OPENAI_API_KEY)
    -> RDS PostgreSQL (private subnets, encrypted)
```

## Trade-off'lar

| Karar | Neden | Alternatif |
| --- | --- | --- |
| ECS Fargate | Operasyon yükü düşük, mülakat için anlatması kolay | EKS (daha esnek, daha kompleks) |
| RDS PostgreSQL | Kalıcı audit/tool logları, production uyumu | SQLite (sadece local) |
| ALB + HTTP | Demo/staging basitliği | HTTPS + ACM (production zorunlu) |
| Secrets Manager | API key rotation ve audit | .env dosyası (sadece local) |
| Mock LLM default | CI ve offline test | OpenAI provider (staging/prod) |

## Güvenlik katmanları

- ECS task private subnet, doğrudan internet erişimi yok
- RDS sadece ECS security group'tan erişilebilir
- PII mask + compliance audit (Aşama 11)
- Input guardrails + role matrix

## CI/CD

- `CI` workflow: her PR/push'ta `pytest` + docker build smoke
- `Deploy` workflow:
  - `compose`: staging sunucuda docker compose
  - `aws`: ECR push + `terraform apply`
- Version: git tag `vX.Y.Z` → `APP_VERSION`

## Maliyet kontrolü

- Staging: `db.t4g.micro`, `desired_count=1`
- CloudWatch log retention: 14 gün
- NAT Gateway maliyeti staging'de bilinçli trade-off (production'da gözden geçir)

## Incident / rollback

1. CloudWatch logs + `/v1/observability/traces/{trace_id}` ile root cause
2. Önceki image tag'e dön (`app_version` downgrade)
3. `terraform apply` ile ECS task definition güncelle
4. Gerekirse `desired_count=0` ile servisi durdur
