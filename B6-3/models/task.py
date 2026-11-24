"""할 일 정보와 진행 상태 및 프로젝트 관계 정의"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

# 런타임 순환 import 방지를 위한 타입 검사 전용 import
if TYPE_CHECKING:
    from models.project import Project


class TaskStatus(str, Enum):
    """할 일의 대기·진행 중·완료 상태를 정의하는 문자열 열거형"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

    @property
    def label(self) -> str:
        """상태 열거값에 대응하는 한글 표시명 반환"""
        return {
            self.TODO: "대기",
            self.IN_PROGRESS: "진행 중",
            self.COMPLETED: "완료",
        }[self]


class Task(Base):
    """프로젝트에 속한 할 일과 진행 상태를 저장하는 모델

    Project.tasks와 연결되는 소속 프로젝트 관계
    SQLAlchemy의 onupdate를 통한 수정 시각 자동 갱신
    """
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=TaskStatus.TODO.value, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    project: Mapped["Project"] = relationship(back_populates="tasks")

    @property
    def status_label(self) -> str:
        """저장된 상태 문자열을 열거형으로 변환하여 한글 표시명 반환"""
        return TaskStatus(self.status).label
