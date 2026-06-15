"""Stage 16 — Full interview simulation: aggregates all Q&A + simulation format."""

from src.learning_hub.interview_qa_expanded import STAGE_INTERVIEW_QA
from src.learning_hub.interview_qa_stage15 import STAGE15_INTERVIEW_QA
from src.learning_hub.stage15 import STAGE15_CONTENT
from src.learning_hub.stages_00_07 import STAGES_00_07
from src.learning_hub.stages_08_14 import STAGES_08_14


def _collect_all_qa() -> list[dict]:
    items: list[dict] = []
    for stage in STAGES_00_07 + STAGES_08_14:
        stage_id = stage["id"]
        qa_list = STAGE_INTERVIEW_QA.get(stage_id, stage.get("interview_qa", []))
        for qa in qa_list:
            items.append(
                {
                    "stage_id": stage_id,
                    "stage_title": stage["title"],
                    **qa,
                }
            )
    for qa in STAGE15_INTERVIEW_QA:
        items.append(
            {
                "stage_id": 15,
                "stage_title": STAGE15_CONTENT["title"],
                **qa,
            }
        )
    return items


STAGE16_CONTENT = {
    "title": "Final Mülakat Simülasyonu",
    "subtitle": "Tüm aşamaların soru-cevap bankası + prova formatı",
    "summary": (
        "Aşama 0-15'teki tüm mülakat soruları tek yerde. "
        "10 dakika intro, canlı kod, system design, behavioral — tam prova akışı."
    ),
    "simulation_schedule": [
        {"order": 1, "area": "Kendini tanıtma", "duration_min": 10, "difficulty": "Orta", "focus": "Role positioning, production mindset"},
        {"order": 2, "area": "Python + FastAPI canlı kod", "duration_min": 20, "difficulty": "Orta", "focus": "LLMClient interface, mock test, /v1/chat"},
        {"order": 3, "area": "Agent workflow canlı kod", "duration_min": 20, "difficulty": "Zor", "focus": "Workflow nodes, policy, approval checkpoint"},
        {"order": 4, "area": "RAG + evaluation", "duration_min": 20, "difficulty": "Zor", "focus": "Retrieval, citations, golden eval"},
        {"order": 5, "area": "PostgreSQL + schema", "duration_min": 15, "difficulty": "Orta-Zor", "focus": "Idempotency, audit, tenant isolation"},
        {"order": 6, "area": "AWS production architecture", "duration_min": 15, "difficulty": "Zor", "focus": "ECS, RDS, secrets, rollback"},
        {"order": 7, "area": "Observability + debugging", "duration_min": 15, "difficulty": "Zor", "focus": "Trace replay, RCA"},
        {"order": 8, "area": "Evaluation + guardrails", "duration_min": 15, "difficulty": "Zor", "focus": "Golden dataset, injection defense"},
        {"order": 9, "area": "Full system design", "duration_min": 30, "difficulty": "Expert", "focus": "Internal banking assistant E2E"},
        {"order": 10, "area": "Behavioral + leadership", "duration_min": 15, "difficulty": "Expert", "focus": "STAR stories, stakeholder management"},
        {"order": 11, "area": "Senin soruların", "duration_min": 10, "difficulty": "-", "focus": "Takım, roadmap, eval kültürü"},
    ],
    "opening_pitch": (
        "Ben Python ağırlıklı AI/LLM data scientist'im; agent sistemlerinde önce deterministic, "
        "test edilebilir omurga kurarım — config, guardrails, policy, audit, eval — LLM'i bu omurganın "
        "içinde kontrollü bileşen olarak konumlandırırım. Bankacılık bağlamında compliance, PII ve human approval "
        "olmazsa olmaz. Bu repoda 0-14 arası her aşamayı çalışan kod ve test ile gösterdim."
    ),
    "live_coding_prompts": [
        {
            "id": "lc-1",
            "prompt": "API anahtarı olmadan test edilebilir LLM endpoint tasarla.",
            "expected_approach": "LLMClient Protocol + MockLLMClient + FastAPI Depends + pytest",
            "project_reference": "src/llm/base.py, src/llm/mock_client.py, src/api/routers/chat.py",
        },
        {
            "id": "lc-2",
            "prompt": "Müşteri mesajını intent/risk/approval JSON'a sınıflandır.",
            "expected_approach": "Pydantic schema + parse + repair loop + guardrail",
            "project_reference": "src/agents/classifier.py, src/llm/structured_output.py",
        },
        {
            "id": "lc-3",
            "prompt": "Yüksek riskli transfer için human approval gate ekle.",
            "expected_approach": "Policy engine REQUIRE_APPROVAL + checkpoint resume",
            "project_reference": "src/agents/policies.py, src/agents/workflow.py",
        },
        {
            "id": "lc-4",
            "prompt": "DELETE içeren SQL'i engelle.",
            "expected_approach": "validate_sql guardrail + regeneration + canonical fallback",
            "project_reference": "src/security/guardrails.py, src/agents/data_analyst.py",
        },
    ],
    "system_design_prompt": {
        "question": "Kurum çalışanları için Internal Banking Knowledge Assistant + Actionable Support Agent tasarla.",
        "answer_skeleton": [
            "1. Problem: policy lookup hızı + guarded action",
            "2. Data: ingestion, metadata, access control",
            "3. Retrieval: hybrid, rerank, citations",
            "4. Agent: deterministic routing + policy",
            "5. Backend: FastAPI async, retry, rate limit",
            "6. Storage: PostgreSQL, pgvector, audit",
            "7. Security: PII, RBAC, approval",
            "8. Eval: golden set, regression CI",
            "9. Observability: trace, cost, latency",
            "10. Deploy: ECS, RDS, Secrets, CloudWatch",
            "11. Impact: resolution time, deflection, cost/interaction",
        ],
        "doc_reference": "docs/system_design_case_study.md",
    },
    "questions_to_ask_interviewer": [
        "Takımın agent sistemlerinde evaluation ve guardrail kültürü nasıl?",
        "Production'da human-in-the-loop onay süreçleri nasıl işliyor?",
        "LLM provider stratejisi: OpenAI, Azure, hybrid?",
        "İlk 6 ayda en kritik business use-case hangisi?",
        "Mülakat sonrası teknik deep-dive veya take-home var mı?",
    ],
    "success_criteria": [
        "Kod çalışıyor ve test edilebilir",
        "Hatalar kontrollü (structured errors)",
        "Security, observability, cost düşünülmüş",
        "Framework ezberi değil production engineering",
        "Business impact ölçülebilir",
    ],
    "all_interview_qa": _collect_all_qa(),
    "total_questions": 0,  # filled below
}

STAGE16_CONTENT["total_questions"] = len(STAGE16_CONTENT["all_interview_qa"])
