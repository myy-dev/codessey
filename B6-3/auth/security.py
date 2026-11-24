"""로그인 세션 초기화와 CSRF 검증 및 로그인 후 이동 경로 검사"""

from __future__ import annotations

import hmac
import secrets

from fastapi import Request

from core.exceptions import AppError


def start_session(request: Request, user_id: int) -> None:
    """기존 세션 초기화 및 로그인 사용자 ID 저장"""
    request.session.clear()
    request.session["user_id"] = user_id


def csrf_token(request: Request) -> str:
    """세션별 CSRF 토큰 조회 또는 난수 토큰 생성·저장"""
    token = request.session.get("csrf_token")
    if not isinstance(token, str):
        token = secrets.token_urlsafe(32)
        request.session["csrf_token"] = token
    return token


def validate_csrf(request: Request, submitted_token: str) -> None:
    """세션·폼 CSRF 토큰의 상수 시간 비교 및 검증 실패 시 403 오류 발생"""
    expected = request.session.get("csrf_token")
    if not isinstance(expected, str) or not hmac.compare_digest(
        expected.encode("utf-8"), submitted_token.encode("utf-8")
    ):
        raise AppError(
            "요청 검증에 실패했습니다. 페이지를 새로고침해 주세요.", status_code=403
        )


def safe_next_url(value: str | None, *, default: str = "/app/projects") -> str:
    """로그인 후 이동 경로의 선행 슬래시 검사 및 조건 미충족 시 기본 경로 반환"""
    if not value or not value.startswith("/") or value.startswith("//"):
        return default
    return value
