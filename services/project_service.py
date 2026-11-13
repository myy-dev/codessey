"""프로젝트 입력 검증과 소유권 검사 및 조회·생성·삭제 처리"""

from __future__ import annotations

from sqlalchemy.orm import Session

from core.exceptions import AppError, ForbiddenError, NotFoundError
from models import Project
from repositories import ProjectRepository


class ProjectService:
    """프로젝트 업무 규칙 검증과 데이터 접근 요청을 담당하는 서비스"""
    def __init__(self, db: Session) -> None:
        """요청의 DB 세션을 사용하는 프로젝트 저장소 준비"""
        self.projects = ProjectRepository(db)

    def list_projects(self, owner_id: int, *, query: str = "") -> list[Project]:
        """검색어 앞뒤 공백 제거 및 사용자가 소유한 프로젝트 목록 조회"""
        return self.projects.list_for_owner(owner_id, query=query.strip())

    def get_owned_project(self, project_id: int, owner_id: int) -> Project:
        """프로젝트 존재 여부와 소유권 검사 후 프로젝트 반환"""
        project = self.projects.get_by_id(project_id)
        if not project:
            raise NotFoundError("프로젝트를 찾을 수 없습니다.")
        if project.owner_id != owner_id:
            raise ForbiddenError()
        return project

    def create_project(
        self, *, owner_id: int, name: str, description: str
    ) -> Project:
        """이름·설명 공백 제거와 길이 검증 후 프로젝트 생성"""
        name = name.strip()
        description = description.strip()
        if not 2 <= len(name) <= 100:
            raise AppError("프로젝트 이름은 2~100자로 입력해 주세요.")
        if len(description) > 1000:
            raise AppError("프로젝트 설명은 1,000자 이하여야 합니다.")
        return self.projects.create(
            owner_id=owner_id, name=name, description=description
        )

    def delete_project(self, *, project_id: int, owner_id: int) -> None:
        """소유권 검사 후 프로젝트 삭제 및 동시 변경 충돌 처리"""
        project = self.get_owned_project(project_id, owner_id)
        if not self.projects.delete(project, owner_id=owner_id):
            raise AppError(
                "다른 요청에서 프로젝트가 변경되었습니다. 페이지를 새로고침해 주세요.",
                status_code=409,
            )

    def dashboard_counts(self, owner_id: int) -> tuple[int, int, int]:
        """사용자의 프로젝트 수·전체 할 일 수·완료 할 일 수 조회"""
        return self.projects.dashboard_counts(owner_id)

