# Agentic AI Prep Mülakat Hazırlık Projesi

Expert AI/LLM Data Scientist in Agentic AI rolü için production mantığı olan, test edilebilir Python agent/LLM servisleri geliştirme projesi.

## Kurulum

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Tum ortam degiskenleri tek dosyada: `.env` (git'e eklenmez). Ornek alanlar:

```env
LLM_PROVIDER=mock
OPENAI_API_KEY=
DATABASE_URL=sqlite:///./data/app.db
APP_ENV=development
PROMPT_VERSION=v1
```

Gerçek OpenAI için:
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
OPENAI_FALLBACK_MODEL=gpt-4o-mini
```

## Çalıştırma (Local — birincil yol)

Günlük geliştirme ve test **terminalden**, Docker olmadan:

```powershell
.\scripts\local-test.ps1     # pytest + eval regression
.\scripts\local-run.ps1      # uvicorn --reload
```

veya klasik:

```powershell
pytest -q
uvicorn src.api.main:app --reload
```

Healthcheck: `GET http://127.0.0.1:8000/health`

Chat: `POST http://127.0.0.1:8000/v1/chat`

```json
{
  "user_id": "user-1",
  "conversation_id": "conv-1",
  "message": "Merhaba",
  "stream": false
}
```

Streaming: aynı body ile `"stream": true` → SSE response.

Agent: `POST http://127.0.0.1:8000/v1/agent/run`

Classify: `POST http://127.0.0.1:8000/v1/classify`

Classify eval: `GET http://127.0.0.1:8000/v1/classify/eval`

All evals: `GET http://127.0.0.1:8000/v1/evals/run`

CLI eval runner:
```powershell
python -m src.evals.run_evals
```

Workflow: `POST http://127.0.0.1:8000/v1/workflow/run`

```json
{
  "user_id": "user-1",
  "conversation_id": "conv-1",
  "message": "Hesabımdan 80000 TL transfer et"
}
```

Onay sonrası resume için aynı endpoint'e `run_id` ve `approval_granted: true` gönder.

RAG query: `POST http://127.0.0.1:8000/v1/rag/query`

```json
{
  "user_id": "user-1",
  "question": "transfer above 50000 TL approval",
  "top_k": 3
}
```

RAG eval: `GET http://127.0.0.1:8000/v1/rag/eval`

Data layer default: SQLite (`DATABASE_URL=sqlite:///./data/app.db`).

Optional PostgreSQL + pgvector:
```powershell
docker compose up -d
# DATABASE_URL=postgresql+psycopg2://agenticai:agenticai@localhost:5432/agenticai
```

Schema: `src/data/schema.sql`

Analyst: `POST http://127.0.0.1:8000/v1/analyst/query`

```json
{
  "user_id": "user-1",
  "tenant_id": "tenant-a",
  "question": "What is total amount by tenant"
}
```

Analyst eval: `GET http://127.0.0.1:8000/v1/analyst/eval`

Observability metrics: `GET http://127.0.0.1:8000/v1/observability/metrics`

Trace replay: `GET http://127.0.0.1:8000/v1/observability/traces/{trace_id}`

## Demo UI (Aşama 13)

```powershell
uvicorn src.api.main:app --reload
```

Tarayıcı: `http://127.0.0.1:8000/ui/` (root `/` otomatik yönlendirir)

- **Workflow modu:** agent adımları, onay modalı, trace paneli
- **Chat Stream modu:** SSE token streaming
- **Feedback:** 👍/👎 → `POST /v1/feedback` (`trace_id` ile eval pipeline'a bağlanır)

Detay: `docs/ai_ux_notes.md`

## System Design (Aşama 14)

Ana case: **Internal Banking Knowledge Assistant + Actionable Support Agent**

Uçtan uca akış tek endpoint'te: `POST /v1/workflow/run` (classify → RAG → policy → tool → audit → trace).

```powershell
# E2E senaryolar (knowledge, transfer+onay, injection block)
python -m src.case_study.run_demo

# Entegrasyon testleri
pytest tests/test_case_study_integration.py -v
```

Dokümanlar:
- `docs/system_design_case_study.md` — mimari, failure modes, MVP scope, business impact
- `docs/production_readiness_checklist.md` — go/no-go checklist

## Mülakat Hazırlık Merkezi (Aşama 15–16)

Tarayıcıda tam rehber: `http://127.0.0.1:8000/ui/`

Sol menüden:
- **Genel Bakış** — tüm aşamaların özeti
- **Aşama 0–14** — her biri için: özet, sınıf açıklamaları, canlı API testi, mülakat Q&A
- **Aşama 15** — STAR leadership hikayeleri + behavioral Q&A
- **Aşama 16** — 78+ mülakat sorusu, prova takvimi, canlı kod promptları
- **Agent Demo UI** — workflow + streaming + onay

```powershell
uvicorn src.api.main:app --reload
pytest tests/test_learning_hub.py -v
```

API: `GET /v1/learning-hub` (tüm içerik JSON)

İçerik kaynağı: `src/learning_hub/` modülleri

Feedback API:

```json
POST /v1/feedback
{
  "user_id": "user-1",
  "conversation_id": "conv-1",
  "rating": "positive",
  "trace_id": "optional-trace-id"
}
```

Workflow response artık `trace_id` ve `trace_summary` (classification/retrieval/LLM/tool latency timeline + cost estimate) döner.

Security audit: `GET http://127.0.0.1:8000/v1/security/audit/recent`

Workflow body opsiyonel alanlar: `tenant_id`, `user_role` (`customer`, `support_agent`, `admin`).

## Modül Sırası

| Aşama | Konu | Durum |
| --- | --- | --- |
| 0 | Config, logging, healthcheck | ✅ |
| 1 | LLM interface, mock client, retry | ✅ |
| 2 | FastAPI chat/agent endpoints | ✅ |
| 3 | LangChain / structured output | ✅ |
| 4 | LangGraph agent workflow | ✅ |
| 5 | OpenAI provider adapter | ✅ |
| 6 | RAG & retrieval | ✅ |
| 7 | PostgreSQL / data layer | ✅ |
| 8 | Agentic data analyst / SQL guardrails | ✅ |
| 9 | Observability, traces, metrics | ✅ |
| 10 | Evaluation, guardrails, golden dataset | ✅ |
| 11 | Security, compliance, banking policy | ✅ |
| 12 | Docker/Terraform deploy + GitHub CI/CD | ✅ |
| 13 | TypeScript client + AI UX demo UI | ✅ |
| 14 | Full system design case study | ✅ |
| 15 | Behavioral & technical leadership | ✅ |
| 16 | Final mülakat simülasyonu + Q&A hub | ✅ |

## Deploy (isteğe bağlı — test sonrası)

Local test geçtikten sonra:

```powershell
# Staging (Docker Compose) — once .env icinde APP_ENV=staging ayarla
.\scripts\deploy-compose.ps1

# AWS (Terraform + ECS) — credentials gerekir
copy infra\terraform\terraform.tfvars.example infra\terraform\terraform.tfvars
.\scripts\deploy-aws.ps1 -AppVersion 0.1.0 -Environment staging
```

Detay: `docs/deploy_workflow.md`, `docs/aws_architecture.md`

## Git / GitHub

```powershell
git init
git add .
git commit -m "Initial commit"
git branch -M main
gh auth login
gh repo create agentic_ai_prep --public --source=. --remote=origin --push
```

Tek kaynak dosyalar: `.env` (gitignore) ve `requirements.txt`.

## Mimari Prensip

> Önce deterministic, test edilebilir ve gözlemlenebilir omurga kurulur; LLM bu omurganın içinde kontrollü bir karar/veri üretim bileşeni olarak konumlandırılır.
