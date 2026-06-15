import re

from pydantic import BaseModel, Field

from src.llm.base import LLMClient, Message, MessageRole
from src.llm.service import generate_chat_response
from src.security.guardrails import SqlGuardrailResult, SqlRiskLevel, validate_sql
from src.security.sql_correctness import (
    SqlCorrectnessResult,
    SqlIntent,
    build_canonical_sql,
    detect_sql_intent,
    repair_sql,
    validate_sql_correctness,
)


class DataAnalystResult(BaseModel):
    question: str
    generated_sql: str
    final_sql: str
    guardrail: SqlGuardrailResult
    correctness: SqlCorrectnessResult
    sql_repaired: bool
    needs_human_approval: bool
    executed: bool
    rows: list[dict] = Field(default_factory=list)
    analysis_summary: str = ""
    confidence: float = 0.0


TRANSACTIONS_TABLE = [
    {"id": 1, "tenant_id": "tenant-a", "customer_id": "c-1", "amount": 1200.0, "category": "groceries"},
    {"id": 2, "tenant_id": "tenant-a", "customer_id": "c-2", "amount": 45000.0, "category": "transfer"},
    {"id": 3, "tenant_id": "tenant-a", "customer_id": "c-1", "amount": 300.0, "category": "food"},
    {"id": 4, "tenant_id": "tenant-b", "customer_id": "c-9", "amount": 900.0, "category": "utilities"},
    {"id": 5, "tenant_id": "tenant-b", "customer_id": "c-9", "amount": 150000.0, "category": "transfer"},
]

SQL_ANALYST_SYSTEM_PROMPT = """You are a read-only SQL analyst for banking transactions.
Return ONLY one SELECT SQL query for table `transactions` with columns:
id, tenant_id, customer_id, amount, category
Rules:
- SELECT only
- always filter tenant_id
- always include LIMIT
- total/sum questions must use SUM(amount)
- top/highest questions must use ORDER BY amount DESC
"""


def build_sql_generation_messages(question: str, tenant_id: str) -> list[Message]:
    return [
        Message(role=MessageRole.SYSTEM, content=SQL_ANALYST_SYSTEM_PROMPT),
        Message(
            role=MessageRole.USER,
            content=f"Tenant: {tenant_id}\nQuestion: {question}\nReturn SQL only.",
        ),
    ]


SQL_REGENERATION_SYSTEM_PROMPT = """You regenerate SQL for a read-only banking analyst.
Hard rules:
- Return exactly ONE SELECT query
- NEVER use DELETE, DROP, UPDATE, INSERT, TRUNCATE, ALTER
- Always filter tenant_id
- Always include LIMIT
- Match the business question with correct SELECT semantics
"""


def build_sql_regeneration_messages(
    question: str,
    tenant_id: str,
    bad_sql: str,
    *,
    safety: SqlGuardrailResult,
    correctness: SqlCorrectnessResult,
) -> list[Message]:
    issues: list[str] = []
    if not safety.allowed:
        issues.extend(safety.reasons)
    if not correctness.is_correct:
        issues.extend(correctness.issues)

    canonical = build_canonical_sql(question, tenant_id)

    return [
        Message(role=MessageRole.SYSTEM, content=SQL_REGENERATION_SYSTEM_PROMPT),
        Message(
            role=MessageRole.USER,
            content=(
                f"Tenant: {tenant_id}\n"
                f"Question: {question}\n"
                f"Rejected SQL: {bad_sql}\n"
                f"Problems: {', '.join(issues) if issues else 'unknown'}\n"
                f"Reference correct pattern: {canonical}\n"
                f"Return corrected SELECT SQL only."
            ),
        ),
    ]


def build_sql_repair_messages(question: str, tenant_id: str, bad_sql: str, issues: list[str]) -> list[Message]:
    return build_sql_regeneration_messages(
        question,
        tenant_id,
        bad_sql,
        safety=SqlGuardrailResult(
            allowed=False,
            needs_human_approval=False,
            risk_level=SqlRiskLevel.HIGH,
            reasons=issues,
        ),
        correctness=SqlCorrectnessResult(
            is_correct=False,
            intent=detect_sql_intent(question),
            issues=issues,
        ),
    )


async def generate_sql_query(
    question: str,
    tenant_id: str,
    client: LLMClient,
) -> str:
    response = await generate_chat_response(
        build_sql_generation_messages(question, tenant_id),
        client,
        timeout_seconds=15.0,
        max_attempts=1,
    )
    sql = response.content.strip()
    if sql:
        return sql
    return build_canonical_sql(question, tenant_id)


async def generate_validated_sql(
    question: str,
    tenant_id: str,
    client: LLMClient,
    *,
    max_regenerations: int = 2,
) -> tuple[str, str, SqlCorrectnessResult, bool]:
    """Üret → güvenlik/doğruluk kontrol → prompt düzelt → LLM ile yeniden üret."""
    generated_sql = await generate_sql_query(question, tenant_id, client)
    final_sql = generated_sql
    repaired = False

    for attempt in range(max_regenerations + 1):
        safety = validate_sql(final_sql, tenant_id=tenant_id)
        correctness = validate_sql_correctness(
            final_sql,
            question=question,
            tenant_id=tenant_id,
        )

        if safety.allowed and correctness.is_correct:
            return generated_sql, final_sql, correctness, repaired

        if attempt >= max_regenerations:
            break

        response = await generate_chat_response(
            build_sql_regeneration_messages(
                question,
                tenant_id,
                final_sql,
                safety=safety,
                correctness=correctness,
            ),
            client,
            timeout_seconds=12.0,
            max_attempts=1,
        )
        candidate = response.content.strip()
        if candidate:
            final_sql = candidate
            repaired = True
            continue

        final_sql = build_canonical_sql(question, tenant_id)
        repaired = True

    safety = validate_sql(final_sql, tenant_id=tenant_id)
    correctness = validate_sql_correctness(
        final_sql,
        question=question,
        tenant_id=tenant_id,
    )

    if safety.allowed and not correctness.is_correct:
        final_sql = build_canonical_sql(question, tenant_id)
        correctness = validate_sql_correctness(
            final_sql,
            question=question,
            tenant_id=tenant_id,
        )
        repaired = True

    return generated_sql, final_sql, correctness, repaired


