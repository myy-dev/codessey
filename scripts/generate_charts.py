#!/usr/bin/env python3
"""관제 로그를 GitHub에서 바로 볼 수 있는 SVG 증거 그래프로 변환한다."""

from __future__ import annotations

import argparse
import html
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COLORS = ("#2563eb", "#dc2626", "#059669", "#7c3aed")


def read_metric(path: Path, metric: str) -> list[float]:
    pattern = re.compile(rf"{metric}:([0-9.]+)(?:%|MB)")
    return [
        float(match.group(1))
        for line in path.read_text(encoding="utf-8").splitlines()
        if (match := pattern.search(line))
    ]


def trim_process_teardown(values: list[float]) -> list[float]:
    """프로세스 종료 직전 객체 해제로 발생한 급락 샘플을 그래프에서 제외한다."""
    trimmed: list[float] = []
    peak = 0.0
    for value in values:
        if peak >= 30 and value < peak * 0.7:
            break
        trimmed.append(value)
        peak = max(peak, value)
    return trimmed


def update_manifest(output_root: Path) -> None:
    generated = output_root / "evidence" / "generated"
    charts = output_root / "evidence" / "charts"
    artifact_paths = [
        path
        for path in sorted(generated.iterdir())
        if path.is_file() and path.name != "manifest.sha256.json"
    ]
    artifact_paths.extend(sorted(charts.glob("*.svg")))
    manifest = {
        str(path.relative_to(output_root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in artifact_paths
    }
    (generated / "manifest.sha256.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )


def points(values: list[float], left: int, top: int, width: int, height: int, maximum: float) -> str:
    if not values:
        return ""
    divisor = max(len(values) - 1, 1)
    return " ".join(
        f"{left + (index / divisor) * width:.1f},{top + height - (value / maximum) * height:.1f}"
        for index, value in enumerate(values)
    )


def write_line_chart(
    path: Path,
    title: str,
    unit: str,
    series: list[tuple[str, list[float]]],
    *,
    maximum: float,
    threshold: float | None = None,
) -> None:
    width, height = 960, 420
    left, top, plot_width, plot_height = 78, 70, 820, 275
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{left}" y="34" font-family="sans-serif" font-size="22" font-weight="700" fill="#111827">{html.escape(title)}</text>',
    ]
    for tick in range(6):
        value = maximum * tick / 5
        y = top + plot_height - plot_height * tick / 5
        elements.extend(
            [
                f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_width}" y2="{y:.1f}" stroke="#e5e7eb"/>',
                f'<text x="{left - 12}" y="{y + 5:.1f}" text-anchor="end" font-family="monospace" font-size="12" fill="#4b5563">{value:.0f}</text>',
            ]
        )
    if threshold is not None:
        threshold_y = top + plot_height - (threshold / maximum) * plot_height
        elements.extend(
            [
                f'<line x1="{left}" y1="{threshold_y:.1f}" x2="{left + plot_width}" y2="{threshold_y:.1f}" stroke="#f59e0b" stroke-width="2" stroke-dasharray="8 6"/>',
                f'<text x="{left + plot_width - 4}" y="{threshold_y - 7:.1f}" text-anchor="end" font-family="sans-serif" font-size="12" fill="#92400e">기준값 {threshold:g}{html.escape(unit)}</text>',
            ]
        )
    for index, (label, values) in enumerate(series):
        color = COLORS[index % len(COLORS)]
        polyline = points(values, left, top, plot_width, plot_height, maximum)
        elements.append(
            f'<polyline points="{polyline}" fill="none" stroke="{color}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>'
        )
        legend_x = left + index * 230
        elements.extend(
            [
                f'<line x1="{legend_x}" y1="382" x2="{legend_x + 28}" y2="382" stroke="{color}" stroke-width="4"/>',
                f'<text x="{legend_x + 36}" y="387" font-family="sans-serif" font-size="14" fill="#111827">{html.escape(label)}</text>',
            ]
        )
    elements.extend(
        [
            f'<line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}" stroke="#111827"/>',
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#111827"/>',
            f'<text x="20" y="{top + plot_height / 2}" transform="rotate(-90 20 {top + plot_height / 2})" text-anchor="middle" font-family="sans-serif" font-size="13" fill="#374151">{html.escape(unit)}</text>',
            f'<text x="{left + plot_width / 2}" y="365" text-anchor="middle" font-family="sans-serif" font-size="13" fill="#374151">관제 샘플 순서 (0.1초 간격)</text>',
            "</svg>",
        ]
    )
    path.write_text("\n".join(elements) + "\n", encoding="utf-8")


def write_scheduler_chart(log_path: Path, chart_path: Path) -> None:
    log_text = log_path.read_text(encoding="utf-8")
    labels = re.findall(r"\[(Thread-[ABC])\] (?:Task Started|Resumed)", log_text)
    box_width = 68
    total_width = 90 + box_width * len(labels)
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="210" viewBox="0 0 {total_width} 210">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="30" y="34" font-family="sans-serif" font-size="21" font-weight="700" fill="#111827">Round-Robin 실행 순서</text>',
    ]
    color_by_thread = {"Thread-A": "#2563eb", "Thread-B": "#059669", "Thread-C": "#7c3aed"}
    for index, label in enumerate(labels):
        x = 30 + index * box_width
        short_label = label[-1]
        elements.extend(
            [
                f'<rect x="{x}" y="78" width="58" height="54" rx="7" fill="{color_by_thread[label]}"/>',
                f'<text x="{x + 29}" y="111" text-anchor="middle" font-family="sans-serif" font-size="18" font-weight="700" fill="#ffffff">{short_label}</text>',
                f'<text x="{x + 29}" y="153" text-anchor="middle" font-family="monospace" font-size="11" fill="#4b5563">q{index + 1}</text>',
            ]
        )
    elements.extend(
        [
            '<text x="30" y="188" font-family="sans-serif" font-size="13" fill="#374151">각 워커가 한 번씩 실행된 뒤 다시 A로 돌아가는 순환 패턴</text>',
            "</svg>",
        ]
    )
    chart_path.write_text(
        "\n".join(elements) + "\n", encoding="utf-8"
    )


