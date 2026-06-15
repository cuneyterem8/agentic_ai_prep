import re
from enum import Enum

from pydantic import BaseModel, Field


class SqlIntent(str, Enum):
    LIST = "list"
    AGGREGATE_TOTAL = "aggregate_total"
    TOP_N = "top_n"
    JOIN = "join"
    UNKNOWN = "unknown"


class SqlCorrectnessResult(BaseModel):
    is_correct: bool
    intent: SqlIntent
    issues: list[str] = Field(default_factory=list)
    canonical_sql: str | None = None


ALLOWED_COLUMNS = {"id", "tenant_id", "customer_id", "amount", "category"}


def detect_sql_intent(question: str) -> SqlIntent:
    lowered = question.lower()
    if any(word in lowered for word in ("total", "sum", "average", "avg")):
        return SqlIntent.AGGREGATE_TOTAL
    if any(word in lowered for word in ("top", "highest", "largest", "max")):
        return SqlIntent.TOP_N
    if any(word in lowered for word in ("join",)):
        return SqlIntent.JOIN
    if any(word in lowered for word in ("show", "list", "transactions", "display")):
        return SqlIntent.LIST
    return SqlIntent.UNKNOWN


def build_canonical_sql(question: str, tenant_id: str) -> str:
    """Deterministic reference SQL — doğruluk kontrolü ve repair için ground truth."""
    intent = detect_sql_intent(question)

    if intent == SqlIntent.AGGREGATE_TOTAL:
        return (
            f"SELECT SUM(amount) AS total_amount FROM transactions "
            f"WHERE tenant_id = '{tenant_id}' LIMIT 100"
        )
    if intent == SqlIntent.TOP_N:
        return (
            f"SELECT id, customer_id, amount, category FROM transactions "
            f"WHERE tenant_id = '{tenant_id}' ORDER BY amount DESC LIMIT 5"
        )
    if intent == SqlIntent.JOIN:
        return (
            "SELECT t1.id, t2.id FROM transactions t1 "
            "JOIN transactions t2 ON t1.customer_id = t2.customer_id "
            f"WHERE t1.tenant_id = '{tenant_id}' LIMIT 10"
        )
    return (
        f"SELECT id, customer_id, amount, category FROM transactions "
        f"WHERE tenant_id = '{tenant_id}' LIMIT 20"
    )


def _extract_selected_columns(sql: str) -> set[str]:
    upper = sql.upper()
    match = re.search(r"SELECT\s+(.*?)\s+FROM", upper, re.DOTALL)
    if not match:
        return set()

    select_clause = match.group(1)
    if select_clause.strip() == "*":
        return set(ALLOWED_COLUMNS)

    columns: set[str] = set()
    for token in select_clause.split(","):
        cleaned = token.strip()
        cleaned = re.sub(r"^(SUM|AVG|COUNT|MIN|MAX)\s*\(\s*([A-Z0-9_.]+)\s*\).*$", r"\2", cleaned)
        cleaned = cleaned.split()[-1]
        cleaned = cleaned.split(".")[-1]
        columns.add(cleaned.lower())
    return columns


def validate_sql_correctness(
    sql: str,
    *,
    question: str,
    tenant_id: str,
) -> SqlCorrectnessResult:
    """Schema + intent uyumu — LLM SQL'i soruya gerçekten cevap veriyor mu?"""
    normalized = " ".join(sql.strip().split())
    upper = normalized.upper()
    intent = detect_sql_intent(question)
    issues: list[str] = []
    canonical_sql = build_canonical_sql(question, tenant_id)

    unknown_columns = _extract_selected_columns(normalized) - ALLOWED_COLUMNS
    if unknown_columns:
        issues.append(f"Unknown columns referenced: {sorted(unknown_columns)}")

    if intent == SqlIntent.AGGREGATE_TOTAL and "SUM(" not in upper:
        issues.append("Aggregate question requires SUM(amount) in SQL")

    if intent == SqlIntent.TOP_N and "ORDER BY" not in upper:
        issues.append("Top-N question requires ORDER BY clause")

    if intent == SqlIntent.TOP_N and "AMOUNT DESC" not in upper:
        issues.append("Top amount question should order by amount DESC")

    if intent == SqlIntent.JOIN and "JOIN" not in upper:
        issues.append("Join question requires JOIN clause")

    if intent == SqlIntent.LIST and "SUM(" in upper:
        issues.append("List question should not use aggregate functions")

    tenant_pattern = rf"tenant_id\s*=\s*['\"]{re.escape(tenant_id)}['\"]"
    if not re.search(tenant_pattern, normalized, re.IGNORECASE):
        issues.append("Canonical tenant filter missing in SQL")

    return SqlCorrectnessResult(
        is_correct=len(issues) == 0,
        intent=intent,
        issues=issues,
        canonical_sql=canonical_sql,
    )


def repair_sql(sql: str, correctness: SqlCorrectnessResult) -> tuple[str, bool]:
    """Semantik olarak hatalı SQL'i canonical ground truth ile düzelt."""
    if correctness.is_correct or not correctness.canonical_sql:
        return sql, False
    return correctness.canonical_sql, True
