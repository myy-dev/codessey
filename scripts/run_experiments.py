#!/usr/bin/env python3
"""모든 장애 시나리오를 실행하고 재현 가능한 증거 파일을 생성한다."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from generate_charts import main as generate_charts


ROOT = Path(__file__).resolve().parents[1]
MONITOR = ROOT / "scripts" / "monitor.sh"


@dataclass(frozen=True)
class Experiment:
    name: str
    scenario: str
    overrides: dict[str, str]
    timeout: float
    expected_exit: int | None
    required_log: str


EXPERIMENTS = (
    Experiment(
        name="oom-before",
        scenario="memory",
        overrides={"MEMORY_LIMIT": "50", "AGENT_RUN_SECONDS": "2.0"},
        timeout=5,
        expected_exit=137,
        required_log="SELF-TERMINATED",
    ),
    Experiment(
        name="oom-after",
        scenario="memory",
        overrides={"MEMORY_LIMIT": "128", "AGENT_RUN_SECONDS": "1.0"},
        timeout=5,
        expected_exit=0,
        required_log="COMPLETED without termination",
    ),
    Experiment(
        name="cpu-before",
        scenario="cpu",
        overrides={
            "CPU_MAX_OCCUPY": "20",
            "CPU_LOAD_PERCENT": "75",
            "AGENT_RUN_SECONDS": "2.0",
        },
        timeout=5,
        expected_exit=143,
        required_log="WATCHDOG: INITIATING EMERGENCY ABORT",
    ),
    Experiment(
        name="cpu-after",
        scenario="cpu",
        overrides={
            "CPU_MAX_OCCUPY": "95",
            "CPU_LOAD_PERCENT": "75",
            "AGENT_RUN_SECONDS": "1.5",
        },
        timeout=5,
        expected_exit=0,
        required_log="COMPLETED without termination",
    ),
    Experiment(
        name="deadlock-before",
        scenario="deadlock",
        overrides={"MULTI_THREAD_ENABLE": "true", "AGENT_RUN_SECONDS": "3.0"},
        timeout=1.5,
        expected_exit=None,
        required_log="DEADLOCK DETECTED",
    ),
    Experiment(
        name="deadlock-after",
        scenario="deadlock",
        overrides={"MULTI_THREAD_ENABLE": "false", "AGENT_RUN_SECONDS": "1.0"},
        timeout=5,
        expected_exit=0,
        required_log="COMPLETED without deadlock",
    ),
    Experiment(
        name="scheduling-round-robin",
        scenario="normal",
        overrides={"AGENT_RUN_SECONDS": "1.0", "SCHEDULER_QUANTUM": "0.03"},
        timeout=5,
        expected_exit=0,
        required_log="order=A,B,C,A,B,C",
    ),
)


def prepare_environment(name: str, output_root: Path) -> dict[str, str]:
    experiment_root = output_root / ".lab" / "experiments" / name
    if experiment_root.exists():
        shutil.rmtree(experiment_root)
    agent_home = experiment_root / "agent-home"
    upload_dir = agent_home / "upload_files"
    key_path = agent_home / "api_keys"
    log_dir = experiment_root / "logs"
    upload_dir.mkdir(parents=True)
    key_path.mkdir(parents=True)
    log_dir.mkdir(parents=True)
    (key_path / "secret.key").write_text("agent_api_key_test\n", encoding="utf-8")

    environment = os.environ.copy()
    environment.update(
        {
            "PYTHONPATH": str(ROOT / "src"),
            "AGENT_HOME": str(agent_home),
            "AGENT_UPLOAD_DIR": str(upload_dir),
            "AGENT_KEY_PATH": str(key_path),
            "AGENT_LOG_DIR": str(log_dir),
            "AGENT_PORT": "15034",
            "MEMORY_LIMIT": "50",
            "CPU_MAX_OCCUPY": "20",
            "MULTI_THREAD_ENABLE": "true",
            "LEAK_CHUNK_MB": "4",
            "LEAK_INTERVAL": "0.1",
            "WATCHDOG_INTERVAL": "0.25",
        }
    )
    return environment


def capture_process_snapshot(pid: int, destination: Path) -> None:
    commands = [["ps", "-ef"]]
    if platform.system() == "Linux":
        commands.append(["ps", "-L", "-p", str(pid), "-o", "pid,tid,pcpu,pmem,stat,comm"])
    else:
        commands.append(["ps", "-M", "-p", str(pid)])

    blocks: list[str] = []
    for command in commands:
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        output = completed.stdout
        if command == ["ps", "-ef"]:
            matching = [line for line in output.splitlines() if str(pid) in line or "UID" in line]
            output = "\n".join(matching) + "\n"
        blocks.append(f"$ {' '.join(command)}\n{output}")
    destination.write_text("\n".join(blocks), encoding="utf-8")


def parse_monitor(path: Path) -> dict[str, float]:
    cpu_values: list[float] = []
    rss_values: list[float] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        cpu_match = re.search(r"CPU:([0-9.]+)%", line)
        rss_match = re.search(r"RSS:([0-9.]+)MB", line)
        if cpu_match:
            cpu_values.append(float(cpu_match.group(1)))
        if rss_match:
            rss_values.append(float(rss_match.group(1)))
    return {
        "samples": len(rss_values),
        "min_cpu_percent": min(cpu_values, default=0.0),
        "max_cpu_percent": max(cpu_values, default=0.0),
        "final_cpu_percent": cpu_values[-1] if cpu_values else 0.0,
        "min_rss_mb": min(rss_values, default=0.0),
        "max_rss_mb": max(rss_values, default=0.0),
        "final_rss_mb": rss_values[-1] if rss_values else 0.0,
    }


def run_experiment(experiment: Experiment, output_root: Path) -> dict[str, object]:
    environment = prepare_environment(experiment.name, output_root)
    environment.update(experiment.overrides)
    environment["AGENT_SCENARIO"] = experiment.scenario

    evidence_dir = output_root / "evidence" / "generated"
    app_log = evidence_dir / f"{experiment.name}.log"
    monitor_log = evidence_dir / f"{experiment.name}-monitor.log"
    snapshot_file = evidence_dir / f"{experiment.name}-ps.txt"
    started = time.monotonic()
    timed_out = False

    with app_log.open("w", encoding="utf-8") as output:
        process = subprocess.Popen(
            [sys.executable, "-m", "agent_leak_app"],
            cwd=ROOT,
            env=environment,
            stdout=output,
            stderr=subprocess.STDOUT,
            text=True,
        )
        monitor = subprocess.Popen(
            [str(MONITOR), str(process.pid), str(monitor_log), "0.10"],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        try:
            process.wait(timeout=experiment.timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            capture_process_snapshot(process.pid, snapshot_file)
            process.send_signal(signal.SIGTERM)
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
        finally:
            monitor.terminate()
            try:
                monitor.wait(timeout=1)
            except subprocess.TimeoutExpired:
                monitor.kill()
                monitor.wait(timeout=1)

    log_text = app_log.read_text(encoding="utf-8")
    if experiment.required_log not in log_text:
        raise RuntimeError(f"{experiment.name}: missing required log: {experiment.required_log}")
    if experiment.expected_exit is not None and process.returncode != experiment.expected_exit:
        raise RuntimeError(
            f"{experiment.name}: expected exit {experiment.expected_exit}, got {process.returncode}"
        )
    if experiment.expected_exit is None and not timed_out:
        raise RuntimeError(f"{experiment.name}: expected the process to remain blocked")

    time.sleep(0.15)
    return {
        "name": experiment.name,
        "scenario": experiment.scenario,
        "exit_code": process.returncode,
        "timed_out_while_alive": timed_out,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "settings": {
            key: environment[key]
            for key in (
                "MEMORY_LIMIT",
                "CPU_MAX_OCCUPY",
                "MULTI_THREAD_ENABLE",
                "CPU_LOAD_PERCENT",
                "AGENT_RUN_SECONDS",
            )
            if key in environment
        },
        "monitor": parse_monitor(monitor_log),
        "files": {
            "application_log": str(app_log.relative_to(output_root)),
            "monitor_log": str(monitor_log.relative_to(output_root)),
            "process_snapshot": str(snapshot_file.relative_to(output_root)) if snapshot_file.exists() else None,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-root", type=Path, default=ROOT,
        help="출력 기준 디렉터리 (기본값: 프로젝트 루트)",
    )
    output_root = parser.parse_args().output_root.resolve()
    if os.geteuid() == 0:
        print("Evidence generation must run as a non-root user.", file=sys.stderr)
        return 2

    evidence_dir = output_root / "evidence" / "generated"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for old_file in evidence_dir.iterdir():
        if old_file.is_file():
            old_file.unlink()

    results = []
    for experiment in EXPERIMENTS:
        print(f"[run] {experiment.name}", flush=True)
        results.append(run_experiment(experiment, output_root))

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "experiments": results,
    }
    summary_path = evidence_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    generate_charts(output_root)
    print(f"Evidence generated: {len(results)} experiments -> {evidence_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
