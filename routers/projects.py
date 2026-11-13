"""로그인 사용자 전용 프로젝트·할 일 요청 처리와 화면 응답"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import RedirectResponse

from auth.dependencies import CurrentUser, DbSession
from auth.security import validate_csrf
from models import TaskStatus
from services import ProjectService, TaskService
from core.ui import add_flash, render


router = APIRouter(prefix="/app", tags=["projects"])


@router.get("/projects", name="project_list")
def project_list(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    q: str = "",
):
    """로그인 사용자의 프로젝트 검색 결과와 전체 집계를 담은 목록 화면 렌더링"""
    service = ProjectService(db)
    projects = service.list_projects(user.id, query=q)
    project_count, task_count, completed_count = service.dashboard_counts(user.id)
    completion_rate = round(completed_count / task_count * 100) if task_count else 0
    return render(
        request,
        "projects/index.html",
        user=user,
        projects=projects,
        q=q,
        project_count=project_count,
        task_count=task_count,
        completed_count=completed_count,
        completion_rate=completion_rate,
    )


@router.post("/projects", name="project_create")
def project_create(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    name: Annotated[str, Form()],
    description: Annotated[str, Form()] = "",
    csrf: Annotated[str, Form()] = "",
):
    """CSRF 검증 후 프로젝트 생성 및 상세 화면으로 이동"""
    validate_csrf(request, csrf)
    project = ProjectService(db).create_project(
        owner_id=user.id, name=name, description=description
    )
    add_flash(request, f"‘{project.name}’ 프로젝트를 만들었습니다.")
    return RedirectResponse(f"/app/projects/{project.id}", status_code=303)


@router.get("/projects/{project_id}", name="project_detail")
def project_detail(
    project_id: int,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    status: Annotated[str, Query()] = "",
    q: Annotated[str, Query()] = "",
):
    """소유 프로젝트와 검색·상태 필터를 적용한 할 일 목록의 상세 화면 렌더링"""
    project, tasks = TaskService(db).get_project_detail(
        project_id=project_id,
        owner_id=user.id,
        status=status,
        query=q,
    )
    return render(
        request,
        "projects/detail.html",
        user=user,
        project=project,
        tasks=tasks,
        statuses=list(TaskStatus),
        selected_status=status,
        q=q,
    )


@router.post("/projects/{project_id}/tasks", name="task_create")
def task_create(
    project_id: int,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    title: Annotated[str, Form()],
    description: Annotated[str, Form()] = "",
    csrf: Annotated[str, Form()] = "",
):
    """CSRF 검증 후 소유 프로젝트에 할 일 추가 및 상세 화면으로 이동"""
    validate_csrf(request, csrf)
    task = TaskService(db).create_task(
        project_id=project_id,
        owner_id=user.id,
        title=title,
        description=description,
    )
    add_flash(request, f"‘{task.title}’ 할 일을 추가했습니다.")
    return RedirectResponse(f"/app/projects/{project_id}", status_code=303)


@router.post("/tasks/{task_id}/status", name="task_change_status")
def task_change_status(
    task_id: int,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    new_status: Annotated[str, Form()],
    csrf: Annotated[str, Form()],
):
    """CSRF 검증 후 할 일 상태 변경 및 변경 전후 상태 알림 저장"""
    validate_csrf(request, csrf)
    task, previous_status = TaskService(db).change_status(
        task_id=task_id,
        owner_id=user.id,
        new_status=new_status,
    )
    add_flash(
        request,
        f"‘{task.title}’ 상태를 {previous_status} → {task.status_label}(으)로 변경했습니다.",
    )
    return RedirectResponse(f"/app/projects/{task.project_id}", status_code=303)


@router.post("/tasks/{task_id}/delete", name="task_delete")
def task_delete(
    task_id: int,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    csrf: Annotated[str, Form()],
):
    """CSRF 검증 후 할 일 삭제 및 소속 프로젝트 상세 화면으로 이동"""
    validate_csrf(request, csrf)
    project_id = TaskService(db).delete_task(task_id=task_id, owner_id=user.id)
    add_flash(request, "할 일을 삭제했습니다.")
    return RedirectResponse(f"/app/projects/{project_id}", status_code=303)


@router.post("/projects/{project_id}/delete", name="project_delete")
def project_delete(
    project_id: int,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    csrf: Annotated[str, Form()],
):
    """CSRF 검증 후 프로젝트와 소속 할 일 삭제 및 프로젝트 목록으로 이동"""
    validate_csrf(request, csrf)
    ProjectService(db).delete_project(project_id=project_id, owner_id=user.id)
    add_flash(request, "프로젝트와 연결된 할 일을 삭제했습니다.")
    return RedirectResponse("/app/projects", status_code=303)
