Aşama 0

Ortamı Aktifleştir

cd c:\Users\cnytC\Desktop\code_projects\agenticai_ing_prep
.\.venv\Scripts\Activate.ps1

Otomatik Testler (pytest) — Ana yöntem

pytest -v



uvicorn src.api.main:app --reload

http://127.0.0.1:8000/health



# Tüm testler
pytest -v

# Sadece Aşama 1
pytest tests/test_mock_llm.py tests/test_retry.py -v

# Sadece Aşama 9 (Observability)
pytest tests/test_observability.py -v

# Metrics: GET http://127.0.0.1:8000/v1/observability/metrics
# Trace:  GET http://127.0.0.1:8000/v1/observability/traces/{trace_id}

# Sadece Aşama 10 (Evaluation + Guardrails)
pytest tests/test_guardrails.py -v
python -m src.evals.run_evals

# Sadece Aşama 11 (Security + Compliance)
pytest tests/test_security_policy.py -v
# GET http://127.0.0.1:8000/v1/security/audit/recent

# Sadece Aşama 12 (Deploy artifacts + local workflow)
pytest tests/test_deploy_artifacts.py -v
.\scripts\local-test.ps1
# Staging deploy (opsiyonel): .\scripts\deploy-compose.ps1
# AWS deploy (opsiyonel): .\scripts\deploy-aws.ps1 -PlanOnly
