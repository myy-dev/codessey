"""Depends와 Annotated를 이용한 DB 세션 및 로그인 사용자 주입"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from core.database import get_db
from core.exceptions import AuthenticationRequired
from models import User
from repositories import UserRepository

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user_optional(request: Request, db: DbSession) -> User | None:
    """세션의 사용자 ID로 사용자 조회, 미인증 시 None 반환 및 삭제된 사용자의 세션 정리"""
    user_id = request.session.get("user_id")
    if not isinstance(user_id, int):
        return None
    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        request.session.clear()
    return user


def require_user(
    user: Annotated[User | None, Depends(get_current_user_optional)],
) -> User:
    """로그인 사용자 반환 및 비로그인 요청의 인증 필요 예외 발생"""
    if user is None:
        raise AuthenticationRequired()
    return user


CurrentUser = Annotated[User, Depends(require_user)]
OptionalUser = Annotated[User | None, Depends(get_current_user_optional)]
