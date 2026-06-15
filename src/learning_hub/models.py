from typing import Any, TypedDict


class ClassInfo(TypedDict):
    path: str
    name: str
    purpose: str
    key_symbols: list[str]


class LabAction(TypedDict, total=False):
    id: str
    label: str
    description: str
    type: str  # api_get | api_post | prompt | command | navigate
    endpoint: str
    method: str
    body: dict[str, Any]
    prompt: str
    command: str
    navigate: str


class InterviewQA(TypedDict, total=False):
    question: str
    answer: str
    deep_dive: str
    red_flags: list[str]
    strong_signals: list[str]
    tags: list[str]


class StageContent(TypedDict, total=False):
    id: int
    title: str
    subtitle: str
    summary: str
    topics: list[str]
    classes: list[ClassInfo]
    lab_actions: list[LabAction]
    interview_qa: list[InterviewQA]
    commands: list[str]
    dod: list[str]
    failure_modes: list[str]
    doc_links: list[str]


class LeadershipStory(TypedDict, total=False):
    id: str
    title: str
    situation: str
    task: str
    action: str
    result: str
    technical_depth: str
    reflection: str


class SimulationRound(TypedDict, total=False):
    order: int
    area: str
    duration_min: int
    difficulty: str
    focus: str


class HubContent(TypedDict):
    version: str
    stages: list[StageContent]
    stage15: dict[str, Any]
    stage16: dict[str, Any]
    overview: dict[str, Any]
