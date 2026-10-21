from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request, Response
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException

from app.database import create_db_and_tables
from app.routers import home, memos
from app.services.memo_service import MemoNotFoundError
from app.templating import STATIC_DIR, templates


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    create_db_and_tables()
    yield


app = FastAPI(title="나의 메모 앱", lifespan=lifespan)


def not_found_response(request: Request, exc: Exception) -> HTMLResponse:
    message = (
        "해당 메모를 찾을 수 없습니다."
        if isinstance(exc, (MemoNotFoundError, RequestValidationError))
        else "요청한 페이지를 찾을 수 없습니다."
    )
    return templates.TemplateResponse(
        request=request,
        name="memos/not_found.html",
        context={"message": message},
        status_code=404,
        headers=exc.headers if isinstance(exc, HTTPException) else None,
    )


app.add_exception_handler(MemoNotFoundError, not_found_response)


@app.exception_handler(HTTPException)
async def http_error_response(request: Request, exc: HTTPException) -> Response:
    if exc.status_code == 404:
        return not_found_response(request, exc)
    return await http_exception_handler(request, exc)


@app.exception_handler(RequestValidationError)
async def validation_error_response(request: Request, exc: RequestValidationError) -> Response:
    if any(error["loc"] == ("path", "memo_id") for error in exc.errors()):
        return not_found_response(request, exc)
    return await request_validation_exception_handler(request, exc)


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(home.router)
app.include_router(memos.router)
