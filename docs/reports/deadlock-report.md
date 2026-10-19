# [Bug] 두 워커의 순환 자원 대기로 원본 앱의 작업 진행 중단

## 1. Description — 현상

`MEMORY_LIMIT=512`, `CPU_MAX_OCCUPY=20`, `MULTI_THREAD_ENABLE=true` 조건에서 원본 워커들이 서로 다른 자원을 획득한 뒤 상대 자원을 기다렸습니다. 14초 관측 종료 시점까지 PID는 유지됐지만 작업 로그가 더 진행되지 않았습니다.

```bash
docker compose build
MEMORY_LIMIT=512 CPU_MAX_OCCUPY=20 MULTI_THREAD_ENABLE=true docker compose run --rm agent-lab
```

실행·관제·증거 수집 절차: [동료 평가 시연 가이드](../USER_DEMO.md).

## 2. Evidence & Logs — 원본 증거

두 워커는 각 자원을 획득한 뒤 상대 자원을 기다립니다.

```text
[AgentWorker][Worker-Thread-1] LOCK ACQUIRED: [Shared_Memory_A]. (Holding...)
[AgentWorker][Worker-Thread-2] LOCK ACQUIRED: [Socket_Pool_B]. (Holding...)
```

마지막 `WAITING ... (Status: BLOCKED)` 로그 이후 작업 진행이 멈췄습니다.

```text
$ ps -L -p 22948 -o pid,tid,pcpu,pmem,stat,wchan:24,comm
  PID   TID %CPU %MEM STAT WCHAN                    COMMAND
22948 22948  0.1  0.2 SNl  futex_wait_queue         agent-leak-app-
22948 24843  0.0  0.2 SNl  futex_wait_queue         agent-leak-app-
22948 24844  0.0  0.2 SNl  futex_wait_queue         agent-leak-app-
```

실행기 PID `22947`의 실제 워커 PID `22948`에서 세 스레드 모두 `futex_wait_queue` 대기였고, 후반 관제 CPU `0.0%`·RSS `16.7MB`·스레드 3개가 유지됐습니다. `ps`의 CPU 0.1%는 수명 평균으로, 관제의 구간 CPU와 구분합니다.

- [Before 원본 출력](../../evidence/generated/deadlock-before.log)
- [Before 워커 관제](../../evidence/generated/deadlock-before-monitor.log)
- [ps -ef·ps -L 원문](../../evidence/generated/deadlock-before-ps.txt)
- [After 원본 출력](../../evidence/generated/deadlock-after.log)
- [After 워커 관제](../../evidence/generated/deadlock-after-monitor.log)
- [실행 환경·관측 시간·종료 주체](../EVIDENCE.md)
- [종료 코드·경과시간 재검증 원문 — 별도 실행](../../evidence/revalidation.log)

## 3. Root Cause Analysis — 원인 추론

`Shared_Memory_A → Socket_Pool_B → Shared_Memory_A`의 순환 대기 로그와 스레드 대기·CPU/RSS 정체·로그 무진행은 교착상태라는 해석을 지지합니다. `futex` 대기만으로 교착을 확정할 수는 없습니다.

교착상태의 네 조건을 로그에 대입하면 다음과 같습니다.

1. 상호 배제: 각 자원의 `LOCK ACQUIRED` 로그와 상대 워커의 대기.
2. 점유 대기: 이미 하나의 자원을 획득한 채 다른 자원 요청.
3. 비선점: 관측 시간 동안 기존 자원 해제·강제 회수 없이 대기 지속.
4. 순환 대기: 두 워커가 서로 보유한 자원을 요청하는 고리.

확인 범위는 14초 관측 중 순환 대기와 작업 중단이며, 원본 내부 미확인으로 정확한 락 구현이나 영구 대기는 확정할 수 없습니다.

## 4. Workaround & Verification — 조치 및 검증

메모리·CPU 설정을 유지하고 `MULTI_THREAD_ENABLE`만 false로 변경했습니다.

| 항목 | Before | After |
| --- | --- | --- |
| 멀티스레드 설정 | true | false |
| 로그 | 자원 획득 후 상호 WAITING/BLOCKED | 안정 모드 작업 완료 후 메모리·CPU 작업 로그 갱신 |
| 14초 관측 | PID 유지, 로그 무진행 | PID 유지, 작업 진행 |
| 관측 종료 후 | 관측 후 외부 `SIGTERM` 정리 | 관측 후 외부 `SIGTERM` 정리 |

After는 `Healthy System Monitoring` 경로로, 동일한 락 코드의 순차 실행을 입증한 결과는 아닙니다. `false`여도 메모리·CPU 워커로 스레드가 3개일 수 있으므로, 스레드 수 감소나 자연 종료 대신 작업 진행 여부로 조치 결과를 판단했습니다.