def main(output_root: Path = ROOT) -> int:
    generated = output_root / "evidence" / "generated"
    charts = output_root / "evidence" / "charts"
    charts.mkdir(parents=True, exist_ok=True)
    write_line_chart(
        charts / "oom-memory.svg",
        "OOM 실험: MEMORY_LIMIT 변경 전후 RSS",
        "RSS (MB)",
        [
            (
                "Before: 50MB",
                trim_process_teardown(read_metric(generated / "oom-before-monitor.log", "RSS")),
            ),
            (
                "After: 128MB",
                trim_process_teardown(read_metric(generated / "oom-after-monitor.log", "RSS")),
            ),
        ],
        maximum=135,
        threshold=50,
    )
    write_line_chart(
        charts / "cpu-usage.svg",
        "CPU 실험: 동일 부하에서 임계값 변경 전후",
        "CPU (%)",
        [
            ("Before: limit 20%", read_metric(generated / "cpu-before-monitor.log", "CPU")),
            ("After: limit 95%", read_metric(generated / "cpu-after-monitor.log", "CPU")),
        ],
        maximum=105,
        threshold=20,
    )
    write_line_chart(
        charts / "deadlock-rss.svg",
        "Deadlock 실험: 프로세스 RSS 정체",
        "RSS (MB)",
        [("MULTI_THREAD_ENABLE=true", read_metric(generated / "deadlock-before-monitor.log", "RSS"))],
        maximum=30,
    )
    write_line_chart(
        charts / "deadlock-cpu.svg",
        "Deadlock 실험: 교착 후 CPU 활동 소멸",
        "CPU (%)",
        [("MULTI_THREAD_ENABLE=true", read_metric(generated / "deadlock-before-monitor.log", "CPU"))],
        maximum=105,
    )
    write_scheduler_chart(generated / "scheduling-round-robin.log", charts / "scheduling-timeline.svg")
    update_manifest(output_root)
    print(f"Charts generated: {charts}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-root", type=Path, default=ROOT,
        help="출력 기준 디렉터리 (기본값: 프로젝트 루트)",
    )
    raise SystemExit(main(parser.parse_args().output_root.resolve()))
