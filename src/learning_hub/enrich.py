"""Learning hub stage içeriklerine symbols_detail ekler."""

from src.learning_hub.models import ClassInfo, StageContent
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


def enrich_stage_list(stages: list[StageContent]) -> list[StageContent]:
    return [{**stage, "classes": enrich_classes(stage.get("classes", []))} for stage in stages]
