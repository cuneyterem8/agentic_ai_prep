import logging
import time

from src.agents.tools import Tool, ToolResult
from src.data.repositories import AuditLogRepository, ToolCallRepository
from src.security.audit import build_tool_audit_event, to_log_extra, to_persistence_payload
from src.security.pii import mask_pii

logger = logging.getLogger("agenticai")


class ToolExecutionService:
    """Idempotent tool execution + compliance-aware persistent audit/tool logs."""

    def __init__(
        self,
        tool_call_repo: ToolCallRepository,
        audit_repo: AuditLogRepository,
    ) -> None:
        self.tool_call_repo = tool_call_repo
        self.audit_repo = audit_repo

    async def execute_tool(
        self,
        *,
        conversation_id: str,
        tool: Tool,
        tool_name: str,
        arguments: dict,
        actor: str,
        tenant_id: str = "default",
        idempotency_key: str,
        approval_id: str | None,
        risk_level: str,
    ) -> tuple[ToolResult, bool]:
        existing = self.tool_call_repo.get_by_idempotency_key(idempotency_key)
        if existing and existing.status == "completed":
            replay_event = build_tool_audit_event(
                actor="tool_execution_service",
                tenant_id=tenant_id,
                action="tool_call_idempotent_replay",
                tool_name=tool_name,
                arguments=arguments,
                approval_id=approval_id,
                result_status="replayed",
                risk_level=risk_level,
                metadata={"replayed_tool_call_id": existing.id},
            )
            payload = to_persistence_payload(replay_event)
            self.audit_repo.append(
                actor="tool_execution_service",
                action="tool_call_idempotent_replay",
                risk_level=risk_level,
                details=payload,
            )
            logger.info("compliance_audit", extra=to_log_extra(replay_event))
            return (
                ToolResult(
                    tool_name=tool_name,
                    success=True,
                    output=existing.output_summary,
                    metadata={"replayed": True},
                ),
                True,
            )

        started = time.perf_counter()
        result = await tool.run(arguments)
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        masked_output = mask_pii(result.output)

        self.tool_call_repo.save_completed(
            conversation_id=conversation_id,
            tool_name=tool_name,
            idempotency_key=idempotency_key,
            input_summary=str(arguments),
            output_summary=masked_output,
            actor=actor,
            approval_id=approval_id,
            latency_ms=latency_ms,
        )

        completed_event = build_tool_audit_event(
            actor=actor,
            tenant_id=tenant_id,
            action="tool_call_completed",
            tool_name=tool_name,
            arguments=arguments,
            approval_id=approval_id,
            result_status="success" if result.success else "failed",
            risk_level=risk_level,
            metadata={"latency_ms": latency_ms, "conversation_id": conversation_id},
        )
        payload = to_persistence_payload(completed_event)
        self.audit_repo.append(
            actor=actor,
            action="tool_call_completed",
            risk_level=risk_level,
            details=payload,
        )
        logger.info("compliance_audit", extra=to_log_extra(completed_event))

        return (
            ToolResult(
                tool_name=tool_name,
                success=result.success,
                output=masked_output,
                metadata=result.metadata,
            ),
            False,
        )
