"""Mini Redis CLI 입력 한 줄의 명령 토큰 변환"""

import shlex


class ParseError(Exception):
    """CLI 명령줄 토큰화 실패용 ParseError"""


def parse_command(line):
    """공백 포함 인용 값을 보존하는 명령줄 분할"""

    stripped = line.strip()

    try:
        return shlex.split(stripped)
    except ValueError as exc:
        raise ParseError("명령행 구문 오류") from exc