def execute_safe_select(sql: str, *, tenant_id: str) -> list[dict]:
    normalized = " ".join(sql.upper().split())
    rows = [row for row in TRANSACTIONS_TABLE if row["tenant_id"] == tenant_id]

    if "SUM(AMOUNT)" in normalized:
        total = sum(row["amount"] for row in rows)
        return [{"total_amount": total}]

    if "ORDER BY AMOUNT DESC" in normalized:
        sorted_rows = sorted(rows, key=lambda item: item["amount"], reverse=True)
        return sorted_rows[:_search_limit(normalized)]

    return rows[:_search_limit(normalized)]


def _search_limit(normalized_sql: str) -> int:
    match = re.search(r"LIMIT\s+(\d+)", normalized_sql)
    return int(match.group(1)) if match else 20


def validate_result_shape(question: str, rows: list[dict]) -> tuple[bool, list[str]]:
    intent_issues: list[str] = []
    intent = detect_sql_intent(question)

    if intent == SqlIntent.AGGREGATE_TOTAL:
        if not rows or "total_amount" not in rows[0]:
            intent_issues.append("Aggregate query did not return total_amount")
    elif intent == SqlIntent.TOP_N and rows:
        amounts = [row.get("amount", 0) for row in rows if "amount" in row]
        if amounts and amounts != sorted(amounts, reverse=True):
            intent_issues.append("Top-N result is not sorted by amount desc")

    return len(intent_issues) == 0, intent_issues


def build_analysis_summary(
    question: str,
    rows: list[dict],
    *,
    sql_repaired: bool,
    correctness: SqlCorrectnessResult,
) -> tuple[str, float]:
    if not rows:
        return "No rows matched the query.", 0.55

    confidence = 0.92 if correctness.is_correct and not sql_repaired else 0.82
    if sql_repaired:
        confidence -= 0.08

    if len(rows) == 1 and "total_amount" in rows[0]:
        total = rows[0]["total_amount"]
        prefix = "Validated SQL" if correctness.is_correct else "Repaired SQL"
        return f"{prefix}: total amount for tenant is {total:.2f} TL.", confidence

    top = max(rows, key=lambda row: row.get("amount", 0))
    return (
        f"Found {len(rows)} transactions. Highest amount: {top.get('amount', 0)} TL.",
        confidence,
    )


async def run_data_analyst(
    *,
    question: str,
    tenant_id: str,
    client: LLMClient,
    approval_granted: bool = False,
) -> DataAnalystResult:
    generated_sql, final_sql, correctness, sql_repaired = await generate_validated_sql(
        question,
        tenant_id,
        client,
    )

    guardrail = validate_sql(final_sql, tenant_id=tenant_id)

    if not guardrail.allowed:
        return DataAnalystResult(
            question=question,
            generated_sql=generated_sql,
            final_sql=final_sql,
            guardrail=guardrail,
            correctness=correctness,
            sql_repaired=sql_repaired,
            needs_human_approval=False,
            executed=False,
            analysis_summary=(
                "SQL could not be regenerated into a safe read-only query: "
                + ", ".join(guardrail.reasons)
            ),
            confidence=0.0,
        )

    if guardrail.needs_human_approval and not approval_granted:
        return DataAnalystResult(
            question=question,
            generated_sql=generated_sql,
            final_sql=final_sql,
            guardrail=guardrail,
            correctness=correctness,
            sql_repaired=sql_repaired,
            needs_human_approval=True,
            executed=False,
            analysis_summary="High-risk SQL requires human approval before execution.",
            confidence=0.65,
        )

    rows = execute_safe_select(final_sql, tenant_id=tenant_id)
    shape_ok, shape_issues = validate_result_shape(question, rows)
    if not shape_ok:
        return DataAnalystResult(
            question=question,
            generated_sql=generated_sql,
            final_sql=final_sql,
            guardrail=guardrail,
            correctness=correctness,
            sql_repaired=sql_repaired,
            needs_human_approval=False,
            executed=False,
            analysis_summary=f"Result validation failed: {', '.join(shape_issues)}",
            confidence=0.4,
        )

    summary, confidence = build_analysis_summary(
        question,
        rows,
        sql_repaired=sql_repaired,
        correctness=correctness,
    )

    return DataAnalystResult(
        question=question,
        generated_sql=generated_sql,
        final_sql=final_sql,
        guardrail=guardrail,
        correctness=correctness,
        sql_repaired=sql_repaired,
        needs_human_approval=guardrail.needs_human_approval,
        executed=True,
        rows=rows,
        analysis_summary=summary,
        confidence=confidence,
    )
