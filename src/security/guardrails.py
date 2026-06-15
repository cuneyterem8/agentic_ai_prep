import re
from enum import Enum

from pydantic import BaseModel, Field


class SqlRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SqlGuardrailResult(BaseModel):
    allowed: bool
    needs_human_approval: bool
    risk_level: SqlRiskLevel
    reasons: list[str] = Field(default_factory=list)


FORBIDDEN_KEYWORDS = (
    "DROP",
    "DELETE",
    "UPDATE",
    "INSERT",
    "TRUNCATE",
    "ALTER",
    "GRANT",
    "REVOKE",
    "CREATE",
    "REPLACE",
    "MERGE",
    "EXEC",
    "EXECUTE",
    "CALL",
)

ALLOWED_TABLES = {"transactions"}


def _normalize_sql(sql: str) -> str:
    return " ".join(sql.strip().split())


def validate_sql(
    sql: str,
    *,
    tenant_id: str | None = None,
    max_rows: int = 1000,
) -> SqlGuardrailResult:
    normalized = _normalize_sql(sql)
    upper = normalized.upper()
    reasons: list[str] = []

    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", upper):
            reasons.append(f"Forbidden keyword detected: {keyword}")

    if reasons:
        return SqlGuardrailResult(
            allowed=False,
            needs_human_approval=False,
            risk_level=SqlRiskLevel.HIGH,
            reasons=reasons,
        )

    if not upper.startswith("SELECT"):
        return SqlGuardrailResult(
            allowed=False,
            needs_human_approval=False,
            risk_level=SqlRiskLevel.HIGH,
            reasons=["Only SELECT statements are allowed"],
        )

    if ";" in normalized.rstrip(";"):
        return SqlGuardrailResult(
            allowed=False,
            needs_human_approval=False,
            risk_level=SqlRiskLevel.HIGH,
            reasons=["Multiple SQL statements are not allowed"],
        )

    table_matches = re.findall(r"\bFROM\s+([a-zA-Z_][\w]*)", upper)
    if not table_matches:
        reasons.append("SQL must include a FROM clause")
    else:
        for table in table_matches:
            if table.lower() not in ALLOWED_TABLES:
                reasons.append(f"Table '{table.lower()}' is not in allowlist")

    if tenant_id:
        tenant_pattern = rf"tenant_id\s*=\s*['\"]{re.escape(tenant_id)}['\"]"
        if not re.search(tenant_pattern, normalized, re.IGNORECASE):
            reasons.append("Tenant filter is required for multi-tenant safety")

    if "LIMIT" not in upper:
        reasons.append("LIMIT clause is recommended")

    if reasons:
        return SqlGuardrailResult(
            allowed=False,
            needs_human_approval=False,
            risk_level=SqlRiskLevel.HIGH,
            reasons=reasons,
        )

    needs_human_approval = False
    risk_level = SqlRiskLevel.LOW
    approval_reasons: list[str] = []

    if re.search(r"\bSUM\s*\(\s*AMOUNT\s*\)", upper):
        needs_human_approval = True
        risk_level = SqlRiskLevel.MEDIUM
        approval_reasons.append("Aggregate on amount requires human approval")

    if "JOIN" in upper:
        needs_human_approval = True
        risk_level = SqlRiskLevel.HIGH
        approval_reasons.append("JOIN queries are high risk")

    limit_match = re.search(r"\bLIMIT\s+(\d+)", upper)
    if limit_match and int(limit_match.group(1)) > max_rows:
        return SqlGuardrailResult(
            allowed=False,
            needs_human_approval=False,
            risk_level=SqlRiskLevel.HIGH,
            reasons=[f"LIMIT exceeds max allowed rows ({max_rows})"],
        )

    return SqlGuardrailResult(
        allowed=True,
        needs_human_approval=needs_human_approval,
        risk_level=risk_level,
        reasons=approval_reasons,
    )
