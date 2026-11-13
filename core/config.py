"""환경 변수와 기본값을 이용한 애플리케이션 공통 설정 구성"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _as_bool(value: str | None, *, default: bool = False) -> bool:
    """문자열의 불리언 변환 및 값 부재 시 기본값 반환"""
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """앱·DB·세션·GitHub 인증 설정을 보관하는 생성 후 필드 재할당 제한 데이터 클래스"""
    app_name: str
    secret_key: str
    database_url: str
    session_https_only: bool
    github_client_id: str | None
    github_client_secret: str | None


def get_settings() -> Settings:
    """환경 변수 조회와 미설정 항목의 기본값 적용을 통한 설정 객체 생성"""
    return Settings(
        app_name="FlowTask",
        secret_key=os.getenv("APP_SECRET_KEY", "dev-only-change-me-before-deploy"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./database.db"),
        session_https_only=_as_bool(os.getenv("SESSION_HTTPS_ONLY")),
        github_client_id=os.getenv("GITHUB_CLIENT_ID"),
        github_client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
    )


settings = get_settings()

