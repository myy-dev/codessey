"""End-to-end HTTP smoke test for a running local Uvicorn server.

Run the app first, then execute::

    python tests/http_smoke.py
"""

from html import escape
from http.client import HTTPConnection
import re
from urllib.parse import urlencode, urlsplit
from uuid import uuid4


HOST = "127.0.0.1"
PORT = 8000


def request(
    connection: HTTPConnection,
    method: str,
    path: str,
    data: dict[str, str] | None = None,
) -> tuple[int, dict[str, str], str]:
    headers: dict[str, str] = {}
    body = None
    if data is not None:
        body = urlencode(data)
        headers["Content-Type"] = "application/x-www-form-urlencoded"

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

        # Refreshing the redirected GET must not repeat the preceding POST.
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
        assert status == 200 and updated_title in searched

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
