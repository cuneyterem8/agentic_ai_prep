"""Genişletilmiş mülakat Q&A — stages 0-14."""

from src.learning_hub.interview_qa_00_07 import STAGE_INTERVIEW_QA as _QA_00_07
from src.learning_hub.interview_qa_08_14 import STAGE_INTERVIEW_QA_08_14

STAGE_INTERVIEW_QA: dict[int, list[dict]] = {
    **_QA_00_07,
    **STAGE_INTERVIEW_QA_08_14,
}
