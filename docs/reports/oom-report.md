# [Bug] 메모리 증가로 원본 앱의 MemoryGuard 보호 종료 발생

## 1. Description — 현상

과제 제공 ARM64 원본을 `MEMORY_LIMIT=50`, `CPU_MAX_OCCUPY=20`, `MULTI_THREAD_ENABLE=false`로 실행했습니다. 약 5초 뒤 앱 내부 Heap 계수가 50MB에 도달하면서 MemoryGuard 로그를 남기고 `SIGKILL`로 종료했습니다.

```bash
docker compose build
MEMORY_LIMIT=50 CPU_MAX_OCCUPY=20 MULTI_THREAD_ENABLE=false docker compose run --rm agent-lab
```

실행·관제·증거 수집 절차: [동료 평가 시연 가이드](../USER_DEMO.md).

## 2. Evidence & Logs — 원본 증거

```text
2026-10-17 08:19:03,025 [INFO] [MemoryWorker] Current Heap: 25MB
2026-10-17 08:19:06,032 [INFO] [MemoryWorker] Current Heap: 50MB
2026-10-17 08:19:06,033 [CRITICAL] [MemoryGuard] Memory limit exceeded (50MB >= 50MB) / (Recommend Over 256MB)
2026-10-17 08:19:06,033 [CRITICAL] [MemoryGuard] Self-terminating process 8 to prevent system instability.
```

실행기 PID `7`과 구분한 실제 워커 PID `8`의 RSS는 `10.1→41.6MB`로 증가했습니다. 앱 내부 Heap 50MB와 관제 최고 RSS 41.6MB는 측정 범위·시점이 달라 직접 비교하지 않습니다.

- [Before 원본 출력](../../evidence/generated/oom-before.log)
- [Before 워커 관제](../../evidence/generated/oom-before-monitor.log)
- [After 원본 출력](../../evidence/generated/oom-after.log)
- [After 워커 관제](../../evidence/generated/oom-after-monitor.log)
- [실행 환경·관측 시간·종료 주체](../EVIDENCE.md)
- [종료 코드·경과시간 재검증 원문 — 별도 실행](../../evidence/revalidation.log)

## 3. Root Cause Analysis — 원인 추론

Heap·RSS 증가와 MemoryGuard 자기 종료 로그는 메모리 누적에 따른 앱 내부 보호 종료라는 해석을 지지합니다. Linux RSS는 프로세스가 실제로 사용하는 상주 메모리 크기입니다.

일반적으로 반환되지 않은 힙 메모리의 누적은 가용 메모리를 줄여 시스템의 메모리 압박과 다른 작업의 지연을 유발할 수 있습니다.

원본 소스 미확인으로 특정 자료구조의 참조 유지나 메모리 해제 결함은 확정할 수 없으며, 커널 OOM Killer가 종료했다는 증거도 없습니다.

## 4. Workaround & Verification — 조치 및 검증

`MEMORY_LIMIT`만 50에서 512로 변경하고 나머지 설정을 유지했습니다.

| 항목 | Before | After |
| --- | --- | --- |
| `MEMORY_LIMIT` | 50MB | 512MB |
| CPU·멀티스레드 설정 | 20%, false | 동일 |
| 앱 내부 Heap 마지막 로그 | 50MB | 100MB |
| 관제 최고 RSS | 41.6MB | 91.8MB |
| 관측 결과 | 약 5초 후 앱 보호 종료 | 12초 관측 중 생존 |
| 최종 종료 주체 | 앱, `SIGKILL` | 관측 후 외부 정리, `SIGTERM` |

512 설정에서는 `Healthy System Monitoring` 경로가 선택돼 동일 할당 루프의 임계값만 바뀐 비교로 해석할 수 없습니다. Heap·RSS 증가가 계속됐으므로 관측 시간 내 조기 종료를 피한 임시 조치이며, 누수 해결이나 장기 안정성을 입증한 결과는 아닙니다.
