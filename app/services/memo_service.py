from app.models.memo import Memo
from app.repositories.memo_repository import MemoRepository
from app.schemas.memo import MemoDTO, MemoFormData


class MemoNotFoundError(LookupError):
    """요청한 메모 부재 시 발생하는 예외"""


class MemoValidationError(ValueError):
    def __init__(self, errors: dict[str, str], form: MemoFormData) -> None:
        """폼 재표시를 위한 필드별 오류와 입력값 보관"""
        super().__init__("메모 입력값을 확인해 주세요.")
        self.errors = errors
        self.form = form


class MemoService:
    """메모의 비즈니스 규칙 및 작업 흐름 처리"""

    def __init__(self, repository: MemoRepository) -> None:
        """메모 데이터 조회와 변경에 사용할 저장소 보관"""
        self.repository = repository

    def list_memos(self, search: str = "") -> list[MemoDTO]:
        """검색어 앞뒤 공백 제거 후 메모 목록 조회 및 DTO 목록 반환"""
        normalized_search = search.strip()
        memos = self.repository.list_all(normalized_search or None)
        return [self._to_dto(memo) for memo in memos]

    def get_memo(self, memo_id: int) -> MemoDTO:
        """메모 존재 여부 확인 후 상세 정보 DTO 반환"""
        return self._to_dto(self._require_memo(memo_id))

    def create_memo(self, title: str, content: str) -> MemoDTO:
        """입력값 검증 후 메모 등록 및 결과 DTO 반환"""
        form = self._validate(title, content)
        memo = self.repository.create(title=form.title, content=form.content)
        return self._to_dto(memo)

    def update_memo(self, memo_id: int, title: str, content: str) -> MemoDTO:
        """메모 존재 여부 확인 및 입력값 검증 후 수정 결과 DTO 반환"""
        memo = self._require_memo(memo_id)
        form = self._validate(title, content)
        updated = self.repository.update(memo, title=form.title, content=form.content)
        return self._to_dto(updated)

    def delete_memo(self, memo_id: int) -> None:
        """메모 존재 여부 확인 후 삭제"""
        memo = self._require_memo(memo_id)
        self.repository.delete(memo)

    def _require_memo(self, memo_id: int) -> Memo:
        """메모 모델 조회 및 반환, 미존재 시 MemoNotFoundError 발생"""
        memo = self.repository.get_by_id(memo_id)
        if memo is None:
            raise MemoNotFoundError(f"메모 {memo_id}을(를) 찾을 수 없습니다.")
        return memo

    @staticmethod
    def _validate(title: str, content: str) -> MemoFormData:
        """앞뒤 공백 제거 후 필수 입력과 글자 수 검증, 실패 시 MemoValidationError 발생"""
        form = MemoFormData(title=title.strip(), content=content.strip())
        errors: dict[str, str] = {}

        if not form.title:
            errors["title"] = "제목을 입력해 주세요."
        elif len(form.title) > 120:
            errors["title"] = "제목은 120자 이하로 입력해 주세요."

        if not form.content:
            errors["content"] = "내용을 입력해 주세요."
        elif len(form.content) > 1000:
            errors["content"] = "내용은 1,000자 이하로 입력해 주세요."

        if errors:
            raise MemoValidationError(errors, form)
        return form

    @staticmethod
    def _to_dto(memo: Memo) -> MemoDTO:
        """ORM 모델의 메모 정보를 전달용 DTO로 변환"""
        return MemoDTO(
            id=memo.id,
            title=memo.title,
            content=memo.content,
            created_at=memo.created_at,
            updated_at=memo.updated_at,
        )
