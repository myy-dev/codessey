"""로그인·세션·OAuth 인증에 사용할 사용자 데이터 접근"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import User


class UserRepository:
    """SQLAlchemy를 이용한 사용자 조회와 로컬·OAuth 계정 저장"""
    def __init__(self, db: Session) -> None:
        """사용자 DB 작업에 사용할 세션 보관"""
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        """기본 키로 사용자 조회 또는 None 반환"""
        return self.db.get(User, user_id)

    def get_by_username(self, username: str) -> User | None:
        """로그인 아이디로 사용자 조회 또는 None 반환"""
        return self.db.scalar(select(User).where(User.username == username))

    def get_by_oauth_identity(self, provider: str, subject: str) -> User | None:
        """OAuth 공급자·외부 사용자 ID 조합으로 사용자 조회 또는 None 반환"""
        return self.db.scalar(
            select(User).where(
                User.oauth_provider == provider,
                User.oauth_subject == subject,
            )
        )

    def create(
        self,
        *,
        username: str,
        display_name: str,
        password_hash: str | None,
        oauth_provider: str | None = None,
        oauth_subject: str | None = None,
    ) -> User:
        """계정 저장 후 객체 갱신·반환 및 무결성 오류 시 롤백과 예외 전달"""
        user = User(
            username=username,
            display_name=display_name,
            password_hash=password_hash,
            oauth_provider=oauth_provider,
            oauth_subject=oauth_subject,
        )
        self.db.add(user)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise
        self.db.refresh(user)
        return user

