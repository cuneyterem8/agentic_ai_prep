"""Learning hub stage içeriklerine symbols_detail ekler."""

from src.learning_hub.interview_qa_expanded import STAGE_INTERVIEW_QA
from src.learning_hub.models import ClassInfo, ConceptGuide, InterviewQA, StageContent
from src.learning_hub.stage_concept_guides import STAGE_CONCEPT_GUIDES
from src.learning_hub.symbols_detail_registry import SYMBOLS_DETAIL_BY_PATH


def enrich_classes(classes: list[ClassInfo]) -> list[ClassInfo]:
    enriched: list[ClassInfo] = []
    for cls in classes:
        if cls.get("symbols_detail"):
            enriched.append(cls)
            continue
        details = SYMBOLS_DETAIL_BY_PATH.get(cls["path"])
        if details:
            enriched.append({**cls, "symbols_detail": details})
        else:
            enriched.append(cls)
    return enriched


def enrich_stage(stage: StageContent) -> StageContent:
    stage_id = stage.get("id")
    concept_guide: ConceptGuide | None = None
    interview_qa: list[InterviewQA] | None = None
    if stage_id is not None:
        concept_guide = STAGE_CONCEPT_GUIDES.get(stage_id)
        interview_qa = STAGE_INTERVIEW_QA.get(stage_id)
    enriched: StageContent = {**stage, "classes": enrich_classes(stage.get("classes", []))}
    if concept_guide:
        enriched["concept_guide"] = concept_guide
    if interview_qa:
        enriched["interview_qa"] = interview_qa
    return enriched


def enrich_stage_list(stages: list[StageContent]) -> list[StageContent]:
    return [enrich_stage(stage) for stage in stages]
