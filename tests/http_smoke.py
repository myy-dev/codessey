"""실행 중인 로컬 Uvicorn 서버의 전체 HTTP 흐름 검증

앱 실행 후 테스트 명령::

    uv run python tests/http_smoke.py
"""

from html import escape
from html.parser import HTMLParser
from http.client import HTTPConnection
import json
import re
from urllib.parse import urlencode, urlsplit
from uuid import uuid4


HOST = "127.0.0.1"
PORT = 8000


class MemoCardParser(HTMLParser):
    """메모 카드의 상세 경로와 제목 추출"""

    def __init__(self) -> None:
        super().__init__()
        self.cards: list[tuple[str, str]] = []
        self.href: str | None = None
        self.in_title = False
        self.title = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "a" and "memo-card" in (attributes.get("class") or "").split():
            self.href = attributes.get("href")
            self.title = ""
        elif tag == "h2" and self.href is not None:
            self.in_title = True

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "h2":
            self.in_title = False
        elif tag == "a" and self.href is not None:
            self.cards.append((urlsplit(self.href).path, self.title))
            self.href = None


def assert_search_result(html: str, detail_path: str, title: str) -> None:
    """검색 결과 카드 안의 상세 링크와 제목 일치 여부 검증"""
    parser = MemoCardParser()
    parser.feed(html)
    assert parser.cards == [(detail_path, title)], parser.cards


def request(
    connection: HTTPConnection,
    method: str,
    path: str,
    data: dict[str, str] | bytes | None = None,
    *,
    content_type: str = "application/x-www-form-urlencoded",
) -> tuple[int, dict[str, str], str]:
    headers: dict[str, str] = {}
    body = None
    if data is not None:
        body = data if isinstance(data, bytes) else urlencode(data)
        headers["Content-Type"] = content_type

    connection.request(method, path, body=body, headers=headers)
    response = connection.getresponse()
    text = response.read().decode("utf-8")
    normalized_headers = {key.lower(): value for key, value in response.getheaders()}
    return response.status, normalized_headers, text


