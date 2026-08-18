"""Command-line entry point for Mini Redis."""

from parser import ParseError, parse_command
from store import MiniRedisStore
import response


def main():
    """Run the interactive Mini Redis REPL until EOF, exit, or quit."""

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
