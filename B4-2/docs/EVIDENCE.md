# 원본 앱 실행 증거

## 출처 및 환경

- [agent-app-leak/](../agent-app-leak)에 압축 해제해 보관한 수정 없는 원본 바이너리
- 실제 실행 대상: `agent-leak-app-arm64`
- 수집 환경: Ubuntu 24.04.5 LTS, Linux aarch64, Docker Desktop LinuxKit

## 시연 환경

| 항목 | 부트 조건 |
| --- | --- |
| 실행 계정 | root가 아닌 일반 사용자 |
| `AGENT_HOME` | 앱 기준 디렉터리 |
| `AGENT_UPLOAD_DIR` | `$AGENT_HOME/upload_files`, 디렉터리 존재 |
| `AGENT_KEY_PATH` | `$AGENT_HOME/api_keys`, 디렉터리 존재 |
| `AGENT_LOG_DIR` | 존재하고 쓰기 가능한 로그 디렉터리 |
| `AGENT_PORT` | `15034`, 바인딩 가능 |
| `secret.key` | 키 디렉터리에 존재, 내용 `agent_api_key_test` |
| `MEMORY_LIMIT` | 정수 50~512 MB |
| `CPU_MAX_OCCUPY` | 정수 10~100 % |
| `MULTI_THREAD_ENABLE` | true/false, 과제 명세의 추가 허용값 1/0·yes/no |

## 장애별 증거

| 구분 | 앱 출력 원문 | 실제 워커 관제 | 관측 결과 |
| --- | --- | --- | --- |
| OOM Before | [실행 로그](../evidence/generated/oom-before.log) | [관제](../evidence/generated/oom-before-monitor.log) | 약 5초 후 앱 `SIGKILL` 종료 |
| OOM After | [실행 로그](../evidence/generated/oom-after.log) | [관제](../evidence/generated/oom-after-monitor.log) | 12초 생존 후 외부 `SIGTERM` 정리 |
| CPU Before | [실행 로그](../evidence/generated/cpu-before.log) | [관제](../evidence/generated/cpu-before-monitor.log) | 약 30초 후 앱 `SIGTERM` 종료 |
| CPU After | [실행 로그](../evidence/generated/cpu-after.log) | [관제](../evidence/generated/cpu-after-monitor.log) | 40초 생존 후 외부 `SIGTERM` 정리 |
| Deadlock Before | [실행 로그](../evidence/generated/deadlock-before.log) | [관제](../evidence/generated/deadlock-before-monitor.log) | 14초 관측 중 무진행, 수집 후 외부 정리 |
| Deadlock After | [실행 로그](../evidence/generated/deadlock-after.log) | [관제](../evidence/generated/deadlock-after-monitor.log) | 14초 관측 중 작업 로그 갱신, 수집 후 외부 정리 |

Deadlock의 추가 증거: [ps -ef·ps -L 원문](../evidence/generated/deadlock-before-ps.txt).

## 종료 상태 재검증

[별도 재실행 기록](../evidence/revalidation.log)에 장애 3종의 조치 전후 6개 실행 설정·시작/종료 시각·경과시간·종료 코드·외부 정리 여부를 보관했습니다. OOM Before는 `137`, CPU Before는 `143`으로 보호 종료했고, 나머지는 관측 후 외부 `SIGTERM`으로 정리했습니다.

## 관제 및 종료 상태

`LAUNCHER_PID`는 원본 실행기, `WORKER_PID`는 관제 대상인 실제 워커 자식의 PID입니다.

`monitor.sh`는 실제 워커의 CPU·RSS·VSZ·프로세스 상태·스레드 수를 기록합니다. CPU는 `/proc`의 CPU 시간 증가량과 경과 시간으로 계산하며 첫 샘플은 0.0%입니다. RSS는 상주 메모리, VSZ는 가상 메모리 크기입니다. 요청 간격 0.10초에 명령 실행 시간이 더해지므로 실제 샘플 간격과는 차이가 있습니다.

| 셸 종료 상태 | 의미 |
| --- | --- |
| `1` | 원본 앱의 부트 실패 |
| `137` | `SIGKILL` 종료 |
| `143` | `SIGTERM` 종료 |

`143`은 앱의 보호 종료와 외부 정리 모두에서 나타날 수 있으므로 종료 로그와 조작 기록을 함께 확인합니다.

## 해석 기준

수동 시연에는 PID 조회·명령 입력 시간이 더해져 기존 수집 기록과 관측 시간이 달라질 수 있습니다. 실제 관측 시간·설정·종료 주체를 기록하며, 생존 시간 증가는 누수 해결이나 무기한 정상 실행의 증거가 아닙니다.

현재 시연 가이드는 화면 관찰과 기존 리포트 비교를 위한 절차입니다. 관제 결과는 새로 보관하지 않으며, 앱 메시지는 컨테이너의 `/tmp/agent-demo.log`에서 임시 확인합니다. 제출 증거는 위에 연결된 기존 원문과 별도 재검증 기록을 사용합니다.
