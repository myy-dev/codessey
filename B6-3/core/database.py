"""SQLAlchemy 엔진과 DB 세션 설정 및 ORM 테이블 생성"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from core.config import settings


class Base(DeclarativeBase):
    """ORM 모델의 공통 부모 클래스와 테이블 메타데이터 관리"""

    pass


engine_options: dict[str, object] = {"pool_pre_ping": True}
if settings.database_url.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.database_url, **engine_options)


if settings.database_url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
        """새 SQLite 연결마다 외래 키 제약 활성화"""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Depends에 사용할 DB 세션 생성·제공 및 사용 종료 후 세션 정리"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """모델을 메타데이터에 등록하고 DB에 존재하지 않는 테이블 생성"""
    import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
