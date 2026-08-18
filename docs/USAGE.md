# 실습 실행 가이드

이 문서는 `agent-leak-app`의 부트 조건을 준비하고 OOM, CPU 과점유, Deadlock을 직접 재현하는 방법을 설명합니다.

## 1. Docker로 전체 실험 실행

Docker Desktop 또는 Docker Engine이 실행 중이어야 합니다.

```bash
make docker-build
make docker-test
make docker-evidence
```

`make docker-evidence`는 비루트 사용자로 Linux 컨테이너를 실행하고 다음 결과를 생성합니다.

- `evidence/generated/`: 애플리케이션 로그, `monitor.sh` 로그, `ps`/`ps -L` 출력, 요약 JSON, SHA-256 매니페스트
- `evidence/charts/`: 실제 관제 로그로 만든 SVG 그래프

## 2. 호스트에서 환경 준비

Linux 또는 macOS에서 Python 3.11 이상을 사용할 수 있습니다. 제출용 증거는 Linux 컨테이너 실행 결과를 사용합니다.

```bash
make setup
. .lab/env.sh
```

생성되는 기본 환경변수는 다음과 같습니다.

```text
AGENT_HOME=.lab/agent-home
AGENT_UPLOAD_DIR=$AGENT_HOME/upload_files
AGENT_KEY_PATH=$AGENT_HOME/api_keys
AGENT_LOG_DIR=.lab/logs
AGENT_PORT=15034
MEMORY_LIMIT=50
CPU_MAX_OCCUPY=20
MULTI_THREAD_ENABLE=true
```

`$AGENT_HOME/api_keys/secret.key`에는 테스트 키 `agent_api_key_test`가 생성됩니다.

## 3. 수동 장애 재현

### 메모리 누수/OOM

```bash
AGENT_SCENARIO=memory MEMORY_LIMIT=50 AGENT_RUN_SECONDS=2 ./bin/agent-leak-app
```

다른 터미널에서 PID를 찾아 관제합니다.

```bash
PID=$(pgrep -f 'python3 -m agent_leak_app' | head -1)
./scripts/monitor.sh "$PID" .lab/oom-monitor.log 0.5
```

임계값을 올려 비교합니다.

```bash
AGENT_SCENARIO=memory MEMORY_LIMIT=128 AGENT_RUN_SECONDS=1 ./bin/agent-leak-app
```

### CPU 과점유

```bash
AGENT_SCENARIO=cpu CPU_MAX_OCCUPY=20 CPU_LOAD_PERCENT=75 ./bin/agent-leak-app
AGENT_SCENARIO=cpu CPU_MAX_OCCUPY=95 CPU_LOAD_PERCENT=75 ./bin/agent-leak-app
```

첫 실행은 Watchdog이 `SIGTERM` 보호 조치를 수행합니다. 두 번째 실행은 같은 부하에서 임계값을 초과하지 않아 정상 완료됩니다.

### Deadlock

```bash
AGENT_SCENARIO=deadlock MULTI_THREAD_ENABLE=true ./bin/agent-leak-app
```

다른 터미널에서 프로세스와 스레드 상태를 확인합니다.

```bash
PID=$(pgrep -f 'python3 -m agent_leak_app' | head -1)
ps -ef | grep agent_leak_app
ps -L -p "$PID" -o pid,tid,pcpu,pmem,stat,comm
```

실습 프로세스를 종료한 뒤 멀티스레드를 비활성화하여 회피 결과를 비교합니다.

```bash
kill "$PID"
AGENT_SCENARIO=deadlock MULTI_THREAD_ENABLE=false ./bin/agent-leak-app
```

## 4. 부트 실패 확인

필수 설정이 잘못되면 애플리케이션은 실행 전에 종료 코드 `2`와 원인을 출력합니다.

```bash
AGENT_PORT=15035 ./bin/agent-leak-app
# >>> [BOOT] FAILED: AGENT_PORT must be 15034 <<<
```

다음 조건을 모두 검증합니다.

- 비루트 사용자
- 필수 환경변수 존재
- 업로드·키·로그 디렉터리 존재
- 로그 디렉터리 쓰기 권한
- `secret.key` 존재 및 내용
- `AGENT_PORT=15034`
- `MEMORY_LIMIT=50~512`
- `CPU_MAX_OCCUPY=10~100`
- `MULTI_THREAD_ENABLE` 허용 값
- `0.0.0.0:15034` 실제 바인딩

## 5. 종료 코드

| 종료 코드 | 의미 |
| --- | --- |
| `0` | 정상 완료 또는 설정 변경 후 장애 회피 |
| `2` | 부트 조건 검증 또는 포트 바인딩 실패 |
| `137` | MemoryGuard가 메모리 임계값 초과를 감지하여 종료 |
| `143` | Watchdog이 CPU 임계값 초과를 감지하여 `SIGTERM` 종료 |

Deadlock 재현 프로세스는 의도적으로 종료되지 않습니다. 자동 실험기는 1.5초 동안 PID와 정체 상태를 관찰한 뒤 `SIGTERM`으로 정리합니다.
