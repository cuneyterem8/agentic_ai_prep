from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import unquote

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.data.models import Base


def _ensure_sqlite_parent_dir(database_url: str) -> None:
    """Create parent folders for file-based SQLite URLs (e.g. ./data/app.db)."""
    if ":memory:" in database_url:
        return
    if not database_url.startswith("sqlite"):
        return

    path_part = database_url.split(":///", 1)[-1]
    if not path_part:
        return

    # Windows absolute: sqlite:///C:/path/db.sqlite
    if path_part.startswith("/") and len(path_part) > 2 and path_part[2] == ":":
        path_part = path_part[1:]

    db_path = Path(unquote(path_part))
    if db_path.parent != Path("."):
        db_path.parent.mkdir(parents=True, exist_ok=True)


def create_db_engine(database_url: str) -> Engine:
    _ensure_sqlite_parent_dir(database_url)
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args, future=True)


def init_database(engine: Engine) -> None:
    Base.metadata.create_all(engine)


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@contextmanager
def session_scope(factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
