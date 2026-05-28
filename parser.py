import shlex


class ParseError(Exception):
    pass


def parse_command(line):
    stripped = line.strip()
    if stripped == "":
        return []

    try:
        return shlex.split(stripped)
    except ValueError as exc:
        raise ParseError(str(exc))
