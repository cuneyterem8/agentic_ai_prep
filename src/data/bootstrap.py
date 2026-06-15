from dataclasses import dataclass
from functools import lru_cache

from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from src.common.config import get_settings
from src.data.database import build_session_factory, create_db_engine, init_database
from src.data.repositories import (
    AuditLogRepository,
    ConversationRepository,
    MessageRepository,
    ToolCallRepository,
)
from src.data.tool_execution import ToolExecutionService


@dataclass
class DataStores:
    engine: Engine
    session_factory: sessionmaker
    conversation_repo: ConversationRepository
    message_repo: MessageRepository
    tool_call_repo: ToolCallRepository
    audit_repo: AuditLogRepository
    tool_execution_service: ToolExecutionService


def build_data_stores(database_url: str) -> DataStores:
    engine = create_db_engine(database_url)
    init_database(engine)
    session_factory = build_session_factory(engine)

    conversation_repo = ConversationRepository(session_factory)
    message_repo = MessageRepository(session_factory)
    tool_call_repo = ToolCallRepository(session_factory)
    audit_repo = AuditLogRepository(session_factory)
    tool_execution_service = ToolExecutionService(tool_call_repo, audit_repo)

    return DataStores(
        engine=engine,
        session_factory=session_factory,
        conversation_repo=conversation_repo,
        message_repo=message_repo,
        tool_call_repo=tool_call_repo,
        audit_repo=audit_repo,
        tool_execution_service=tool_execution_service,
    )


@lru_cache
def get_data_stores() -> DataStores:
    settings = get_settings()
    return build_data_stores(settings.database_url)
