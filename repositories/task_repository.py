"""소유권과 동시 변경 조건을 반영한 할 일 데이터 접근"""

from __future__ import annotations

from sqlalchemy import delete, insert, literal, or_, select, update
from sqlalchemy.orm import Session

from models import Project, Task


class TaskRepository:
    """SQLAlchemy를 이용한 할 일 조회·생성·상태 변경·삭제"""
    def __init__(self, db: Session) -> None:
        """할 일 DB 작업에 사용할 세션 보관"""
        self.db = db

    def get_by_id(self, task_id: int) -> Task | None:
        """기본 키로 할 일 조회 또는 None 반환"""
        return self.db.get(Task, task_id)

    def list_for_project(
        self,
        project_id: int,
        *,
        owner_id: int,
        status: str = "",
        query: str = "",
    ) -> list[Task]:
        """프로젝트·소유자 조건과 상태·검색어 필터를 적용한 최신순 할 일 조회"""
        statement = select(Task).where(
            Task.project_id == project_id,
            Task.project.has(Project.owner_id == owner_id),
        )
        if status:
            statement = statement.where(Task.status == status)
        if query:
            pattern = f"%{query}%"
            statement = statement.where(
                or_(Task.title.ilike(pattern), Task.description.ilike(pattern))
            )
        statement = statement.order_by(Task.created_at.desc())
        return list(self.db.scalars(statement).all())

    def create(
        self, *, project_id: int, owner_id: int, title: str, description: str, status: str
    ) -> Task | None:
        """프로젝트 소유권 조건으로 할 일 생성 및 커밋 전 조회 후 반환, 생성 실패 시 None 반환"""
        # 프로젝트 교체에 대비한 INSERT 내부의 소유권 재검사
        statement = (
            insert(Task)
            .from_select(
                ["project_id", "title", "description", "status"],
                select(Project.id, literal(title), literal(description), literal(status))
                .where(Project.id == project_id, Project.owner_id == owner_id),
            )
        )
        result = self.db.execute(statement)
        if result.rowcount != 1:
            self.db.rollback()
            return None
        # 쓰기 트랜잭션의 잠금 해제 전 생성한 행 조회
        # RETURNING 미지원 SQLite와의 호환성을 위한 lastrowid 사용
        task = self.db.scalar(
            select(Task)
            .where(
                Task.id == result.lastrowid,
                Task.project_id == project_id,
                Task.project.has(Project.owner_id == owner_id),
            )
            .execution_options(populate_existing=True)
        )
        if task is None:
            self.db.rollback()
            return None
        self.db.commit()
        return task

    def change_status(self, task: Task, *, owner_id: int, new_status: str) -> bool:
        """할 일 ID·프로젝트·기존 상태·소유자 조건으로 상태 변경 및 객체 갱신과 성공 여부 반환"""
        # 삭제된 ID 재사용에 대비한 UPDATE 시 소유권 재검사
        result = self.db.execute(
            update(Task)
            .where(
                Task.id == task.id,
                Task.project_id == task.project_id,
                Task.status == task.status,
                Task.project.has(Project.owner_id == owner_id),
            )
            .values(status=new_status)
            .execution_options(synchronize_session=False)
        )
        if result.rowcount != 1:
            self.db.rollback()
            return False
        self.db.refresh(task)
        self.db.commit()
        return True

    def delete(self, task: Task, *, owner_id: int) -> bool:
        """할 일 ID·프로젝트·소유자 조건으로 삭제 및 성공 여부 반환"""
        result = self.db.execute(
            delete(Task)
            .where(
                Task.id == task.id,
                Task.project_id == task.project_id,
                Task.project.has(Project.owner_id == owner_id),
            )
            .execution_options(synchronize_session="fetch")
        )
        if result.rowcount != 1:
            self.db.rollback()
            return False
        self.db.commit()
        return True

