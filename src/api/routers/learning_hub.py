from fastapi import APIRouter

from src.learning_hub.build import build_hub_content

router = APIRouter(prefix="/v1", tags=["learning-hub"])


@router.get("/learning-hub")
async def get_learning_hub() -> dict:
    return build_hub_content()


@router.get("/learning-hub/stages/{stage_id}")
async def get_stage(stage_id: int) -> dict:
    hub = build_hub_content()
    if stage_id == 15:
        return {"stage": hub["stage15"], "type": "leadership"}
    if stage_id == 16:
        return {"stage": hub["stage16"], "type": "simulation"}
    for stage in hub["stages"]:
        if stage["id"] == stage_id:
            return {"stage": stage, "type": "technical"}
    return {"error": "Stage not found", "stage_id": stage_id}
