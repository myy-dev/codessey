"""홈 화면과 서버 상태 확인을 위한 공개 경로 모음"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from auth.dependencies import OptionalUser
from core.ui import render


# main.py에서 앱에 등록할 경로 묶음 생성
router = APIRouter()


# GET 요청과 함수 연결 및 url_for()에서 사용할 경로 이름 지정
@router.get("/", name="home")
def home(request: Request, user: OptionalUser):
    """로그인 상태를 반영한 홈 화면 렌더링"""
    # Request로 요청 정보 수신 및 OptionalUser 의존성으로 사용자 객체 또는 None 주입
    return render(request, "home.html", user=user)


@router.get("/health", name="health")
def health() -> JSONResponse:
    """서버 응답 여부 확인을 위한 JSON 반환"""
    return JSONResponse({"status": "ok"})
