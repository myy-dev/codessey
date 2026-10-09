# 증거 자료 인덱스

모든 파일은 다음 명령으로 다시 생성할 수 있습니다.

```bash
make docker-evidence
```

## 실행 환경

- 운영체제: Ubuntu 24.04 LTS 컨테이너 (`ubuntu:24.04`)
- Linux 커널: Docker Desktop LinuxKit
- 아키텍처: `aarch64`
- Python: `3.12.3`
- 상세 환경: [`generated/summary.json`](generated/summary.json)

## 장애별 증거

| 구분 | 애플리케이션 로그 | 관제 로그 | 추가 증거 | 그래프 |
| --- | --- | --- | --- | --- |
| OOM Before | [`oom-before.log`](generated/oom-before.log) | [`oom-before-monitor.log`](generated/oom-before-monitor.log) | 종료 코드 137 | [`oom-memory.svg`](charts/oom-memory.svg) |
| OOM After | [`oom-after.log`](generated/oom-after.log) | [`oom-after-monitor.log`](generated/oom-after-monitor.log) | 종료 코드 0 | [`oom-memory.svg`](charts/oom-memory.svg) |
| CPU Before | [`cpu-before.log`](generated/cpu-before.log) | [`cpu-before-monitor.log`](generated/cpu-before-monitor.log) | 종료 코드 143 | [`cpu-usage.svg`](charts/cpu-usage.svg) |
| CPU After | [`cpu-after.log`](generated/cpu-after.log) | [`cpu-after-monitor.log`](generated/cpu-after-monitor.log) | 종료 코드 0 | [`cpu-usage.svg`](charts/cpu-usage.svg) |
| Deadlock Before | [`deadlock-before.log`](generated/deadlock-before.log) | [`deadlock-before-monitor.log`](generated/deadlock-before-monitor.log) | [`ps`/`ps -L` 출력](generated/deadlock-before-ps.txt) | [`deadlock-cpu.svg`](charts/deadlock-cpu.svg), [`deadlock-rss.svg`](charts/deadlock-rss.svg) |
| Deadlock After | [`deadlock-after.log`](generated/deadlock-after.log) | [`deadlock-after-monitor.log`](generated/deadlock-after-monitor.log) | 종료 코드 0 | - |
| Scheduling | [`scheduling-round-robin.log`](generated/scheduling-round-robin.log) | [`scheduling-round-robin-monitor.log`](generated/scheduling-round-robin-monitor.log) | A→B→C 순환 로그 | [`scheduling-timeline.svg`](charts/scheduling-timeline.svg) |

## 무결성 확인

[`generated/manifest.sha256.json`](generated/manifest.sha256.json)은 로그, 명령어 출력, 요약 파일, SVG 그래프의 SHA-256 해시를 기록합니다.
