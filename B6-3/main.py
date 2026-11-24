"""앱 초기화와 세션 설정, 라우터 등록 및 공통 예외 처리를 담당하는 FastAPI 진입점"""

from __future__ import annotations

from contextlib import asynccontextmanager
from urllib.parse import quote

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from core.config import settings
from core.database import SessionLocal, create_tables
from core.exceptions import AppError, AuthenticationRequired
from routers import auth_router, projects_router, web_router
from services import AuthService
from core.ui import render


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """서버 시작 전 DB 테이블과 테스트 계정 준비"""
    create_tables()
    with SessionLocal() as db:
        AuthService(db).ensure_test_account()
    # yield를 기준으로 시작 작업과 종료 작업 구분
    yield


# Uvicorn이 실행할 main 모듈의 app 객체 생성
app = FastAPI(title=settings.app_name, lifespan=lifespan)
# 로그인 세션 쿠키의 서명과 검증을 위한 미들웨어 설정
# SQLAlchemy의 DB 세션과 별개이며 쿠키 암호화는 미지원
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie="flowtask_session",
    same_site="lax",
    https_only=settings.session_https_only,
    max_age=60 * 60 * 8,
)
# /static 경로에 CSS 등 정적 파일 제공
app.mount("/static", StaticFiles(directory="static"), name="static")

# 기능별 라우터 등록
app.include_router(web_router)
app.include_router(auth_router)
app.include_router(projects_router)


# 발생한 예외를 공통 HTTP 응답으로 변환하는 전역 예외 처리
@app.exception_handler(AuthenticationRequired)
async def authentication_required_handler(
    request: Request, _exc: AuthenticationRequired
):
    """비로그인 요청의 로그인 화면 이동 및 로그인 후 복귀 경로 지정"""
    # 로그인 후 조회 요청은 원래 경로로, 변경 요청은 프로젝트 목록으로 이동
    next_path = (
        request.url.path if request.method in {"GET", "HEAD"} else "/app/projects"
    )
    # next 경로 인코딩 및 303 리다이렉트로 로그인 화면 GET 요청 유도
    next_url = quote(next_path, safe="/")
    return RedirectResponse(f"/login?next={next_url}", status_code=303)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    """입력값·소유권·상태 변경 규칙 위반의 공통 오류 화면 처리"""
    return render(
        request,
        "error.html",
        status_code=exc.status_code,
        title="요청을 처리할 수 없습니다",
        message=exc.message,
    )


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException):
    """404 등 HTTP 오류의 공통 HTML 화면 처리"""
    message = (
        "요청한 페이지를 찾을 수 없습니다."
        if exc.status_code == 404
        else str(exc.detail)
    )
    return render(
        request,
        "error.html",
        status_code=exc.status_code,
        title=f"오류 {exc.status_code}",
        message=message,
    )
