import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.security.pii import mask_pii

FEEDBACK_PATH = Path("data/feedback.jsonl")


def append_feedback(
    *,
    user_id: str,
    conversation_id: str,
    rating: str,
    comment: str = "",
    trace_id: str | None = None,
    run_id: str | None = None,
    message_preview: str = "",
) -> dict[str, Any]:
    FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "feedback_id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "conversation_id": conversation_id,
        "rating": rating,
        "comment": mask_pii(comment),
        "trace_id": trace_id,
        "run_id": run_id,
        "message_preview": mask_pii(message_preview[:240]),
    }
    with FEEDBACK_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def list_feedback(*, limit: int = 20) -> list[dict[str, Any]]:
    if not FEEDBACK_PATH.exists():
        return []
    lines = [
        line for line in FEEDBACK_PATH.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    items = [json.loads(line) for line in lines[-limit:]]
    return list(reversed(items))
