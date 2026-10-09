"""애플리케이션 부트 설정 검증."""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


class ConfigError(ValueError):
    """필수 실행 조건이 충족되지 않았을 때 발생한다."""


TRUE_VALUES = {"true", "1", "yes"}
FALSE_VALUES = {"false", "0", "no"}
SCENARIOS = {"normal", "memory", "cpu", "deadlock"}


def _required(env: Mapping[str, str], name: str) -> str:
    value = env.get(name, "").strip()
    if not value:
        raise ConfigError(f"{name} is required")
    return value


def _integer(env: Mapping[str, str], name: str, minimum: int, maximum: int) -> int:
    raw = _required(env, name)
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer") from exc
    if not minimum <= value <= maximum:
        raise ConfigError(f"{name} must be between {minimum} and {maximum}")
    return value


def _positive_float(env: Mapping[str, str], name: str, default: float) -> float:
    raw = env.get(name, str(default)).strip()
    try:
        value = float(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be a number") from exc
    if not math.isfinite(value) or value <= 0:
        raise ConfigError(f"{name} must be finite and greater than zero")
    return value


def parse_bool(raw: str) -> bool:
    normalized = raw.strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    raise ConfigError("MULTI_THREAD_ENABLE must be true/false, 1/0, or yes/no")


@dataclass(frozen=True)
class Config:
    agent_home: Path
    upload_dir: Path
    key_path: Path
    log_dir: Path
    port: int
    memory_limit_mb: int
    cpu_max_occupy: int
    multi_thread_enable: bool
    scenario: str
    run_seconds: float
    leak_chunk_mb: int
    leak_interval: float
    cpu_load_percent: int
    watchdog_interval: float
    scheduler_quantum: float

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str] | None = None,
        *,
        euid: int | None = None,
    ) -> "Config":
        values = os.environ if env is None else env
        effective_uid = os.geteuid() if euid is None else euid
        if effective_uid == 0:
            raise ConfigError("agent-leak-app must run as a non-root user")

        agent_home = Path(_required(values, "AGENT_HOME")).expanduser().resolve()
        upload_dir = Path(_required(values, "AGENT_UPLOAD_DIR")).expanduser().resolve()
        key_path = Path(_required(values, "AGENT_KEY_PATH")).expanduser().resolve()
        log_dir = Path(_required(values, "AGENT_LOG_DIR")).expanduser().resolve()

        expected_upload = (agent_home / "upload_files").resolve()
        expected_key_path = (agent_home / "api_keys").resolve()
        if upload_dir != expected_upload:
            raise ConfigError("AGENT_UPLOAD_DIR must be $AGENT_HOME/upload_files")
        if key_path != expected_key_path:
            raise ConfigError("AGENT_KEY_PATH must be $AGENT_HOME/api_keys")

        for name, path in (
            ("AGENT_HOME", agent_home),
            ("AGENT_UPLOAD_DIR", upload_dir),
            ("AGENT_KEY_PATH", key_path),
            ("AGENT_LOG_DIR", log_dir),
        ):
            if not path.is_dir():
                raise ConfigError(f"{name} directory does not exist: {path}")

        if not os.access(log_dir, os.W_OK):
            raise ConfigError(f"AGENT_LOG_DIR is not writable: {log_dir}")

        secret_file = key_path / "secret.key"
        if not secret_file.is_file():
            raise ConfigError(f"secret.key does not exist: {secret_file}")
        if secret_file.read_text(encoding="utf-8").strip() != "agent_api_key_test":
            raise ConfigError("secret.key content must be agent_api_key_test")

        port = _integer(values, "AGENT_PORT", 1, 65535)
        if port != 15034:
            raise ConfigError("AGENT_PORT must be 15034")

        memory_limit_mb = _integer(values, "MEMORY_LIMIT", 50, 512)
        cpu_max_occupy = _integer(values, "CPU_MAX_OCCUPY", 10, 100)
        multi_thread_enable = parse_bool(_required(values, "MULTI_THREAD_ENABLE"))

        scenario = values.get("AGENT_SCENARIO", "normal").strip().lower()
        if scenario not in SCENARIOS:
            raise ConfigError(f"AGENT_SCENARIO must be one of: {', '.join(sorted(SCENARIOS))}")

        leak_chunk_mb = int(values.get("LEAK_CHUNK_MB", "4"))
        if not 1 <= leak_chunk_mb <= 32:
            raise ConfigError("LEAK_CHUNK_MB must be between 1 and 32")

        cpu_load_percent = int(values.get("CPU_LOAD_PERCENT", "75"))
        if not 1 <= cpu_load_percent <= 100:
            raise ConfigError("CPU_LOAD_PERCENT must be between 1 and 100")

        return cls(
            agent_home=agent_home,
            upload_dir=upload_dir,
            key_path=key_path,
            log_dir=log_dir,
            port=port,
            memory_limit_mb=memory_limit_mb,
            cpu_max_occupy=cpu_max_occupy,
            multi_thread_enable=multi_thread_enable,
            scenario=scenario,
            run_seconds=_positive_float(values, "AGENT_RUN_SECONDS", 2.0),
            leak_chunk_mb=leak_chunk_mb,
            leak_interval=_positive_float(values, "LEAK_INTERVAL", 0.1),
            cpu_load_percent=cpu_load_percent,
            watchdog_interval=_positive_float(values, "WATCHDOG_INTERVAL", 0.25),
            scheduler_quantum=_positive_float(values, "SCHEDULER_QUANTUM", 0.05),
        )
