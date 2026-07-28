"""End-to-end HTTP smoke test for a running local Uvicorn server.

Run the app first, then execute::

    python tests/http_smoke.py
"""

from http.client import HTTPConnection
from urllib.parse import urlencode, urlsplit


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

    status, _, home = request(connection, "GET", "/")
    assert status == 200
    assert "메모 목록 보기" in home and "새 메모 작성" in home

    status, _, stylesheet = request(connection, "GET", "/static/styles.css")
    assert status == 200 and "--green" in stylesheet

    status, _, listing = request(connection, "GET", "/memos")
    assert status == 200 and "메모 목록" in listing

    status, _, form = request(connection, "GET", "/memos/new")
    assert status == 200
    assert 'name="title"' in form and 'name="content"' in form

    status, headers, _ = request(
        connection,
        "POST",
        "/memos",
        {"title": "통합 테스트 메모", "content": "DB 저장 확인"},
    )
    assert status == 303
    detail_path = urlsplit(headers["location"]).path
    memo_id = int(detail_path.rsplit("/", 1)[-1])

    try:
        status, _, detail = request(connection, "GET", detail_path)
        assert status == 200
        assert "통합 테스트 메모" in detail and "DB 저장 확인" in detail

        # Refreshing the redirected GET must not repeat the preceding POST.
        status, _, refreshed_detail = request(connection, "GET", detail_path)
        assert status == 200 and refreshed_detail == detail

        status, headers, _ = request(
            connection,
            "POST",
            f"/memos/{memo_id}/edit",
            {"title": "수정된 통합 메모", "content": "수정도 DB에 반영"},
        )
        assert status == 303
        assert urlsplit(headers["location"]).path == f"/memos/{memo_id}"

        status, _, updated = request(connection, "GET", f"/memos/{memo_id}")
        assert status == 200
        assert "수정된 통합 메모" in updated and "수정도 DB에 반영" in updated

        status, _, refreshed_update = request(connection, "GET", f"/memos/{memo_id}")
        assert status == 200 and refreshed_update == updated

        status, _, searched = request(
            connection,
            "GET",
            "/memos?q=%EC%88%98%EC%A0%95%EB%90%9C",
        )
        assert status == 200 and "수정된 통합 메모" in searched

        status, _, no_results = request(
            connection,
            "GET",
            "/memos?q=%EC%97%86%EB%8A%94%EA%B2%80%EC%83%89%EC%96%B4",
        )
        assert status == 200 and "검색 결과가 없습니다" in no_results

        status, _, invalid = request(
            connection,
            "POST",
            "/memos",
            {"title": "   ", "content": "다시 입력할 때 유지할 내용"},
        )
        assert status == 422
        assert "제목을 입력해 주세요" in invalid
        assert "다시 입력할 때 유지할 내용" in invalid

        status, _, missing = request(connection, "GET", "/memos/999999")
        assert status == 404 and "찾을 수 없습니다" in missing

        status, _, missing_edit = request(
            connection,
            "POST",
            "/memos/999999/edit",
            {"title": "없는 메모", "content": "수정할 수 없음"},
        )
        assert status == 404 and "찾을 수 없습니다" in missing_edit

        status, _, missing_delete = request(connection, "POST", "/memos/999999/delete")
        assert status == 404 and "찾을 수 없습니다" in missing_delete
    finally:
        status, headers, _ = request(connection, "POST", f"/memos/{memo_id}/delete")
        delete_redirect_path = urlsplit(headers["location"]).path
        assert status == 303 and delete_redirect_path == "/memos"

    status, _, list_after_delete = request(connection, "GET", delete_redirect_path)
    assert status == 200 and "수정된 통합 메모" not in list_after_delete
    status, _, refreshed_delete = request(connection, "GET", delete_redirect_path)
    assert status == 200 and refreshed_delete == list_after_delete

    status, _, deleted = request(connection, "GET", f"/memos/{memo_id}")
    assert status == 404 and "찾을 수 없습니다" in deleted
    connection.close()
    print("HTTP smoke test: PASS")


if __name__ == "__main__":
    main()
