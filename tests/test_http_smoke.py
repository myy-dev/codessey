from html import escape
import unittest

from tests.http_smoke import assert_search_result


class SearchResultAssertionTestCase(unittest.TestCase):
    def test_matching_card_link_and_title_are_accepted(self) -> None:
        title = "검색 <메모> & 확인"
        html = (
            '<a href="http://localhost:8000/memos/42" class="memo-card">'
            f'<h2>{escape(title)}</h2><p>본문</p></a>'
        )
        assert_search_result(html, "/memos/42", title)

    def test_search_term_without_result_cards_is_rejected(self) -> None:
        html = (
            '<input name="q" value="검색 제목">'
            '<section><h2>검색 결과가 없습니다.</h2>'
            '<p>검색 제목에 포함된 메모를 찾지 못했습니다.</p></section>'
        )
        with self.assertRaises(AssertionError):
            assert_search_result(html, "/memos/42", "검색 제목")

    def test_card_with_wrong_detail_link_is_rejected(self) -> None:
        html = '<a class="memo-card" href="/memos/99"><h2>검색 제목</h2></a>'
        with self.assertRaises(AssertionError):
            assert_search_result(html, "/memos/42", "검색 제목")

    def test_card_with_wrong_title_is_rejected(self) -> None:
        html = '<a class="memo-card" href="/memos/42"><h2>다른 제목</h2></a>'
        with self.assertRaises(AssertionError):
            assert_search_result(html, "/memos/42", "검색 제목")
