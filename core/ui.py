"""Jinja2 화면 렌더링과 일회성 알림을 위한 공통 도구"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from passlib.utils import MAX_PASSWORD_SIZE

from auth.security import csrf_token
from models import User


templates = Jinja2Templates(directory="templates")


def add_flash(request: Request, message: str, *, category: str = "success") -> None:
    """다음 화면에 표시할 일회성 알림 메시지와 유형의 세션 저장"""
    request.session["flash"] = {"message": message, "category": category}


def render(
    request: Request,
    template_name: str,
    *,
    user: User | None = None,
    status_code: int = 200,
    **context: Any,
) -> HTMLResponse:
    """공통 화면 데이터와 개별 데이터를 템플릿에 전달하여 HTML 응답 생성"""
    payload = {
        "request": request,
        "app_name": "FlowTask",
        "styles_version": Path("static/styles.css").stat().st_mtime_ns,
        "current_user": user,
        "csrf_token": csrf_token(request),
        "password_max_length": MAX_PASSWORD_SIZE,
        "flash": request.session.pop("flash", None),
        **context,
    }
    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context=payload,
        status_code=status_code,
    )
