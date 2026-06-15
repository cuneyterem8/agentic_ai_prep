# Production Readiness Checklist

Internal Banking Knowledge Assistant için production öncesi kontrol listesi.  
Her madde projedeki mevcut implementasyona referans verir.

## Security & Compliance

| # | Kontrol | Durum | Referans |
|---|---------|-------|----------|
| 1 | Input guardrails (injection, exfiltration) | ✅ | `src/security/input_guardrails.py` |
| 2 | Tool argument validation | ✅ | `validate_tool_arguments` |
| 3 | RBAC / role matrix | ✅ | `src/agents/policies.py` |
| 4 | Human approval high-risk actions | ✅ | `workflow._request_human_approval` |
| 5 | PII masking in logs/feedback | ✅ | `src/security/pii.py` |
| 6 | Audit trail (immutable events) | ✅ | `src/security/audit.py` |
| 7 | SQL guardrails (analyst path) | ✅ | `src/security/input_guardrails.py` |
| 8 | Secrets not in git | ✅ | `.env` gitignored, AWS Secrets Manager |
| 9 | HTTPS / TLS termination | ⏳ | ALB + ACM (production zorunlu) |
| 10 | Penetration / security review | ⏳ | Pre-prod gate |

## Reliability & Operations

| # | Kontrol | Durum | Referans |
|---|---------|-------|----------|
| 11 | Health endpoint | ✅ | `GET /health` |
| 12 | LLM timeout + retry | ✅ | `src/llm/service.py`, `fallback_client.py` |
| 13 | Idempotent tool execution | ✅ | `ToolExecutionService` |
| 14 | Workflow checkpoint / resume | ✅ | `_checkpoint_store` |
| 15 | Graceful error responses | ✅ | `exception_handlers.py` |
| 16 | Rate limiting | ⏳ | API gateway / ALB (production) |
| 17 | Circuit breaker (LLM provider) | ⏳ | Fallback model mevcut; full CB sonraki faz |

## Observability

| # | Kontrol | Durum | Referans |
|---|---------|-------|----------|
| 18 | Request correlation ID | ✅ | `correlation_id_middleware` |
| 19 | Per-step trace timeline | ✅ | `src/observability/traces.py` |
| 20 | LLM cost / token metrics | ✅ | `metrics.record_llm_call` |
| 21 | HTTP latency metrics | ✅ | `request_metrics_middleware` |
| 22 | Workflow status metrics | ✅ | `record_workflow_run` |
| 23 | Centralized logging (CloudWatch) | ⏳ | ECS deploy sonrası |
| 24 | Alerting (error rate, p95 latency) | ⏳ | CloudWatch alarms |
| 25 | Incident runbook | ✅ | `docs/aws_architecture.md` § Incident |

## Quality & Evaluation

| # | Kontrol | Durum | Referans |
|---|---------|-------|----------|
| 26 | Classification golden dataset | ✅ | `classification_golden_dataset.jsonl` |
| 27 | Automated eval runner | ✅ | `python -m src.evals.run_evals` |
| 28 | CI pytest gate | ✅ | `.github/workflows/ci.yml` |
| 29 | E2E case study scenarios | ✅ | `tests/test_case_study_integration.py` |
| 30 | User feedback → eval link | ✅ | `trace_id` in feedback |
| 31 | Deploy öncesi eval regression | ⏳ | CI'ya eval gate ekle (Faz 2) |
| 32 | Human review loop | ⏳ | Feedback → golden dataset manuel |

## Data & Infrastructure

| # | Kontrol | Durum | Referans |
|---|---------|-------|----------|
| 33 | Schema migrations plan | ⏳ | `src/data/schema.sql` |
| 34 | PostgreSQL + pgvector (staging) | ⏳ | `docker-compose.yml` |
| 35 | Backup / restore (RDS) | ⏳ | Terraform RDS |
| 36 | Document ingestion pipeline | ⏳ | Mock retriever → real pipeline |
| 37 | Multi-tenant isolation test | ✅ | `tenant_id` + SQL guardrails |

## Deployment & Release

| # | Kontrol | Durum | Referans |
|---|---------|-------|----------|
| 38 | Dockerfile + healthcheck | ✅ | `Dockerfile` |
| 39 | Docker Compose staging | ✅ | `docker-compose.deploy.yml` |
| 40 | Terraform IaC | ✅ | `infra/terraform/` |
| 41 | CI docker build smoke | ✅ | `ci.yml` |
| 42 | Versioned deploy (`APP_VERSION`) | ✅ | deploy workflow |
| 43 | Rollback procedure | ✅ | `docs/aws_architecture.md` |
| 44 | Blue/green or canary | ⏳ | ECS rolling update (MVP yeterli) |

## Go / No-Go özet

**MVP staging Go** (mevcut kod ile):
- Güvenlik omurgası (1–8) ✅
- Observability temel (18–22) ✅
- Eval + test (26–29) ✅
- Deploy artifacts (38–43) ✅

**Production Go** (ek gereksinimler):
- HTTPS (9), rate limit (16), CloudWatch alerting (23–24)
- Gerçek RAG ingestion (36), eval deploy gate (31)
- Security review (10), backup plan (35)

```text
Staging:  ✅ hazır (mock LLM + SQLite/Compose)
Production: ⏳ checklist'teki ⏳ maddeler tamamlanınca
```
