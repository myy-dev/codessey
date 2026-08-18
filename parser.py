"""Parse one CLI input line into Mini Redis command tokens."""

import shlex


class ParseError(Exception):
    """Raised when a CLI command line cannot be tokenized."""


def parse_command(line):
    """Split a command line while preserving quoted values with spaces."""

    stripped = line.strip()
    if stripped == "":
        return []

    try:
        return shlex.split(stripped)
    except ValueError as exc:
        raise ParseError(str(exc))
