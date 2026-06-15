"""Run end-to-end case study scenarios against the integrated workflow."""

from __future__ import annotations

import argparse
import asyncio
import json
import uuid

from src.agents.workflow import CustomerSupportWorkflow, clear_checkpoints
from src.case_study.scenarios import SCENARIOS
from src.llm.mock_client import MockLLMClient
from src.observability.traces import clear_trace_store


async def run_scenario(scenario_name: str | None = None) -> list[dict]:
    clear_checkpoints()
    clear_trace_store()
    client = MockLLMClient()
    workflow = CustomerSupportWorkflow(client)
    results: list[dict] = []

    for scenario in SCENARIOS:
        if scenario_name and scenario.name != scenario_name:
            continue

        conversation_id = f"case-{uuid.uuid4()}"
        result = await workflow.run(
            user_id="employee-1",
            conversation_id=conversation_id,
            customer_message=scenario.message,
        )

        record = {
            "scenario": scenario.name,
            "status": result.status.value,
            "steps_completed": result.steps_completed,
            "needs_human_approval": result.needs_human_approval,
            "trace_id": result.trace_id,
            "final_answer_preview": (result.final_answer or "")[:200],
        }

        if scenario.requires_approval_resume and result.status.value == "awaiting_approval":
            resumed = await workflow.run(
                user_id="employee-1",
                conversation_id=conversation_id,
                customer_message=scenario.message,
                run_id=result.run_id,
                approval_granted=True,
                approval_id=result.approval_id,
            )
            record["resume_status"] = resumed.status.value
            record["resume_steps"] = resumed.steps_completed

        results.append(record)

    return results


def main() -> None:
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Run Agentic AI Prep case study E2E scenarios")
    parser.add_argument("--scenario", help="Run a single scenario by name")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    args = parser.parse_args()

    results = asyncio.run(run_scenario(args.scenario))

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    for item in results:
        print(f"\n=== {item['scenario']} ===")
        print(f"status: {item['status']}")
        print(f"steps: {', '.join(item['steps_completed']) or '-'}")
        if "resume_status" in item:
            print(f"resume_status: {item['resume_status']}")
        print(f"trace_id: {item['trace_id']}")
        print(f"answer: {item['final_answer_preview']}")


if __name__ == "__main__":
    main()
