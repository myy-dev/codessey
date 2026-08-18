"""Memory/CPU/Deadlock 장애를 의도적으로 재현하는 실습 애플리케이션."""

from __future__ import annotations

import logging
import os
import resource
import signal
import socket
import sys
import threading
import time
from pathlib import Path

from agent_leak_app.config import Config, ConfigError


LOGGER = logging.getLogger("agent-leak-app")


def configure_logging(log_dir: Path) -> None:
    LOGGER.setLevel(logging.INFO)
    LOGGER.handlers.clear()
    formatter = logging.Formatter(
        fmt="[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    file_handler = logging.FileHandler(log_dir / "agent.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    LOGGER.addHandler(stream_handler)
    LOGGER.addHandler(file_handler)


class ServiceSocket:
    """고정 포트 바인딩 요구사항을 실제로 검증한다."""

    def __init__(self, port: int) -> None:
        self.port = port
        self.socket: socket.socket | None = None

    def __enter__(self) -> "ServiceSocket":
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", self.port))
        server.listen(1)
        self.socket = server
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self.socket is not None:
            self.socket.close()


def current_rss_mb() -> float:
    statm = Path("/proc/self/statm")
    if statm.exists():
        resident_pages = int(statm.read_text(encoding="utf-8").split()[1])
        return resident_pages * os.sysconf("SC_PAGE_SIZE") / (1024 * 1024)

    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == "darwin":
        return usage / (1024 * 1024)
    return usage / 1024


def run_memory_scenario(config: Config) -> int:
    LOGGER.info(
        "[MemoryGuard] START limit=%dMB chunk=%dMB interval=%.2fs",
        config.memory_limit_mb,
        config.leak_chunk_mb,
        config.leak_interval,
    )
    allocations: list[bytearray] = []
    started = time.monotonic()

    while time.monotonic() - started < config.run_seconds:
        chunk = bytearray(config.leak_chunk_mb * 1024 * 1024)
        for index in range(0, len(chunk), 4096):
            chunk[index] = 1
        allocations.append(chunk)
        rss = current_rss_mb()
        LOGGER.info(
            "[MemoryGuard] RSS=%.1fMB LIMIT=%dMB chunks=%d",
            rss,
            config.memory_limit_mb,
            len(allocations),
        )
        if rss >= config.memory_limit_mb:
            LOGGER.critical(
                "[MemoryGuard] Memory limit exceeded (%.1fMB >= %dMB)",
                rss,
                config.memory_limit_mb,
            )
            LOGGER.critical(
                "[MemoryGuard] Self-terminating process %d to prevent system instability.",
                os.getpid(),
            )
            LOGGER.critical(">>> [SYSTEM] SELF-TERMINATED (Memory Limit Exceeded) <<<")
            return 137
        time.sleep(config.leak_interval)

    LOGGER.info(
        "[MemoryGuard] COMPLETED without termination elapsed=%.2fs final_rss=%.1fMB",
        time.monotonic() - started,
        current_rss_mb(),
    )
    return 0


def run_cpu_scenario(config: Config) -> int:
    stop_event = threading.Event()
    watchdog_triggered = threading.Event()

    def handle_sigterm(signum: int, frame: object) -> None:
        del signum, frame
        watchdog_triggered.set()
        stop_event.set()

    previous_handler = signal.signal(signal.SIGTERM, handle_sigterm)

    def watchdog() -> None:
        last_wall = time.monotonic()
        last_cpu = time.process_time()
        while not stop_event.wait(config.watchdog_interval):
            now_wall = time.monotonic()
            now_cpu = time.process_time()
            cpu_percent = 100 * (now_cpu - last_cpu) / max(now_wall - last_wall, 0.001)
            LOGGER.info(
                "[Watchdog] CPU=%.1f%% LIMIT=%d%%",
                cpu_percent,
                config.cpu_max_occupy,
            )
            last_wall, last_cpu = now_wall, now_cpu
            if cpu_percent >= config.cpu_max_occupy:
                LOGGER.critical(
                    "[Watchdog] CPU threshold exceeded (%.1f%% >= %d%%)",
                    cpu_percent,
                    config.cpu_max_occupy,
                )
                LOGGER.critical(">>> [SYSTEM] WATCHDOG: INITIATING EMERGENCY ABORT (SIGTERM) <<<")
                os.kill(os.getpid(), signal.SIGTERM)
                return

    watcher = threading.Thread(target=watchdog, name="cpu-watchdog", daemon=True)
    watcher.start()
    LOGGER.info(
        "[Watchdog] START limit=%d%% target_load=%d%%",
        config.cpu_max_occupy,
        config.cpu_load_percent,
    )

    started = time.monotonic()
    cycle_seconds = 0.1
    busy_seconds = cycle_seconds * config.cpu_load_percent / 100
    try:
        while time.monotonic() - started < config.run_seconds and not stop_event.is_set():
            cycle_started = time.monotonic()
            while time.monotonic() - cycle_started < busy_seconds:
                _ = sum(index * index for index in range(250))
            remaining = cycle_seconds - (time.monotonic() - cycle_started)
            if remaining > 0:
                stop_event.wait(remaining)
    finally:
        stop_event.set()
        watcher.join(timeout=1)
        signal.signal(signal.SIGTERM, previous_handler)

    if watchdog_triggered.is_set():
        LOGGER.info("[Watchdog] process stopped by protection policy")
        return 143

    LOGGER.info(
        "[Watchdog] COMPLETED without termination elapsed=%.2fs",
        time.monotonic() - started,
    )
    return 0


def run_deadlock_scenario(config: Config) -> int:
    if not config.multi_thread_enable:
        LOGGER.info("[DeadlockLab] MULTI_THREAD_ENABLE=false; running locks sequentially")
        first_lock = threading.Lock()
        second_lock = threading.Lock()
        with first_lock:
            LOGGER.info("[Thread-A] acquired Resource-A")
            with second_lock:
                LOGGER.info("[Thread-A] acquired Resource-B; task completed")
        with second_lock:
            LOGGER.info("[Thread-B] acquired Resource-B")
            with first_lock:
                LOGGER.info("[Thread-B] acquired Resource-A; task completed")
        LOGGER.info("[DeadlockLab] COMPLETED without deadlock")
        return 0

    first_lock = threading.Lock()
    second_lock = threading.Lock()
    rendezvous = threading.Barrier(2)

    def worker(
        name: str,
        owned: threading.Lock,
        requested: threading.Lock,
        owned_name: str,
        requested_name: str,
    ) -> None:
        with owned:
            LOGGER.info("[%s] acquired %s", name, owned_name)
            rendezvous.wait()
            LOGGER.warning("[%s] WAITING for %s; state=BLOCKED", name, requested_name)
            requested.acquire()

    workers = [
        threading.Thread(
            target=worker,
            args=("Thread-A", first_lock, second_lock, "Resource-A", "Resource-B"),
            daemon=False,
        ),
        threading.Thread(
            target=worker,
            args=("Thread-B", second_lock, first_lock, "Resource-B", "Resource-A"),
            daemon=False,
        ),
    ]
    LOGGER.info("[DeadlockLab] START MULTI_THREAD_ENABLE=true")
    for thread in workers:
        thread.start()

    time.sleep(0.25)
    if all(thread.is_alive() for thread in workers):
        LOGGER.error(
            "[DeadlockLab] DEADLOCK DETECTED: PID=%d threads remain BLOCKED; log output stops here",
            os.getpid(),
        )

    while True:
        time.sleep(60)


def run_normal_scenario(config: Config) -> int:
    workers = ("Thread-A", "Thread-B", "Thread-C")
    progress = {worker: 0 for worker in workers}
    LOGGER.info("[Scheduler] START policy=round-robin quantum=%.2fs", config.scheduler_quantum)
    for _ in range(4):
        for worker in workers:
            progress[worker] += 25
            action = "Task Started" if progress[worker] == 25 else "Resumed"
            LOGGER.info("[%s] %s. Calculating... (%d%%)", worker, action, progress[worker])
            time.sleep(config.scheduler_quantum)
    LOGGER.info("[Scheduler] COMPLETED order=A,B,C,A,B,C,A,B,C,A,B,C")
    return 0


def main() -> int:
    try:
        config = Config.from_env()
    except (ConfigError, OSError, ValueError) as exc:
        print(f">>> [BOOT] FAILED: {exc} <<<", file=sys.stderr)
        return 2

    configure_logging(config.log_dir)
    try:
        with ServiceSocket(config.port):
            LOGGER.info(
                "[BOOT] SUCCESS user_uid=%d bind=0.0.0.0:%d scenario=%s",
                os.geteuid(),
                config.port,
                config.scenario,
            )
            scenarios = {
                "normal": run_normal_scenario,
                "memory": run_memory_scenario,
                "cpu": run_cpu_scenario,
                "deadlock": run_deadlock_scenario,
            }
            return scenarios[config.scenario](config)
    except OSError as exc:
        LOGGER.critical("[BOOT] FAILED: cannot bind 0.0.0.0:%d: %s", config.port, exc)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
