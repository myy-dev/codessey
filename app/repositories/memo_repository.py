from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.memo import Memo


class MemoRepository:
    """All database access for the Memo model."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(self, search: str | None = None) -> list[Memo]:
        statement = select(Memo).order_by(Memo.created_at.desc(), Memo.id.desc())
        if search:
            statement = statement.where(Memo.title.contains(search, autoescape=True))
        return self.db.scalars(statement).all()

    def get_by_id(self, memo_id: int) -> Memo | None:
        # SQLite INTEGER values must fit in a signed 64-bit integer.
        if not -(2**63) <= memo_id < 2**63:
            return None
        return self.db.get(Memo, memo_id)

    def create(self, *, title: str, content: str) -> Memo:
        memo = Memo(title=title, content=content)
        self.db.add(memo)
        self.db.commit()
        return memo

    def update(self, memo: Memo, *, title: str, content: str) -> Memo:
        memo.title = title
        memo.content = content
        self.db.commit()
        return memo

    def delete(self, memo: Memo) -> None:
        self.db.delete(memo)
        self.db.commit()
