from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.templating import templates


router = APIRouter()


# 홈 화면 표시
@router.get("/", response_class=HTMLResponse, name="home", summary="홈 화면 조회")
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="home.html",
    )
