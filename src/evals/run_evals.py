import json
from pathlib import Path
from typing import Any

from src.agents.classifier import classify_customer_message
from src.agents.data_analyst import run_data_analyst
from src.llm.mock_client import MockLLMClient
from src.security.guardrails import validate_sql
from src.security.input_guardrails import GuardrailCategory, validate_user_input
from src.security.sql_correctness import validate_sql_correctness
from src.evals.judge import run_judge_eval

EVALS_DIR = Path(__file__).resolve().parent
ANALYST_DATASET_PATH = EVALS_DIR / "golden_dataset.jsonl"
CLASSIFICATION_DATASET_PATH = EVALS_DIR / "classification_golden_dataset.jsonl"


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            cases.append(json.loads(line))
    return cases


def _build_eval_report(*, total: int, passed: int, cases: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "score": round(passed / total, 4) if total else 0.0,
        "cases": cases,
    }


async def run_classification_eval(client=None) -> dict[str, Any]:
    client = client or MockLLMClient()
    cases = []
    passed = 0

    for case in _load_jsonl(CLASSIFICATION_DATASET_PATH):
        input_guardrail = validate_user_input(case["message"])

        if case.get("should_block"):
            ok = input_guardrail.blocked
            if case.get("block_category"):
                expected = GuardrailCategory(case["block_category"])
                ok = ok and expected in input_guardrail.categories
            passed += int(ok)
            cases.append(
                {
                    "message": case["message"],
                    "blocked": input_guardrail.blocked,
                    "categories": [item.value for item in input_guardrail.categories],
                    "reasons": input_guardrail.reasons,
                    "pass": ok,
                }
            )
            continue

        if input_guardrail.blocked:
            cases.append(
                {
                    "message": case["message"],
                    "blocked": True,
                    "pass": False,
                    "reason": "Unexpected input guardrail block",
                }
            )
            continue

        result = await classify_customer_message(case["message"], client)
        ok = result.intent.value == case["expected_intent"]
        ok = ok and result.risk_level.value == case["expected_risk_level"]
        ok = ok and result.needs_human_approval == case["expected_needs_human_approval"]
        passed += int(ok)

        cases.append(
            {
                "message": case["message"],
                "blocked": False,
                "intent": result.intent.value,
                "risk_level": result.risk_level.value,
                "needs_human_approval": result.needs_human_approval,
                "expected_intent": case["expected_intent"],
                "expected_risk_level": case["expected_risk_level"],
                "expected_needs_human_approval": case["expected_needs_human_approval"],
                "pass": ok,
            }
        )

    return _build_eval_report(total=len(cases), passed=passed, cases=cases)


async def run_analyst_eval(client=None) -> dict[str, Any]:
    client = client or MockLLMClient()
    cases = []
    passed = 0

    for case in _load_jsonl(ANALYST_DATASET_PATH):
        result = await run_data_analyst(
            question=case["question"],
            tenant_id=case["tenant_id"],
            client=client,
            approval_granted=case.get("needs_human_approval", False),
        )

        guardrail = validate_sql(result.final_sql, tenant_id=case["tenant_id"])
        correctness = validate_sql_correctness(
            result.final_sql,
            question=case["question"],
            tenant_id=case["tenant_id"],
        )

        ok = guardrail.allowed == case["should_allow"]
        ok = ok and (result.needs_human_approval == case["needs_human_approval"])
        ok = ok and (case["expected_sql_contains"].upper() in result.final_sql.upper())
        if case["should_allow"]:
            ok = ok and correctness.is_correct
        passed += int(ok)

        cases.append(
            {
                "question": case["question"],
                "generated_sql": result.generated_sql,
                "final_sql": result.final_sql,
                "allowed": guardrail.allowed,
                "sql_correct": correctness.is_correct,
                "sql_repaired": result.sql_repaired,
                "needs_human_approval": result.needs_human_approval,
                "pass": ok,
            }
        )

    return _build_eval_report(total=len(cases), passed=passed, cases=cases)


async def run_golden_dataset_eval(client=None) -> dict[str, Any]:
    """Geriye dönük uyumluluk — analyst eval alias."""
    return await run_analyst_eval(client)


async def run_all_evals(client=None) -> dict[str, Any]:
    client = client or MockLLMClient()
    classification = await run_classification_eval(client)
    analyst = await run_analyst_eval(client)
    judge = await run_judge_eval(client)

    total = classification["total"] + analyst["total"] + judge["total"]
    passed = classification["passed"] + analyst["passed"] + judge["passed"]

    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "score": round(passed / total, 4) if total else 0.0,
        "suites": {
            "classification": classification,
            "analyst": analyst,
            "judge": judge,
        },
    }


def format_eval_summary(report: dict[str, Any], *, suite_name: str = "eval") -> str:
    return (
        f"[{suite_name}] score={report['score']:.2%} "
        f"passed={report['passed']}/{report['total']} failed={report['failed']}"
    )


if __name__ == "__main__":
    import asyncio

    async def _main() -> None:
        report = await run_all_evals()
        print(format_eval_summary(report["suites"]["classification"], suite_name="classification"))
        print(format_eval_summary(report["suites"]["analyst"], suite_name="analyst"))
        print(format_eval_summary(report, suite_name="all"))

    asyncio.run(_main())
