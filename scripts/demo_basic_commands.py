import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mini_redis.store import MiniRedisStore


def run_examples(commands: list[tuple[str, list[str]]]) -> None:
    store = MiniRedisStore()

    for command, parts in commands:
        print(f"mini-redis> {command}")
        result = store.execute(parts)
        if result is not None:
            print(result)
        print()


def main() -> None:
    run_examples(
        [
            ('SET greeting "hello world"', ["SET", "greeting", "hello world"]),
            ("GET greeting", ["GET", "greeting"]),
            ("EXISTS greeting", ["EXISTS", "greeting"]),
            ("DBSIZE", ["DBSIZE"]),
            ("KEYS", ["KEYS"]),
            ("DEL greeting", ["DEL", "greeting"]),
            ("GET greeting", ["GET", "greeting"]),
            ("KEYS", ["KEYS"]),
        ]
    )


if __name__ == "__main__":
    main()
