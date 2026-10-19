# 평가 시연 가이드

## 1. 실습 환경 시작

호스트의 프로젝트 폴더에서 실행합니다.

```bash
docker compose build
docker compose run --name b4-2-lab agent-lab sh
```

이후 명령은 컨테이너 내부에서 실행합니다.

```bash
mkdir -p .lab/manual
```

실행 환경과 부트 조건은 [시연 환경](EVIDENCE.md#시연-환경)을 참고합니다.

## 2. 시연 조건 선택

아래에서 **한 줄만 선택**한 뒤 3~5번을 진행합니다.

메모리: [분석 리포트](reports/oom-report.md)

```bash
export CASE=oom-before MEMORY_LIMIT=50 CPU_MAX_OCCUPY=20 MULTI_THREAD_ENABLE=false
export CASE=oom-after MEMORY_LIMIT=512 CPU_MAX_OCCUPY=20 MULTI_THREAD_ENABLE=false
```

CPU: [분석 리포트](reports/cpu-report.md)

```bash
export CASE=cpu-before MEMORY_LIMIT=512 CPU_MAX_OCCUPY=100 MULTI_THREAD_ENABLE=false
export CASE=cpu-after MEMORY_LIMIT=512 CPU_MAX_OCCUPY=20 MULTI_THREAD_ENABLE=false
```

교착상태: [분석 리포트](reports/deadlock-report.md)

```bash
export CASE=deadlock-before MEMORY_LIMIT=512 CPU_MAX_OCCUPY=20 MULTI_THREAD_ENABLE=true
export CASE=deadlock-after MEMORY_LIMIT=512 CPU_MAX_OCCUPY=20 MULTI_THREAD_ENABLE=false
```

## 3. 앱 실행과 관제

```bash
RUN_LOG=".lab/manual/$CASE-run.log"
STARTED_AT=$(date +%s.%N)
printf 'START case=%s time=%s memory=%s cpu=%s multi=%s\n' \
  "$CASE" "$STARTED_AT" "$MEMORY_LIMIT" "$CPU_MAX_OCCUPY" "$MULTI_THREAD_ENABLE" > "$RUN_LOG"
./agent-app-leak/agent-leak-app-arm64 > ".lab/manual/$CASE.log" 2>&1 &
LAUNCHER_PID=$!
sleep 1
WORKER_PID=$(pgrep -P "$LAUNCHER_PID")
printf 'launcher=%s worker=%s\n' "$LAUNCHER_PID" "$WORKER_PID" | tee -a "$RUN_LOG"
./scripts/monitor.sh "$WORKER_PID" ".lab/manual/$CASE-monitor.log" 0.10 &
MONITOR_PID=$!
```

PID 구분과 관제 수치 해석은 [관제 및 종료 상태](EVIDENCE.md#관제-및-종료-상태)를 참고합니다.

## 4. 장애와 조치 결과 확인

**메모리·CPU Before** — 앱의 보호 종료까지 대기합니다.

```bash
wait "$LAUNCHER_PID"
EXIT_STATUS=$?
FINISHED_AT=$(date +%s.%N)
ELAPSED=$(awk -v start="$STARTED_AT" -v end="$FINISHED_AT" 'BEGIN { printf "%.3f", end-start }')
printf 'END time=%s elapsed_seconds=%s exit=%s cleanup=none\n' \
  "$FINISHED_AT" "$ELAPSED" "$EXIT_STATUS" | tee -a "$RUN_LOG"
wait "$MONITOR_PID"
cat ".lab/manual/$CASE.log"
tail ".lab/manual/$CASE-monitor.log"
```

**After·교착상태 Before** — 아래 시간만큼 관찰합니다.

| 조건 | 대기 명령 |
| --- | --- |
| 메모리 After | `sleep 12` |
| CPU After | `sleep 40` |
| 교착상태 Before·After | `sleep 14` |

```bash
tail ".lab/manual/$CASE.log"
ps -p "$WORKER_PID" -o pid,pcpu,rss,stat,comm
tail ".lab/manual/$CASE-monitor.log"
```

교착상태 Before에서는 종료 전에 스레드 상태도 수집합니다.

```bash
{
  ps -ef
  ps -L -p "$WORKER_PID" -o pid,tid,pcpu,pmem,stat,wchan:24,comm
} > .lab/manual/deadlock-before-ps.txt
cat .lab/manual/deadlock-before-ps.txt
```

비교 기준: [장애별 증거](EVIDENCE.md#장애별-증거)

## 5. 관측 후 앱 정리

After·교착상태 Before에서 증거 수집을 마친 뒤 실행합니다.

```bash
printf 'CLEANUP time=%s signal=SIGTERM worker=%s\n' "$(date +%s.%N)" "$WORKER_PID" | tee -a "$RUN_LOG"
kill -TERM "$WORKER_PID"
wait "$LAUNCHER_PID"
EXIT_STATUS=$?
FINISHED_AT=$(date +%s.%N)
ELAPSED=$(awk -v start="$STARTED_AT" -v end="$FINISHED_AT" 'BEGIN { printf "%.3f", end-start }')
printf 'END time=%s elapsed_seconds=%s exit=%s cleanup=external-SIGTERM\n' \
  "$FINISHED_AT" "$ELAPSED" "$EXIT_STATUS" | tee -a "$RUN_LOG"
wait "$MONITOR_PID"
```

다음 조건은 2번부터 반복합니다.

## 6. 로그 보관과 시연 종료

컨테이너 내부에서 실행합니다.

```bash
exit
```

이후 명령은 호스트에서 실행합니다.

```bash
mkdir -p .lab
docker cp b4-2-lab:/app/.lab/manual .lab/
docker rm b4-2-lab
```

로그 보관·기록 기준은 [해석 기준](EVIDENCE.md#해석-기준)을 참고합니다.
