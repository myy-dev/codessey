from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.templating import templates


router = APIRouter()


@router.get("/", response_class=HTMLResponse, name="home")
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={},
    )
