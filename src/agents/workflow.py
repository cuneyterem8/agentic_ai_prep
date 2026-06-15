from src.agents.checkpoint import append_audit, from_checkpoint, mark_step_complete, to_checkpoint
from src.agents.classifier import classify_customer_message
from src.agents.policies import PolicyDecision, UserRole, can_execute_tool
from src.agents.state import AgentState, WorkflowResult, WorkflowStatus
from src.agents.tools import get_tool_registry
from src.common.config import get_settings
from src.common.errors import AuthorizationError, ValidationError
from src.data.tool_execution import ToolExecutionService
from src.llm.base import LLMClient
from src.llm.structured_output import IntentType, RiskLevel
from src.observability.metrics import get_metrics
from src.observability.traces import TraceSession, TraceSummary, start_trace
from src.rag.retriever import MockRetriever
from src.security.audit import build_policy_audit_event, to_persistence_payload
from src.security.input_guardrails import validate_tool_arguments, validate_user_input

_checkpoint_store: dict[str, dict] = {}


class CustomerSupportWorkflow:
    """LangGraph-style explicit workflow — node/edge/state kontrolü framework dışında."""

    def __init__(
        self,
        client: LLMClient,
        retriever: MockRetriever | None = None,
        tool_execution_service: ToolExecutionService | None = None,
    ) -> None:
        self.client = client
        self.retriever = retriever or MockRetriever()
        self.tools = get_tool_registry()
        self.tool_execution_service = tool_execution_service

    async def run(
        self,
        *,
        user_id: str,
        conversation_id: str,
        customer_message: str,
        approval_granted: bool = False,
        approval_id: str | None = None,
        user_role: UserRole = UserRole.CUSTOMER,
        tenant_id: str = "default",
        run_id: str | None = None,
    ) -> WorkflowResult:
        if run_id and run_id in _checkpoint_store:
            state = from_checkpoint(_checkpoint_store[run_id])
            state.approval_granted = approval_granted
            if approval_id:
                state.approval_id = approval_id
            trace = start_trace(
                run_id=state.run_id,
                prompt_version=get_settings().prompt_version,
            )
            try:
                return await self._resume_from_checkpoint(state, trace)
            except Exception:
                trace_summary = trace.finish(status=state.status.value)
                self._record_workflow_metrics(trace, trace_summary, state.status.value)
                trace.close()
                raise

        state = AgentState(
            user_id=user_id,
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            user_role=user_role,
            customer_message=customer_message,
            approval_granted=approval_granted,
            approval_id=approval_id,
        )

        trace = start_trace(
            run_id=state.run_id,
            prompt_version=get_settings().prompt_version,
        )

        try:
            return await self._execute_from_start(state, trace)
        except Exception as exc:
            state.status = WorkflowStatus.FAILED
            state.error = str(exc)
            append_audit(
                state,
                action="workflow_failed",
                actor="workflow_engine",
                risk_level=RiskLevel.HIGH,
                details={"error": str(exc)},
            )
            self._save_checkpoint(state)
            trace_summary = trace.finish(status=state.status.value)
            self._record_workflow_metrics(trace, trace_summary, state.status.value)
            trace.close()
            raise

    async def _resume_from_checkpoint(
        self,
        state: AgentState,
        trace: TraceSession,
    ) -> WorkflowResult:
        if state.status != WorkflowStatus.AWAITING_APPROVAL:
            return self._finalize_result(state, trace)

        if not state.approval_granted:
            return self._finalize_result(state, trace)

        state.status = WorkflowStatus.RUNNING
        with trace.span("execute_tool", "tool", tool=state.selected_tool):
            await self._execute_tool(state)

        if state.status == WorkflowStatus.AWAITING_APPROVAL:
            self._save_checkpoint(state)
            return self._finalize_result(state, trace)

        with trace.span("final_answer", "generation"):
            await self._final_answer(state)
        with trace.span("audit_log", "audit"):
            await self._audit_log(state)
        state.status = WorkflowStatus.COMPLETED
        self._save_checkpoint(state)
        return self._finalize_result(state, trace)

    async def _execute_from_start(
        self,
        state: AgentState,
        trace: TraceSession,
    ) -> WorkflowResult:
        input_guardrail = validate_user_input(state.customer_message)
        if input_guardrail.blocked:
            state.status = WorkflowStatus.BLOCKED
            state.final_answer = (
                "Mesajınız güvenlik kontrolünden geçemedi. "
                "Lütfen talebinizi yeniden ifade edin."
            )
            append_audit(
                state,
                action="input_guardrail_blocked",
                actor="input_guardrail",
                risk_level=RiskLevel.HIGH,
                details={
                    "categories": [item.value for item in input_guardrail.categories],
                    "reasons": input_guardrail.reasons,
                },
            )
            return self._finalize_result(state, trace)

        with trace.span("classify_intent", "classification"):
            await self._classify_intent(state)
        with trace.span("retrieve_context", "retrieval", top_k=3):
            await self._retrieve_context(state)
        with trace.span("decide_action", "routing"):
            await self._decide_action(state)
        with trace.span("request_human_approval", "policy"):
            await self._request_human_approval(state)

        if state.status == WorkflowStatus.AWAITING_APPROVAL:
            self._save_checkpoint(state)
            return self._finalize_result(state, trace)

        with trace.span("execute_tool", "tool", tool=state.selected_tool):
            await self._execute_tool(state)
        with trace.span("final_answer", "generation"):
            await self._final_answer(state)
        with trace.span("audit_log", "audit"):
            await self._audit_log(state)

        state.status = WorkflowStatus.COMPLETED
        self._save_checkpoint(state)
        return self._finalize_result(state, trace)

    async def _classify_intent(self, state: AgentState) -> None:
        state.classification = await classify_customer_message(
            state.customer_message,
            self.client,
            max_repairs=1,
        )
        append_audit(
            state,
            action="classify_intent",
            actor="classification_chain",
            risk_level=state.classification.risk_level,
            details=state.classification.model_dump(),
        )
        mark_step_complete(state, "classify_intent")

    async def _retrieve_context(self, state: AgentState) -> None:
        docs = await self.retriever.retrieve(state.customer_message, top_k=3)
        state.retrieved_doc_ids = [doc.id for doc in docs]
        state.retrieved_context = "\n".join(doc.content for doc in docs)
        append_audit(
            state,
            action="retrieve_context",
            actor="retriever",
            details={"doc_ids": state.retrieved_doc_ids},
        )
        mark_step_complete(state, "retrieve_context")

    async def _decide_action(self, state: AgentState) -> None:
        assert state.classification is not None
        intent = state.classification.intent

        if intent == IntentType.KNOWLEDGE_QUESTION:
            state.selected_tool = "knowledge_search"
            state.tool_arguments = {"query": state.customer_message}
        elif intent == IntentType.ACCOUNT_ACTION:
            state.selected_tool = "transfer_money"
            state.tool_arguments = {
                "amount": 80_000,
                "destination": "TR000000000000000000000000",
            }
            state.needs_human_approval = True
        elif intent == IntentType.COMPLAINT:
            state.selected_tool = None
        else:
            state.selected_tool = None

        append_audit(
            state,
            action="decide_action",
            actor="workflow_router",
            risk_level=state.classification.risk_level,
            details={
                "selected_tool": state.selected_tool,
                "intent": intent.value,
            },
        )
        mark_step_complete(state, "decide_action")

    async def _request_human_approval(self, state: AgentState) -> None:
        if not state.selected_tool:
            mark_step_complete(state, "request_human_approval")
            return

        policy = can_execute_tool(
            user_id=state.user_id,
            tool_name=state.selected_tool,
            classification=state.classification,
            approval_granted=state.approval_granted,
            user_role=state.user_role,
        )

        if policy.decision == PolicyDecision.REQUIRE_APPROVAL:
            state.needs_human_approval = True
            state.status = WorkflowStatus.AWAITING_APPROVAL
            state.approval_id = state.approval_id or state.idempotency_key
            compliance_event = build_policy_audit_event(
                actor="policy_engine",
                tenant_id=state.tenant_id,
                action="request_human_approval",
                risk_level=policy.risk_level.value,
                approval_id=state.approval_id,
                result_status="pending",
                details={
                    "tool": state.selected_tool,
                    "reason": policy.reason,
                    "effective_role": policy.effective_role.value if policy.effective_role else None,
                },
            )
            append_audit(
                state,
                action="request_human_approval",
                actor="policy_engine",
                risk_level=policy.risk_level,
                details=to_persistence_payload(compliance_event),
            )
        else:
            append_audit(
                state,
                action="approval_not_required",
                actor="policy_engine",
                details={"tool": state.selected_tool},
            )

        mark_step_complete(state, "request_human_approval")

    async def _execute_tool(self, state: AgentState) -> None:
        if not state.selected_tool:
            mark_step_complete(state, "execute_tool")
            return

        if state.tool_executed:
            append_audit(
                state,
                action="execute_tool_skipped",
                actor="workflow_engine",
                details={"reason": "idempotent skip"},
            )
            mark_step_complete(state, "execute_tool")
            return

        policy = can_execute_tool(
            user_id=state.user_id,
            tool_name=state.selected_tool,
            classification=state.classification,
            approval_granted=state.approval_granted,
            user_role=state.user_role,
        )

        if policy.decision == PolicyDecision.DENY:
            state.status = WorkflowStatus.BLOCKED
            append_audit(
                state,
                action="execute_tool_denied",
                actor="policy_engine",
                risk_level=policy.risk_level,
                details={"reason": policy.reason},
            )
            raise AuthorizationError(policy.reason)

        if policy.decision == PolicyDecision.REQUIRE_APPROVAL:
            state.status = WorkflowStatus.AWAITING_APPROVAL
            mark_step_complete(state, "execute_tool")
            return

        tool_validation = validate_tool_arguments(
            state.selected_tool,
            state.tool_arguments,
        )
        if tool_validation.blocked:
            state.status = WorkflowStatus.BLOCKED
            append_audit(
                state,
                action="tool_validation_blocked",
                actor="tool_guardrail",
                risk_level=RiskLevel.HIGH,
                details={"reasons": tool_validation.reasons},
            )
            raise ValidationError(
                "Tool arguments failed validation: " + ", ".join(tool_validation.reasons)
            )

        tool = self.tools[state.selected_tool]
        if self.tool_execution_service:
            state.tool_result, replayed = await self.tool_execution_service.execute_tool(
                conversation_id=state.conversation_id,
                tool=tool,
                tool_name=state.selected_tool,
                arguments=state.tool_arguments,
                actor=state.user_id,
                tenant_id=state.tenant_id,
                idempotency_key=state.idempotency_key,
                approval_id=state.approval_id,
                risk_level=policy.risk_level.value,
            )
            state.tool_executed = True
            append_audit(
                state,
                action="execute_tool",
                actor=state.user_id,
                risk_level=policy.risk_level,
                details={
                    "tool": state.selected_tool,
                    "success": state.tool_result.success,
                    "idempotency_key": state.idempotency_key,
                    "replayed": replayed,
                },
            )
            mark_step_complete(state, "execute_tool")
            return

        state.tool_result = await tool.run(state.tool_arguments)
        state.tool_executed = True

        append_audit(
            state,
            action="execute_tool",
            actor=state.user_id,
            risk_level=policy.risk_level,
            details={
                "tool": state.selected_tool,
                "success": state.tool_result.success,
                "idempotency_key": state.idempotency_key,
            },
        )
        mark_step_complete(state, "execute_tool")

    async def _final_answer(self, state: AgentState) -> None:
        assert state.classification is not None

        if state.tool_result and state.tool_result.success:
            state.final_answer = (
                f"{state.tool_result.output}\n"
                f"Sources: {', '.join(state.retrieved_doc_ids) or 'none'}"
            )
        elif state.classification.intent == IntentType.COMPLAINT:
            state.final_answer = (
                "Şikayetiniz kaydedildi. İlgili ekip 2 saat içinde dönüş yapacaktır. "
                f"Kaynaklar: {', '.join(state.retrieved_doc_ids)}"
            )
        elif state.retrieved_context:
            state.final_answer = (
                f"İlgili politika bilgisi:\n{state.retrieved_context}\n"
                f"Kaynaklar: {', '.join(state.retrieved_doc_ids)}"
            )
        else:
            state.final_answer = (
                "Talebinizi net anlayamadım. Lütfen daha fazla detay paylaşın."
            )

        mark_step_complete(state, "final_answer")

    async def _audit_log(self, state: AgentState) -> None:
        append_audit(
            state,
            action="audit_log",
            actor="workflow_engine",
            details={
                "steps_completed": state.steps_completed,
                "status": state.status.value,
            },
        )
        mark_step_complete(state, "audit_log")

    def _save_checkpoint(self, state: AgentState) -> None:
        _checkpoint_store[state.run_id] = to_checkpoint(state)

    def _finalize_result(
        self,
        state: AgentState,
        trace: TraceSession,
    ) -> WorkflowResult:
        trace_summary = trace.finish(status=state.status.value)
        self._record_workflow_metrics(trace, trace_summary, state.status.value)
        trace.close()
        return self._to_result(state, trace_summary)

    def _record_workflow_metrics(
        self,
        trace: TraceSession,
        trace_summary: TraceSummary,
        status: str,
    ) -> None:
        step_latencies = {
            span.name: span.latency_ms
            for span in trace.spans
            if span.kind != "llm"
        }
        get_metrics().record_workflow_run(
            status=status,
            latency_ms=trace_summary.total_latency_ms,
            step_latencies=step_latencies,
        )

    def _to_result(
        self,
        state: AgentState,
        trace_summary: TraceSummary | None = None,
    ) -> WorkflowResult:
        return WorkflowResult(
            run_id=state.run_id,
            conversation_id=state.conversation_id,
            status=state.status,
            final_answer=state.final_answer,
            needs_human_approval=state.needs_human_approval,
            approval_id=state.approval_id,
            selected_tool=state.selected_tool,
            audit_events=state.audit_events,
            steps_completed=state.steps_completed,
            trace_id=trace_summary.trace_id if trace_summary else None,
            trace_summary=trace_summary,
        )


def clear_checkpoints() -> None:
    _checkpoint_store.clear()
