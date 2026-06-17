import pytest

from src.evals.judge import (
    aggregate_metrics,
    judge_answer,
    load_judge_golden_dataset,
    pairwise_eval,
    pointwise_eval,
    run_judge_eval,
)


@pytest.mark.asyncio
async def test_judge_low_groundedness_for_unsupported_claim():
    rubric = await judge_answer(
        question="EFT hafta sonu yapılabilir mi?",
        context="EFT işlemleri hafta içi mesai saatlerinde gerçekleşir.",
        answer="EFT işlemleri hafta sonu da yapılabilir.",
    )
    assert rubric.groundedness <= 2


@pytest.mark.asyncio
async def test_judge_high_groundedness_for_supported_claim():
    rubric = await judge_answer(
        question="FAST ne zaman?",
        context="FAST işlemleri 7/24 yapılabilir.",
        answer="FAST işlemleri 7/24 yapılabilir.",
    )
    assert rubric.groundedness >= 4


def test_aggregate_metrics():
    from src.evals.judge import JudgeRubric

    results = [
        JudgeRubric(groundedness=5, correctness=5, completeness=4, safety=5, reason="ok"),
        JudgeRubric(groundedness=3, correctness=4, completeness=3, safety=5, reason="ok"),
    ]
    agg = aggregate_metrics(results)
    assert agg["groundedness"] == 4.0
    assert agg["safety"] == 5.0


@pytest.mark.asyncio
async def test_pairwise_prefers_grounded_answer():
    context = "FAST işlemleri 7/24 yapılabilir."
    result = await pairwise_eval(
        question="FAST saatleri?",
        context=context,
        answer_a="FAST 7/24 yapılabilir.",
        answer_b="FAST sadece mesai saatlerinde yapılır.",
    )
    assert result.winner == "A"


@pytest.mark.asyncio
async def test_judge_golden_eval():
    report = await run_judge_eval()
    assert report["total"] == len(load_judge_golden_dataset())
    assert "aggregate_metrics" in report
