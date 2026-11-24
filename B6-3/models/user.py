"""사용자 계정 정보와 프로젝트 소유 관계 정의"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

# 런타임 순환 import 방지를 위한 타입 검사 전용 import
if TYPE_CHECKING:
    from models.project import Project


class User(Base):
    """로컬·OAuth 계정과 프로젝트 소유 정보를 저장하는 사용자 모델

    OAuth 공급자와 사용자 식별자 조합의 고유성 보장
    Project.owner와 연결되는 양방향 1:N 관계
    """
    __tablename__ = "users"
    # 같은 소셜 계정의 중복 저장 방지를 위한 공급자·사용자 식별자 조합의 고유 제약
    __table_args__ = (
        UniqueConstraint("oauth_provider", "oauth_subject", name="uq_user_oauth_identity"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    oauth_provider: Mapped[str | None] = mapped_column(String(30))
    oauth_subject: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # 소유자 없는 프로젝트 방지를 위한 사용자 삭제 시 프로젝트 연쇄 삭제
    projects: Mapped[list["Project"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
