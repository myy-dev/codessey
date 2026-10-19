# [Bug] CPU 부하 증가로 원본 앱의 보호 종료 발생

## 1. Description — 현상

`MEMORY_LIMIT=512`, `CPU_MAX_OCCUPY=100`, `MULTI_THREAD_ENABLE=false` 조건에서 원본 CPU 작업의 부하 수치가 증가했습니다. 약 30초 후 앱 자체 부하 로그가 51.22%에 도달했고, `CPU Threshold Violated!`를 남긴 뒤 `SIGTERM`으로 종료했습니다.

```bash
docker compose build
MEMORY_LIMIT=512 CPU_MAX_OCCUPY=100 MULTI_THREAD_ENABLE=false docker compose run --rm agent-lab
```

실행·관제·증거 수집 절차: [동료 평가 시연 가이드](../USER_DEMO.md).

## 2. Evidence & Logs — 원본 증거

```text
2026-10-17 08:19:35,790 [INFO] [CpuWorker] Current Load: 30.75%
2026-10-17 08:19:38,909 [INFO] [CpuWorker] Current Load: 35.06%
2026-10-17 08:19:42,024 [INFO] [CpuWorker] Current Load: 37.87%
2026-10-17 08:19:45,143 [INFO] [CpuWorker] Current Load: 46.46%
2026-10-17 08:19:48,259 [INFO] [CpuWorker] Current Load: 51.22%
2026-10-17 08:19:48,360 [CRITICAL] [CpuWorker] CPU Threshold Violated! (51.220000000000006%).
```

`/proc`의 CPU 시간 증가량과 경과 시간으로 계산한 워커 CPU 최고치는 45.5%입니다. 앱의 `Current Load` 51.22%와는 측정 방식·구간이 달라 직접 비교하지 않습니다.

- [Before 원본 출력](../../evidence/generated/cpu-before.log)
- [Before 워커 관제](../../evidence/generated/cpu-before-monitor.log)
- [After 원본 출력](../../evidence/generated/cpu-after.log)
- [After 워커 관제](../../evidence/generated/cpu-after-monitor.log)
- [실행 환경·관측 시간·종료 주체](../EVIDENCE.md)
- [종료 코드·경과시간 재검증 원문 — 별도 실행](../../evidence/revalidation.log)

## 3. Root Cause Analysis — 원인 추론

앱 부하·워커 CPU 상승과 위반 로그 직후의 `SIGTERM` 종료는 CPU 부하 증가에 따른 보호 동작이라는 해석을 지지합니다. CPU를 공유하는 다른 작업의 대기시간이 늘어 응답 지연이 발생할 수 있으나, 이번 실험에서 실제 지연을 측정하지는 않았습니다.

100% 설정에서 앱 부하 약 51%로 종료되고 20% 설정에서는 냉각 로그가 나타나므로, `CPU_MAX_OCCUPY`는 단순 보호 임계값으로 해석할 수 없습니다. 설정은 부하 패턴에도 영향을 주며, 정확한 측정·보호 조건은 원본 소스 미확인으로 확정하지 않습니다.

## 4. Workaround & Verification — 조치 및 검증

메모리와 멀티스레드 설정을 유지하고 `CPU_MAX_OCCUPY`를 100에서 20으로 낮췄습니다.

| 항목 | Before | After |
| --- | --- | --- |
| `CPU_MAX_OCCUPY` | 100% | 20% |
| 메모리·멀티스레드 설정 | 512MB, false | 동일 |
| 앱 자체 부하 | 51.22% 및 위반 로그 | 20% 도달 후 냉각 로그 |
| 관제 최고 CPU | 45.5% | 18.2% |
| 관측 결과 | 약 30초 후 앱 보호 종료 | 40초 관측 중 생존 |
| 최종 종료 주체 | 앱, `SIGTERM` | 관측 후 외부 정리, `SIGTERM` |

After는 `Healthy System Monitoring` 경로에서 40초 관측 중 부하 완화와 보호 종료 회피를 확인한 결과입니다. 실행 경로와 관측 시간이 달라 동일 작업·동일 시간의 누적 부하 비교로 해석할 수 없습니다.
