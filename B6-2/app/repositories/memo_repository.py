from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.memo import Memo


class MemoRepository:
    """메모 모델의 데이터베이스 접근 처리"""

    def __init__(self, db: Session) -> None:
        """메모 조회와 변경에 사용할 DB 세션 보관"""
        self.db = db

    def list_all(self, search: str | None = None) -> list[Memo]:
        """제목 검색 조건을 적용한 메모 목록 조회, 생성 시각과 ID 내림차순 정렬"""
        statement = select(Memo).order_by(Memo.created_at.desc(), Memo.id.desc())
        if search:
            statement = statement.where(Memo.title.contains(search, autoescape=True))
        return self.db.scalars(statement).all()

    def get_by_id(self, memo_id: int) -> Memo | None:
        """ID로 메모 조회, 정수 범위 초과 또는 미존재 시 None 반환"""
        # SQLite INTEGER의 부호 있는 64비트 정수 범위 확인
        if not -(2**63) <= memo_id < 2**63:
            return None
        return self.db.get(Memo, memo_id)

    def create(self, *, title: str, content: str) -> Memo:
        """메모 모델 생성 및 DB 저장 확정 후 반환"""
        memo = Memo(title=title, content=content)
        self.db.add(memo)
        self.db.commit()
        return memo

    def update(self, memo: Memo, *, title: str, content: str) -> Memo:
        """기존 메모의 제목과 내용 변경 및 DB 저장 확정 후 반환"""
        memo.title = title
        memo.content = content
        self.db.commit()
        return memo

    def delete(self, memo: Memo) -> None:
        """메모 삭제 및 DB 변경 확정"""
        self.db.delete(memo)
        self.db.commit()
