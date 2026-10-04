"""Mini Redis CLI 진입점"""

from . import response
from .parser import ParseError, parse_command
from .store import MiniRedisStore


def main():
    """EOF, exit, quit 입력까지의 대화형 Mini Redis REPL 실행"""

    store = MiniRedisStore()

    while True:
        try:
            line = input("mini-redis> ")
        except EOFError:
            break

        if line.strip().lower() in ("exit", "quit"):
            break

        try:
            parts = parse_command(line)
        except ParseError as exc:
            print(response.error(f"ERR {exc}"))
            continue

        result = store.execute(parts)
        if result is not None:
            print(result)


if __name__ == "__main__":
    main()