def main() -> None:
    connection = HTTPConnection(HOST, PORT, timeout=5)
    run_id = uuid4().hex
    title = f"통합 테스트 메모 {run_id}"
    updated_title = f"수정된 통합 메모 {run_id}"

    status, _, home = request(connection, "GET", "/")
    assert status == 200
    assert "메모 목록 보기" in home and "새 메모 작성" in home

    status, _, schema = request(connection, "GET", "/openapi.json")
    assert status == 200
    paths = json.loads(schema)["paths"]
    for path in ("/memos", "/memos/{memo_id}/edit", "/memos/{memo_id}/delete"):
        responses = paths[path]["post"]["responses"]
        assert "303" in responses and "200" not in responses, (path, responses)
        if path != "/memos":
            assert "text/html" in responses["404"]["content"], path
        if path.endswith("/delete"):
            assert "422" not in responses, path
        else:
            assert set(responses["422"]["content"]) == {"text/html", "application/json"}, path
    for path in ("/memos/{memo_id}", "/memos/{memo_id}/edit"):
        responses = paths[path]["get"]["responses"]
        assert "text/html" in responses["404"]["content"], path
        assert "422" not in responses, path

    stylesheet_link = re.search(r'<link rel="stylesheet" href="([^"]+)"', home)
    assert stylesheet_link is not None
    stylesheet_url = urlsplit(stylesheet_link[1])
    assert stylesheet_url.query.startswith("v=") and stylesheet_url.query[2:].isdigit()
    status, _, stylesheet = request(
        connection, "GET", f"{stylesheet_url.path}?{stylesheet_url.query}"
    )
    assert status == 200 and "--green" in stylesheet

    status, _, listing = request(connection, "GET", "/memos")
    assert status == 200 and "메모 목록" in listing

    status, _, form = request(connection, "GET", "/memos/new")
    assert status == 200
    assert 'name="title"' in form and 'name="content"' in form
    assert 'maxlength="1000"' in form and "1,000자 이하로 입력해 주세요." in form

    for path in ("/not-a-route", "/memos/abc", "/memos/abc/edit"):
        status, headers, missing = request(connection, "GET", path)
        assert status == 404, (path, status)
        assert "text/html" in headers["content-type"], path
        assert "404 NOT FOUND" in missing, path
        message = (
            "요청한 페이지를 찾을 수 없습니다."
            if path == "/not-a-route"
            else "해당 메모를 찾을 수 없습니다."
        )
        assert message in missing, path

    for memo_id in (str(-(2**63) - 1), str(2**63), "abc", "9" * 4301):
        for method, suffix, data in (
            ("GET", "", None),
            ("GET", "/edit", None),
            ("POST", "/edit", {}),
            ("POST", "/delete", None),
        ):
            path = f"/memos/{memo_id}{suffix}"
            status, headers, missing = request(connection, method, path, data)
            assert status == 404, (method, suffix, memo_id[:20], status)
            assert "text/html" in headers["content-type"]
            assert "404 NOT FOUND" in missing
            assert "해당 메모를 찾을 수 없습니다." in missing

    status, headers, _ = request(connection, "PUT", "/memos/new")
    assert status == 405 and "allow" in headers

    status, headers, _ = request(
        connection,
        "POST",
        "/memos",
        {"title": title, "content": "DB 저장 확인"},
    )
    assert status == 303
    detail_path = urlsplit(headers["location"]).path
    memo_id = int(detail_path.rsplit("/", 1)[-1])

    try:
        status, _, detail = request(connection, "GET", detail_path)
        assert status == 200
        assert title in detail and "DB 저장 확인" in detail

        # 리다이렉트된 GET 화면 새로고침 시 이전 POST 요청의 중복 실행 방지 확인
        status, _, refreshed_detail = request(connection, "GET", detail_path)
        assert status == 200 and refreshed_detail == detail

        status, headers, _ = request(
            connection,
            "POST",
            f"/memos/{memo_id}/edit",
            {"title": updated_title, "content": "수정도 DB에 반영"},
        )
        assert status == 303
        assert urlsplit(headers["location"]).path == f"/memos/{memo_id}"

        status, _, updated = request(connection, "GET", f"/memos/{memo_id}")
        assert status == 200
        assert updated_title in updated and "수정도 DB에 반영" in updated

        status, _, refreshed_update = request(connection, "GET", f"/memos/{memo_id}")
        assert status == 200 and refreshed_update == updated

        status, _, searched = request(
            connection,
            "GET",
            f"/memos?{urlencode({'q': updated_title})}",
        )
        assert status == 200
        assert_search_result(searched, detail_path, updated_title)

        status, _, no_results = request(
            connection,
            "GET",
            f"/memos?{urlencode({'q': f'no-match-{run_id}'})}",
        )
        assert status == 200 and "검색 결과가 없습니다" in no_results

        status, _, listing_before_invalid = request(connection, "GET", "/memos")
        assert status == 200
        invalid_forms = [
            {"title": "", "content": ""},
            {"title": "", "content": "유지할 내용 <&>"},
            {"title": "유지할 제목", "content": ""},
            {"title": "   ", "content": "공백 제목 검증"},
            {},
            {"title": "제목만 보낸 경우"},
            {"content": "내용만 보낸 경우"},
            {"title": "내용 길이 검증", "content": "가" * 1001},
        ]
        for path in ("/memos", f"/memos/{memo_id}/edit"):
            for data in invalid_forms:
                status, headers, invalid = request(connection, "POST", path, data)
                assert status == 422, (path, data, status)
                assert "text/html" in headers["content-type"], (path, data)
                if not data.get("title", "").strip():
                    assert "제목을 입력해 주세요" in invalid
                if not data.get("content", "").strip():
                    assert "내용을 입력해 주세요" in invalid
                elif len(data["content"].strip()) > 1000:
                    assert "내용은 1,000자 이하로 입력해 주세요." in invalid
                for value in data.values():
                    assert escape(value.strip()) in invalid

            # 문자열 필드에 파일을 전송한 요청의 JSON 검증 오류 확인
            boundary = f"smoke-{run_id}"
            for file_field in ("title", "content"):
                parts = []
                for field in ("title", "content"):
                    filename = '; filename="input.txt"' if field == file_field else ""
                    parts.append(
                        f'--{boundary}\r\n'
                        f'Content-Disposition: form-data; name="{field}"{filename}\r\n'
                        '\r\n검증용 값\r\n'
                    )
                body = ("".join(parts) + f"--{boundary}--\r\n").encode("utf-8")
                status, headers, invalid = request(
                    connection, "POST", path, body,
                    content_type=f"multipart/form-data; boundary={boundary}",
                )
                assert status == 422, (path, file_field, status)
                assert "application/json" in headers["content-type"], (path, file_field)
                errors = json.loads(invalid)["detail"]
                assert any(
                    error["loc"] == ["body", file_field] and error["type"] == "string_type"
                    for error in errors
                ), (path, file_field, errors)

        status, _, listing_after_invalid = request(connection, "GET", "/memos")
        assert status == 200 and listing_after_invalid == listing_before_invalid
        status, _, detail_after_invalid = request(connection, "GET", detail_path)
        assert status == 200 and detail_after_invalid == updated

    finally:
        status, headers, _ = request(connection, "POST", f"/memos/{memo_id}/delete")
        delete_redirect_path = urlsplit(headers["location"]).path
        assert status == 303 and delete_redirect_path == "/memos"

    status, _, list_after_delete = request(connection, "GET", delete_redirect_path)
    assert status == 200 and updated_title not in list_after_delete
    status, _, refreshed_delete = request(connection, "GET", delete_redirect_path)
    assert status == 200 and refreshed_delete == list_after_delete

    status, _, deleted = request(connection, "GET", f"/memos/{memo_id}")
    assert status == 404 and "찾을 수 없습니다" in deleted

    status, _, missing_form = request(connection, "GET", f"/memos/{memo_id}/edit")
    assert status == 404 and "찾을 수 없습니다" in missing_form

    status, _, missing_edit = request(
        connection,
        "POST",
        f"/memos/{memo_id}/edit",
        {"title": "없는 메모", "content": "수정할 수 없음"},
    )
    assert status == 404 and "찾을 수 없습니다" in missing_edit

    status, headers, missing_edit = request(
        connection, "POST", f"/memos/{memo_id}/edit", {}
    )
    assert status == 404 and "text/html" in headers["content-type"]
    assert "404 NOT FOUND" in missing_edit and 'name="title"' not in missing_edit

    status, _, missing_delete = request(connection, "POST", f"/memos/{memo_id}/delete")
    assert status == 404 and "찾을 수 없습니다" in missing_delete
    connection.close()
    print("HTTP smoke test: PASS")


if __name__ == "__main__":
    main()
