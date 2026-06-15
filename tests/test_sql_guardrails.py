import pytest

from src.agents.data_analyst import generate_validated_sql, run_data_analyst
from src.evals.run_evals import run_golden_dataset_eval
from src.llm.base import LLMResponse, Message, MessageRole
from src.llm.mock_client import MockLLMClient
from src.security.guardrails import validate_sql
from src.security.sql_correctness import validate_sql_correctness


class WrongSqlMockClient:
    """İlk üretimde kasıtlı yanlış SQL döner — regeneration katmanını test eder."""

    async def complete(self, messages: list[Message]) -> LLMResponse:
        system = " ".join(m.content.lower() for m in messages if m.role == MessageRole.SYSTEM)
        if "regenerate sql" in system or "fix sql" in system:
            return LLMResponse(
                content=(
                    "SELECT SUM(amount) AS total_amount FROM transactions "
                    "WHERE tenant_id = 'tenant-a' LIMIT 100"
                ),
                model="wrong-sql-mock",
            )
        return LLMResponse(
            content=(
                "SELECT id, amount FROM transactions "
                "WHERE tenant_id = 'tenant-a' LIMIT 20"
            ),
            model="wrong-sql-mock",
        )

    async def stream(self, messages: list[Message]):
        if False:
            yield


def test_validate_sql_blocks_drop():
    result = validate_sql("DROP TABLE transactions", tenant_id="tenant-a")
    assert result.allowed is False
    assert any("DROP" in reason for reason in result.reasons)


def test_validate_sql_blocks_delete():
    result = validate_sql(
        "DELETE FROM transactions WHERE tenant_id = 'tenant-a'",
        tenant_id="tenant-a",
    )
    assert result.allowed is False


def test_validate_sql_blocks_cross_tenant_missing_filter():
    result = validate_sql(
        "SELECT id, amount FROM transactions LIMIT 10",
        tenant_id="tenant-a",
    )
    assert result.allowed is False
    assert any("Tenant filter" in reason for reason in result.reasons)


def test_validate_sql_allows_safe_select():
    result = validate_sql(
        "SELECT id, amount FROM transactions WHERE tenant_id = 'tenant-a' LIMIT 20",
        tenant_id="tenant-a",
    )
    assert result.allowed is True
    assert result.needs_human_approval is False


def test_validate_sql_marks_aggregate_as_needing_approval():
    result = validate_sql(
        "SELECT SUM(amount) FROM transactions WHERE tenant_id = 'tenant-a' LIMIT 100",
        tenant_id="tenant-a",
    )
    assert result.allowed is True
    assert result.needs_human_approval is True


@pytest.mark.asyncio
async def test_data_analyst_regenerates_delete_sql_to_safe_select():
    client = MockLLMClient()
    result = await run_data_analyst(
        question="Delete old transactions",
        tenant_id="tenant-a",
        client=client,
    )

    assert "DELETE" in result.generated_sql.upper()
    assert "DELETE" not in result.final_sql.upper()
    assert result.guardrail.allowed is True
    assert result.sql_repaired is True
    assert result.executed is True
    assert result.rows


@pytest.mark.asyncio
async def test_data_analyst_regenerates_drop_sql_to_safe_select():
    client = MockLLMClient()
    result = await run_data_analyst(
        question="Drop transactions table",
        tenant_id="tenant-a",
        client=client,
    )

    assert "DROP" in result.generated_sql.upper()
    assert result.final_sql.upper().startswith("SELECT")
    assert result.executed is True


@pytest.mark.asyncio
async def test_data_analyst_requires_approval_for_sum_query():
    client = MockLLMClient()
    result = await run_data_analyst(
        question="What is total amount by tenant",
        tenant_id="tenant-a",
        client=client,
        approval_granted=False,
    )

    assert result.needs_human_approval is True
    assert result.executed is False


@pytest.mark.asyncio
async def test_data_analyst_executes_after_approval():
    client = MockLLMClient()
    result = await run_data_analyst(
        question="What is total amount by tenant",
        tenant_id="tenant-a",
        client=client,
        approval_granted=True,
    )

    assert result.executed is True
    assert result.rows
    assert result.confidence > 0


@pytest.mark.asyncio
async def test_golden_dataset_eval_runs():
    report = await run_golden_dataset_eval(MockLLMClient())
    assert report["total"] == 5
    assert report["passed"] >= 4


@pytest.mark.asyncio
async def test_wrong_sql_is_repaired_to_correct_aggregate():
    client = WrongSqlMockClient()
    generated, final, correctness, repaired = await generate_validated_sql(
        "What is total amount by tenant",
        "tenant-a",
        client,
    )

    assert "SUM" not in generated.upper()
    assert "SUM" in final.upper()
    assert correctness.is_correct is True
    assert repaired is True


@pytest.mark.asyncio
async def test_repaired_sql_returns_correct_total_amount():
    client = WrongSqlMockClient()
    result = await run_data_analyst(
        question="What is total amount by tenant",
        tenant_id="tenant-a",
        client=client,
        approval_granted=True,
    )

    assert result.executed is True
    assert result.sql_repaired is True
    assert result.correctness.is_correct is True
    assert result.rows[0]["total_amount"] == 46500.0


def test_validate_sql_correctness_detects_missing_sum():
    result = validate_sql_correctness(
        "SELECT id FROM transactions WHERE tenant_id = 'tenant-a' LIMIT 20",
        question="What is total amount by tenant",
        tenant_id="tenant-a",
    )
    assert result.is_correct is False
    assert any("SUM" in issue for issue in result.issues)
