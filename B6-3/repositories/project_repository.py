"""프로젝트와 연관 할 일의 데이터 접근 및 집계"""

from __future__ import annotations

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session, selectinload

from models import Project, Task


class ProjectRepository:
    """SQLAlchemy를 이용한 프로젝트 조회·저장·삭제 및 집계"""

    def __init__(self, db: Session) -> None:
        """프로젝트 DB 작업에 사용할 세션 보관"""
        self.db = db

    def list_for_owner(self, owner_id: int, *, query: str = "") -> list[Project]:
        """소유자별 프로젝트 검색·최신순 정렬 및 연관 할 일 일괄 로드"""
        statement = (
            select(Project)
            .where(Project.owner_id == owner_id)
            .options(
                selectinload(
                    Project.tasks.and_(Task.project.has(Project.owner_id == owner_id))
                )
            )
            .order_by(Project.created_at.desc())
        )
        if query:
            pattern = f"%{query}%"
            statement = statement.where(
                or_(Project.name.ilike(pattern), Project.description.ilike(pattern))
            )
        return list(self.db.scalars(statement).all())

    def get_by_id(self, project_id: int) -> Project | None:
        """기본 키로 프로젝트 조회 또는 None 반환"""
        return self.db.get(Project, project_id)

    def create(self, *, owner_id: int, name: str, description: str) -> Project:
        """프로젝트 객체 생성·세션 등록 및 트랜잭션 확정 후 반환"""
        project = Project(owner_id=owner_id, name=name, description=description)
        self.db.add(project)
        self.db.commit()
        return project

    def delete(self, project: Project, *, owner_id: int) -> bool:
        # 소유자 조건에 맞는 프로젝트 삭제 시 DB 연쇄 삭제로 소속 할 일 제거
        """프로젝트 ID와 소유자 조건으로 삭제 및 성공 여부 반환"""
        result = self.db.execute(
            delete(Project)
            .where(Project.id == project.id, Project.owner_id == owner_id)
            .execution_options(synchronize_session="fetch")
        )
        # 삭제 건수가 1이 아니면 대상 부재·소유자 불일치 등으로 판단하여 롤백
        if result.rowcount != 1:
            self.db.rollback()
            return False
        self.db.commit()
        self.db.expire_all()
        return True

    def dashboard_counts(self, owner_id: int) -> tuple[int, int, int]:
        """소유자 기준 프로젝트 수·전체 할 일 수·완료 할 일 수 집계"""
        project_count = (
            self.db.scalar(
                select(func.count(Project.id)).where(Project.owner_id == owner_id)
            )
            or 0
        )
        task_count = (
            self.db.scalar(
                select(func.count(Task.id))
                .join(Project)
                .where(Project.owner_id == owner_id)
            )
            or 0
        )
        completed_count = (
            self.db.scalar(
                select(func.count(Task.id))
                .join(Project)
                .where(Project.owner_id == owner_id, Task.status == "completed")
            )
            or 0
        )
        return project_count, task_count, completed_count
