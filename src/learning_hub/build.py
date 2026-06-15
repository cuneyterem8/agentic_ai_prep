from src.learning_hub.enrich import enrich_stage_list
from src.learning_hub.interview_qa_stage15 import STAGE15_INTERVIEW_QA
from src.learning_hub.models import HubContent
from src.learning_hub.stage15 import STAGE15_CONTENT
from src.learning_hub.stage16 import STAGE16_CONTENT
from src.learning_hub.stages_00_07 import STAGES_00_07
from src.learning_hub.stages_08_14 import STAGES_08_14


def build_hub_content() -> HubContent:
    stages = enrich_stage_list(STAGES_00_07 + STAGES_08_14)
    stage15 = {**STAGE15_CONTENT, "interview_qa": STAGE15_INTERVIEW_QA}
    return {
        "version": "1.0.0",
        "stages": stages,
        "stage15": stage15,
        "stage16": STAGE16_CONTENT,
        "overview": {
            "title": "Agentic AI Prep — Mülakat Hazırlık Merkezi",
            "description": (
                "Aşama 0-16 kapsamlı rehber: her modülün sınıf açıklamaları, "
                "canlı API testleri, mülakat soru-cevapları ve leadership hikayeleri."
            ),
            "total_stages": 17,
            "total_interview_questions": STAGE16_CONTENT["total_questions"],
            "key_principle": (
                "Önce deterministic, test edilebilir ve gözlemlenebilir omurga; "
                "LLM bu omurganın içinde kontrollü karar bileşeni."
            ),
            "quick_start": [
                "pytest -q",
                "uvicorn src.api.main:app --reload",
                "http://127.0.0.1:8000/ui/",
            ],
            "stage_index": [
                {"id": s["id"], "title": s["title"]} for s in stages
            ]
            + [
                {"id": 15, "title": STAGE15_CONTENT["title"]},
                {"id": 16, "title": STAGE16_CONTENT["title"]},
            ],
        },
    }
