Aşama 0

Ortamı Aktifleştir

cd c:\Users\cnytC\Desktop\code_projects\agentic_ai_prep
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

# Sadece Aşama 13 (Frontend + AI UX + Feedback)
pytest tests/test_feedback.py -v
uvicorn src.api.main:app --reload
# UI: http://127.0.0.1:8000/ui/
# Feedback: POST http://127.0.0.1:8000/v1/feedback

# Sadece Aşama 14 (System Design Case Study)
pytest tests/test_case_study_integration.py -v
python -m src.case_study.run_demo
# Doküman: docs/system_design_case_study.md

# Sadece Aşama 15-16 (Leadership + Mülakat Hub)
pytest tests/test_learning_hub.py -v
uvicorn src.api.main:app --reload
# UI: http://127.0.0.1:8000/ui/  → sol menüden tüm aşamalar + Q&A
# API: GET http://127.0.0.1:8000/v1/learning-hub
