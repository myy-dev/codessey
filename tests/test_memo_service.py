import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.memo import Memo
from app.repositories.memo_repository import MemoRepository
from app.services.memo_service import MemoNotFoundError, MemoService, MemoValidationError


class MemoServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine, expire_on_commit=False)
        self.service = MemoService(MemoRepository(self.session))

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def test_crud_flow(self) -> None:
        created = self.service.create_memo(" 첫 메모 ", " 테스트 내용 ")
        self.assertEqual(created.title, "첫 메모")
        self.assertEqual(created.content, "테스트 내용")
        self.assertEqual(len(self.service.list_memos()), 1)

        found = self.service.get_memo(created.id)
        self.assertEqual(found, created)

        updated = self.service.update_memo(created.id, "수정된 제목", "수정된 내용")
        self.assertEqual(updated.title, "수정된 제목")
        self.assertEqual(updated.content, "수정된 내용")

        self.service.delete_memo(created.id)
        self.assertEqual(self.service.list_memos(), [])
        with self.assertRaises(MemoNotFoundError):
            self.service.get_memo(created.id)

    def test_search_filters_by_title(self) -> None:
        self.service.create_memo("FastAPI 학습", "라우터를 학습한다.")
        self.service.create_memo("SQLAlchemy 학습", "ORM을 학습한다.")

        results = self.service.list_memos("FastAPI")
        self.assertEqual([memo.title for memo in results], ["FastAPI 학습"])

    def test_search_escapes_sql_wildcards(self) -> None:
        self.service.create_memo("100% 완료", "퍼센트 문자가 있는 제목")
        self.service.create_memo("일반 메모", "검색되면 안 된다.")

        results = self.service.list_memos("%")
        self.assertEqual([memo.title for memo in results], ["100% 완료"])

    def test_empty_values_are_rejected(self) -> None:
        with self.assertRaises(MemoValidationError) as context:
            self.service.create_memo("   ", "   ")

        self.assertEqual(
            context.exception.errors,
            {"title": "제목을 입력해 주세요.", "content": "내용을 입력해 주세요."},
        )
        self.assertEqual(self.session.query(Memo).count(), 0)

    def test_title_over_120_characters_is_rejected(self) -> None:
        with self.assertRaises(MemoValidationError) as context:
            self.service.create_memo("가" * 121, "내용")

        self.assertIn("title", context.exception.errors)


if __name__ == "__main__":
    unittest.main()
