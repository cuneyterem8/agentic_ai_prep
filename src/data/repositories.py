import json
from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from src.common.logging import get_correlation_id
from src.data.models import AuditLogORM, ConversationORM, MessageORM, ToolCallORM
from src.security.pii import mask_mapping, mask_pii


@dataclass
class ToolCallRecord:
    id: str
    tool_name: str
    status: str
    output_summary: str
    idempotency_key: str


class ConversationRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def create(
        self,
        *,
        user_id: str,
        conversation_id: str | None = None,
        tenant_id: str = "default",
    ) -> ConversationORM:
        with self._session_factory() as session:
            conversation = ConversationORM(
                id=conversation_id or str(uuid4()),
                user_id=user_id,
                tenant_id=tenant_id,
            )
            session.add(conversation)
            session.commit()
            session.refresh(conversation)
            return conversation

    def get(self, conversation_id: str) -> ConversationORM | None:
        with self._session_factory() as session:
            return session.get(ConversationORM, conversation_id)


class MessageRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def add_message(self, *, conversation_id: str, role: str, content: str) -> MessageORM:
        with self._session_factory() as session:
            message = MessageORM(
                conversation_id=conversation_id,
                role=role,
                content=mask_pii(content),
            )
            session.add(message)
            session.commit()
            session.refresh(message)
            return message

    def list_by_conversation(self, conversation_id: str) -> list[MessageORM]:
        with self._session_factory() as session:
            return (
                session.query(MessageORM)
                .filter(MessageORM.conversation_id == conversation_id)
                .order_by(MessageORM.created_at.asc())
                .all()
            )


class ToolCallRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def get_by_idempotency_key(self, idempotency_key: str) -> ToolCallRecord | None:
        with self._session_factory() as session:
            row = (
                session.query(ToolCallORM)
                .filter(ToolCallORM.idempotency_key == idempotency_key)
                .one_or_none()
            )
            if row is None:
                return None
            return ToolCallRecord(
                id=row.id,
                tool_name=row.tool_name,
                status=row.status,
                output_summary=row.output_summary,
                idempotency_key=row.idempotency_key,
            )

    def save_completed(
        self,
        *,
        conversation_id: str,
        tool_name: str,
        idempotency_key: str,
        input_summary: str,
        output_summary: str,
        actor: str,
        approval_id: str | None,
        latency_ms: float,
    ) -> ToolCallORM:
        with self._session_factory() as session:
            row = ToolCallORM(
                conversation_id=conversation_id,
                tool_name=tool_name,
                idempotency_key=idempotency_key,
                input_summary=mask_pii(input_summary),
                output_summary=mask_pii(output_summary),
                status="completed",
                latency_ms=latency_ms,
                actor=actor,
                approval_id=approval_id,
                correlation_id=get_correlation_id(),
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return row


class AuditLogRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def append(
        self,
        *,
        actor: str,
        action: str,
        risk_level: str,
        details: dict,
    ) -> AuditLogORM:
        masked_details = mask_mapping(details)
        with self._session_factory() as session:
            row = AuditLogORM(
                actor=actor,
                action=action,
                risk_level=risk_level,
                details_json=json.dumps(masked_details, ensure_ascii=False),
                correlation_id=get_correlation_id(),
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return row

    def list_recent(self, limit: int = 20) -> list[AuditLogORM]:
        with self._session_factory() as session:
            return (
                session.query(AuditLogORM)
                .order_by(AuditLogORM.created_at.desc())
                .limit(limit)
                .all()
            )
