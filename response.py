import json


def _quoted(value):
    """Quote and escape a value for the human-readable CLI response."""

    return json.dumps(str(value), ensure_ascii=False)


def simple_string(value):
    return value


def nil():
    return "(nil)"


def integer(value):
    return f"(integer) {value}"


def error(message):
    return f"(error) {message}"


def bulk_string(value):
    return _quoted(value)


def array(values):
    if len(values) == 0:
        return "(empty array)"

    lines = []
    for index, value in enumerate(values, start=1):
        lines.append(f"{index}) {_quoted(value)}")
    return "\n".join(lines)


def subscription(channel, subscription_count):
    """Return a Redis-style SUBSCRIBE confirmation array."""

    return "\n".join(
        [
            f"1) {_quoted('subscribe')}",
            f"2) {_quoted(channel)}",
            f"3) {integer(subscription_count)}",
        ]
    )


def memory_info(used_memory, maxmemory, evicted_keys):
    return "\n".join(
        [
            f"used_memory:{used_memory}",
            f"maxmemory:{maxmemory}",
            f"evicted_keys:{evicted_keys}",
        ]
    )
