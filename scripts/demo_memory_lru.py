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
            ("CONFIG SET maxmemory 4", ["CONFIG", "SET", "maxmemory", "4"]),
            ("SET a 1", ["SET", "a", "1"]),
            ("SET b 2", ["SET", "b", "2"]),
            ("GET a", ["GET", "a"]),
            ("CONFIG SET maxmemory 2", ["CONFIG", "SET", "maxmemory", "2"]),
            ("INFO memory", ["INFO", "memory"]),
            ("SET huge abcde", ["SET", "huge", "abcde"]),
            ("CONFIG SET maxmemory 0", ["CONFIG", "SET", "maxmemory", "0"]),
        ]
    )


if __name__ == "__main__":
    main()
