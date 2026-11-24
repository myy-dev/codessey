"""프로젝트 정보와 사용자·할 일 관계 정의"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

# 런타임 순환 import 방지를 위한 타입 검사 전용 import
if TYPE_CHECKING:
    from models.task import Task
    from models.user import User


class Project(Base):
    """사용자가 소유하고 여러 할 일을 포함하는 프로젝트 모델

    User.projects와 연결되는 소유자 관계
    Task.project와 연결되는 양방향 1:N 관계
    """
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    owner: Mapped["User"] = relationship(back_populates="projects")
    # 소속 프로젝트 없는 할 일 방지를 위한 프로젝트 삭제 시 할 일 연쇄 삭제
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Task.created_at.desc()",
    )
