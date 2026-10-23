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

MEMO_RESPONSES = {
    404: {
        "description": "잘못된 메모 번호이거나 메모가 없을 때 표시하는 HTML 오류 화면",
        "content": {"text/html": {"schema": {"type": "string"}}},
    },
    # 메모 ID 검증 실패를 처리하는 404 대신 자동 422 응답이 표기되는 현상 방지
    "default": {"description": "기타 HTTP 오류"},
}
FORM_ERROR_RESPONSE = {
    "description": "입력값 검증 실패 시 HTML 폼, 요청 형식 검증 실패 시 JSON 오류",
    "content": {
        "text/html": {"schema": {"type": "string"}},
        "application/json": {
            "schema": {
                "type": "object",
                "properties": {"detail": {"type": "array", "items": {"type": "object"}}},
                "required": ["detail"],
            },
        },
    },
}


def get_memo_service(db: Session = Depends(get_db)) -> MemoService:
    return MemoService(MemoRepository(db))


# 메모 목록 조회 및 제목 검색
@router.get(
    "",
    response_class=HTMLResponse,
    name="memo_list",
    summary="메모 목록 조회",
    description="검색어 q로 제목에 포함된 문자열 검색, 검색어가 없거나 공백이면 전체 목록을 HTML로 반환",
)
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


# 메모 작성 화면 표시 ("new"의 메모 ID 해석 방지를 위해 /{memo_id}보다 먼저 등록)
@router.get(
    "/new",
    response_class=HTMLResponse,
    name="memo_create_form",
    summary="메모 작성 화면 조회",
)
def memo_create_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="memos/create.html",
        context={"form": MemoFormData(title="", content=""), "errors": {}},
    )


# 메모 등록 및 상세 화면 이동, 입력 오류 시 작성 화면 재표시
@router.post(
    "",
    status_code=303,
    response_class=RedirectResponse,
    responses={422: FORM_ERROR_RESPONSE},
    name="memo_create",
    summary="메모 등록",
    description=(
        "제목과 내용의 앞뒤 공백 제거 후 필수 입력 및 제목 최대 120자, 내용 최대 1000자 검증\n\n"
        "성공 시 상세 화면으로 303 리다이렉트, 검증 실패 시 입력값과 오류를 포함한 작성 화면을 422로 반환"
    ),
)
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


# 메모 상세 조회
@router.get(
    "/{memo_id}",
    response_class=HTMLResponse,
    responses=MEMO_RESPONSES,
    name="memo_detail",
    summary="메모 상세 조회",
    description="메모 번호에 해당하는 상세 화면 반환, 잘못된 번호이거나 메모가 없으면 404 오류 화면 반환",
)
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


# 기존 메모를 채운 수정 화면 표시
@router.get(
    "/{memo_id}/edit",
    response_class=HTMLResponse,
    responses=MEMO_RESPONSES,
    name="memo_edit_form",
    summary="메모 수정 화면 조회",
    description="기존 제목과 내용을 채운 수정 화면 반환, 잘못된 번호이거나 메모가 없으면 404 오류 화면 반환",
)
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


# 메모 수정 및 상세 화면 이동, 입력 오류 시 수정 화면 재표시
@router.post(
    "/{memo_id}/edit",
    status_code=303,
    response_class=RedirectResponse,
    responses={**MEMO_RESPONSES, 422: FORM_ERROR_RESPONSE},
    name="memo_update",
    summary="메모 수정",
    description=(
        "메모 존재 여부 확인 후 앞뒤 공백 제거 및 필수 입력, 제목 최대 120자, 내용 최대 1000자 검증\n\n"
        "성공 시 상세 화면으로 303 리다이렉트, 검증 실패 시 입력값과 오류를 포함한 수정 화면을 422로 반환\n\n"
        "잘못된 메모 번호이거나 메모가 없으면 404 오류 화면 반환"
    ),
)
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


# 메모 삭제 및 목록 화면 이동
@router.post(
    "/{memo_id}/delete",
    status_code=303,
    response_class=RedirectResponse,
    responses=MEMO_RESPONSES,
    name="memo_delete",
    summary="메모 삭제",
    description="삭제 성공 시 목록 화면으로 303 리다이렉트, 잘못된 번호이거나 메모가 없으면 404 오류 화면 반환",
)
def memo_delete(
    request: Request,
    memo_id: int,
    service: MemoService = Depends(get_memo_service),
) -> Response:
    service.delete_memo(memo_id)

    return RedirectResponse(url=request.url_for("memo_list"), status_code=303)
