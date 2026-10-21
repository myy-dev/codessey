from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.memo_repository import MemoRepository
from app.schemas.memo import MemoFormData
from app.services.memo_service import MemoService, MemoValidationError
from app.templating import templates


router = APIRouter(prefix="/memos", tags=["memos"])


def get_memo_service(db: Session = Depends(get_db)) -> MemoService:
    return MemoService(MemoRepository(db))


@router.get("", response_class=HTMLResponse, name="memo_list")
def memo_list(
    request: Request,
    q: str = "",
    service: MemoService = Depends(get_memo_service),
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="memos/list.html",
        context={"memos": service.list_memos(q), "query": q},
    )


# "new"의 메모 ID 해석 방지를 위한 /{memo_id} 이전 고정 경로 등록
@router.get("/new", response_class=HTMLResponse, name="memo_create_form")
def memo_create_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="memos/create.html",
        context={"form": MemoFormData(title="", content=""), "errors": {}},
    )


@router.post("", name="memo_create")
def memo_create(
    request: Request,
    title: Annotated[str, Form()] = "",
    content: Annotated[str, Form()] = "",
    service: MemoService = Depends(get_memo_service),
) -> Response:
    try:
        memo = service.create_memo(title, content)
    except MemoValidationError as exc:
        return templates.TemplateResponse(
            request=request,
            name="memos/create.html",
            context={"form": exc.form, "errors": exc.errors},
            status_code=422,
        )

    return RedirectResponse(
        url=request.url_for("memo_detail", memo_id=memo.id),
        status_code=303,
    )


@router.get("/{memo_id}", response_class=HTMLResponse, name="memo_detail")
def memo_detail(
    request: Request,
    memo_id: int,
    service: MemoService = Depends(get_memo_service),
) -> HTMLResponse:
    memo = service.get_memo(memo_id)

    return templates.TemplateResponse(
        request=request,
        name="memos/detail.html",
        context={"memo": memo},
    )


@router.get("/{memo_id}/edit", response_class=HTMLResponse, name="memo_edit_form")
def memo_edit_form(
    request: Request,
    memo_id: int,
    service: MemoService = Depends(get_memo_service),
) -> HTMLResponse:
    memo = service.get_memo(memo_id)

    return templates.TemplateResponse(
        request=request,
        name="memos/edit.html",
        context={
            "memo_id": memo.id,
            "form": MemoFormData(title=memo.title, content=memo.content),
            "errors": {},
        },
    )


@router.post("/{memo_id}/edit", name="memo_update")
def memo_update(
    request: Request,
    memo_id: int,
    title: Annotated[str, Form()] = "",
    content: Annotated[str, Form()] = "",
    service: MemoService = Depends(get_memo_service),
) -> Response:
    try:
        memo = service.update_memo(memo_id, title, content)
    except MemoValidationError as exc:
        return templates.TemplateResponse(
            request=request,
            name="memos/edit.html",
            context={"memo_id": memo_id, "form": exc.form, "errors": exc.errors},
            status_code=422,
        )

    return RedirectResponse(
        url=request.url_for("memo_detail", memo_id=memo.id),
        status_code=303,
    )


@router.post("/{memo_id}/delete", name="memo_delete")
def memo_delete(
    request: Request,
    memo_id: int,
    service: MemoService = Depends(get_memo_service),
) -> Response:
    service.delete_memo(memo_id)

    return RedirectResponse(url=request.url_for("memo_list"), status_code=303)
