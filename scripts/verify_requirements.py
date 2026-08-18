#!/usr/bin/env python3
"""README 체크리스트의 구현 증거를 기계적으로 검증한다."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "evidence" / "generated"


class VerificationError(AssertionError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def text(relative_path: str) -> str:
    path = ROOT / relative_path
    require(path.is_file(), f"missing file: {relative_path}")
    return path.read_text(encoding="utf-8")


def monitor_values(filename: str, field: str, unit: str) -> list[float]:
    pattern = re.compile(rf"{field}:([0-9.]+){re.escape(unit)}")
    return [
        float(match.group(1))
        for line in text(f"evidence/generated/{filename}").splitlines()
        if (match := pattern.search(line))
    ]


def verify_manifest() -> int:
    manifest = json.loads(text("evidence/generated/manifest.sha256.json"))
    for relative_path, expected in manifest.items():
        artifact = ROOT / relative_path
        require(artifact.is_file(), f"manifest target missing: {relative_path}")
        actual = hashlib.sha256(artifact.read_bytes()).hexdigest()
        require(actual == expected, f"checksum mismatch: {relative_path}")
    return len(manifest)


def verify_markdown_links() -> int:
    checked = 0
    link_pattern = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
    markdown_files = [ROOT / "README.md"]
    markdown_files.extend(sorted((ROOT / "docs").glob("*.md")))
    markdown_files.extend(sorted((ROOT / "evidence").glob("*.md")))
    markdown_files.extend(sorted((ROOT / "reports").glob("*.md")))
    for markdown_file in markdown_files:
        for target in link_pattern.findall(markdown_file.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            file_target = target.split("#", 1)[0].strip("<>")
            require(
                (markdown_file.parent / file_target).resolve().exists(),
                f"broken Markdown link in {markdown_file.relative_to(ROOT)}: {target}",
            )
            checked += 1
    return checked


def main() -> int:
    readme = text("README.md")
    require("- [ ]" not in readme, "README still contains an incomplete checklist item")
    require(readme.count("- [x]") >= 60, "README completion checklist is unexpectedly short")

    required_files = (
        "Dockerfile",
        "compose.yaml",
        "bin/agent-leak-app",
        "bin/agent-app-leak-x86",
        "bin/agent-app-leak-arm64",
        "scripts/setup_lab.sh",
        "scripts/select_binary.sh",
        "scripts/monitor.sh",
        "reports/oom-report.md",
        "reports/cpu-report.md",
        "reports/deadlock-report.md",
        "reports/scheduling-report.md",
        "docs/USAGE.md",
    )
    for relative_path in required_files:
        require((ROOT / relative_path).is_file(), f"required artifact missing: {relative_path}")

    summary = json.loads(text("evidence/generated/summary.json"))
    require(summary["platform"].startswith("Linux-"), "evidence was not generated on Linux")
    experiments = {item["name"]: item for item in summary["experiments"]}
    require(len(experiments) == 7, "expected seven experiments")

    require(experiments["oom-before"]["exit_code"] == 137, "OOM before did not self-terminate")
    require(experiments["oom-after"]["exit_code"] == 0, "OOM after did not survive")
    oom_rss = monitor_values("oom-before-monitor.log", "RSS", "MB")
    monitor_increases = sum(current > previous for previous, current in zip(oom_rss, oom_rss[1:]))
    require(
        len(oom_rss) >= 3 and monitor_increases >= 2 and max(oom_rss) - min(oom_rss) >= 8,
        "OOM monitor does not prove a rising RSS pattern",
    )
    oom_before_log = text("evidence/generated/oom-before.log")
    app_rss = [float(value) for value in re.findall(r"RSS=([0-9.]+)MB", oom_before_log)]
    require(
        len(app_rss) >= 6 and app_rss[-1] - app_rss[0] >= 20,
        "OOM application log does not prove sustained allocation growth",
    )
    require("Memory limit exceeded" in oom_before_log, "OOM threshold log missing")
    require("SELF-TERMINATED" in oom_before_log, "OOM termination log missing")

    require(experiments["cpu-before"]["exit_code"] == 143, "CPU before was not SIGTERM-protected")
    require(experiments["cpu-after"]["exit_code"] == 0, "CPU after did not survive")
    cpu_before_log = text("evidence/generated/cpu-before.log")
    require("CPU threshold exceeded" in cpu_before_log, "CPU threshold evidence missing")
    require("WATCHDOG: INITIATING EMERGENCY ABORT (SIGTERM)" in cpu_before_log, "Watchdog log missing")

    deadlock_before = experiments["deadlock-before"]
    require(deadlock_before["timed_out_while_alive"] is True, "deadlock PID did not remain alive")
    deadlock_log = text("evidence/generated/deadlock-before.log")
    require("WAITING" in deadlock_log and "BLOCKED" in deadlock_log, "deadlock wait logs missing")
    deadlock_cpu = monitor_values("deadlock-before-monitor.log", "CPU", "%")
    deadlock_rss = monitor_values("deadlock-before-monitor.log", "RSS", "MB")
    require(
        len(deadlock_cpu) >= 8 and all(value == 0 for value in deadlock_cpu[-6:]),
        "deadlock CPU did not settle at 0%",
    )
    require(len(set(deadlock_rss[-6:])) == 1, "deadlock RSS was not stationary")
    ps_snapshot = text("evidence/generated/deadlock-before-ps.txt")
    require("ps -ef" in ps_snapshot and "ps -L" in ps_snapshot, "Linux process/thread snapshot missing")
    require(experiments["deadlock-after"]["exit_code"] == 0, "deadlock workaround failed")

    scheduler_log = text("evidence/generated/scheduling-round-robin.log")
    require("order=A,B,C,A,B,C,A,B,C,A,B,C" in scheduler_log, "round-robin order missing")

    for chart in (
        "oom-memory.svg",
        "cpu-usage.svg",
        "deadlock-cpu.svg",
        "deadlock-rss.svg",
        "scheduling-timeline.svg",
    ):
        require((ROOT / "evidence" / "charts" / chart).is_file(), f"chart missing: {chart}")

    report_links = {
        "reports/oom-report.md": ("oom-before.log", "oom-after.log"),
        "reports/cpu-report.md": ("cpu-before.log", "cpu-after.log"),
        "reports/deadlock-report.md": ("deadlock-before.log", "deadlock-before-ps.txt"),
        "reports/scheduling-report.md": ("scheduling-round-robin.log",),
    }
    for report, names in report_links.items():
        report_text = text(report)
        for name in names:
            require(name in report_text, f"{report} does not link {name}")

    manifest_count = verify_manifest()
    link_count = verify_markdown_links()
    print("Requirements verification: PASS")
    print(f"- Linux experiments: {len(experiments)}")
    print(f"- Evidence artifacts verified: {manifest_count}")
    print(f"- Local Markdown links verified: {link_count}")
    print("- OOM: RSS growth + exit 137 + Before/After verified")
    print("- CPU: Watchdog SIGTERM + exit 143 + Before/After verified")
    print("- Deadlock: live PID + 0% CPU/RSS plateau + ps -L + workaround verified")
    print("- Scheduling: A→B→C round-robin pattern verified")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except VerificationError as exc:
        print(f"Requirements verification: FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
