from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "database.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


class Base(DeclarativeBase):
    """모든 SQLAlchemy ORM 모델의 공통 기본 클래스"""


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def create_db_and_tables() -> None:
    """애플리케이션 시작 시 누락된 테이블 생성"""

    # 모델 로딩을 통한 Base의 테이블 메타데이터 등록
    from app.models.memo import Memo  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """요청별 DB 세션 제공 및 요청 종료 시 세션 정리"""

    with SessionLocal() as db:
        yield db
