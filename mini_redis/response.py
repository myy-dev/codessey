import json


def _quoted(value):
    """사람이 읽을 수 있는 CLI 응답용 값 인용 및 escape 처리"""

    return json.dumps(str(value), ensure_ascii=False)


def simple_string(value):
    """값을 그대로 사용하는 단순 문자열 응답 생성"""

    return value


def nil():
    """존재하지 않는 값을 나타내는 nil 응답 생성"""

    return "(nil)"


def integer(value):
    """정숫값을 포함하는 Redis 형식 응답 생성"""

    return f"(integer) {value}"


def error(message):
    """오류 메시지를 포함하는 Redis 형식 응답 생성"""

    return f"(error) {message}"


def bulk_string(value):
    """인용 및 이스케이프 처리된 벌크 문자열 응답 생성"""

    return _quoted(value)


def array(values):
    """값 목록의 번호를 포함하는 Redis 형식 배열 응답 생성"""

    if len(values) == 0:
        return "(empty array)"

    lines = []
    for index, value in enumerate(values, start=1):
        lines.append(f"{index}) {_quoted(value)}")
    return "\n".join(lines)


def subscription(channel, subscription_count):
    """Redis 형식 SUBSCRIBE 확인 배열 생성"""

    return "\n".join(
        [
            f"1) {_quoted('subscribe')}",
            f"2) {_quoted(channel)}",
            f"3) {integer(subscription_count)}",
        ]
    )


def memory_info(used_memory, maxmemory, evicted_keys):
    """메모리 사용량, 제한, 제거 통계 응답 생성"""

    return "\n".join(
        [
            f"used_memory:{used_memory}",
            f"maxmemory:{maxmemory}",
            f"evicted_keys:{evicted_keys}",
        ]
    )
