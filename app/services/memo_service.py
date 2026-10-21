from app.models.memo import Memo
from app.repositories.memo_repository import MemoRepository
from app.schemas.memo import MemoDTO, MemoFormData


class MemoNotFoundError(LookupError):
    """Raised when a requested memo does not exist."""


class MemoValidationError(ValueError):
    def __init__(self, errors: dict[str, str], form: MemoFormData) -> None:
        super().__init__("메모 입력값을 확인해 주세요.")
        self.errors = errors
        self.form = form


class MemoService:
    """Business rules and application flow for memos."""

    def __init__(self, repository: MemoRepository) -> None:
        self.repository = repository

    def list_memos(self, search: str = "") -> list[MemoDTO]:
        normalized_search = search.strip()
        memos = self.repository.list_all(normalized_search or None)
        return [self._to_dto(memo) for memo in memos]

    def get_memo(self, memo_id: int) -> MemoDTO:
        return self._to_dto(self._require_memo(memo_id))

    def create_memo(self, title: str, content: str) -> MemoDTO:
        form = self._validate(title, content)
        memo = self.repository.create(title=form.title, content=form.content)
        return self._to_dto(memo)

    def update_memo(self, memo_id: int, title: str, content: str) -> MemoDTO:
        memo = self._require_memo(memo_id)
        form = self._validate(title, content)
        updated = self.repository.update(memo, title=form.title, content=form.content)
        return self._to_dto(updated)

    def delete_memo(self, memo_id: int) -> None:
        memo = self._require_memo(memo_id)
        self.repository.delete(memo)

    def _require_memo(self, memo_id: int) -> Memo:
        memo = self.repository.get_by_id(memo_id)
        if memo is None:
            raise MemoNotFoundError(f"메모 {memo_id}을(를) 찾을 수 없습니다.")
        return memo

    @staticmethod
    def _validate(title: str, content: str) -> MemoFormData:
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
        return MemoDTO(
            id=memo.id,
            title=memo.title,
            content=memo.content,
            created_at=memo.created_at,
            updated_at=memo.updated_at,
        )
