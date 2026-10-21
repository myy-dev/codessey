# 평가 시연 가이드

## 1. 실습 환경 시작

```bash
docker compose build
docker compose run --rm agent-lab sh
```

## 2. 메모리 Before

RSS 증가와 보호 종료 관찰(기존 증거: 약 5초)

**실행·관제**

```bash
export MEMORY_LIMIT=50 CPU_MAX_OCCUPY=20 MULTI_THREAD_ENABLE=false
./agent-app-leak/agent-leak-app-arm64 > /tmp/agent-demo.log 2>&1 &
LAUNCHER_PID=$!
sleep 1
WORKER_PID=$(pgrep -P "$LAUNCHER_PID")
echo "실행기 PID=$LAUNCHER_PID / 워커 PID=$WORKER_PID"
./scripts/monitor.sh "$WORKER_PID" /dev/null 0.10
```

**앱 메시지 확인**

```bash
cat /tmp/agent-demo.log
```

`Memory limit exceeded`와 `Self-terminating` 메시지 확인 [분석 리포트](reports/oom-report.md)와 비교

**정리 후 다음 단계**

```bash
wait "$LAUNCHER_PID" 2>/dev/null || :
```

## 3. 메모리 After

메모리 한도 50 → 512 12초 관찰 후 관제 중지

**실행·관제**

```bash
export MEMORY_LIMIT=512 CPU_MAX_OCCUPY=20 MULTI_THREAD_ENABLE=false
./agent-app-leak/agent-leak-app-arm64 > /tmp/agent-demo.log 2>&1 &
LAUNCHER_PID=$!
sleep 1
WORKER_PID=$(pgrep -P "$LAUNCHER_PID")
echo "실행기 PID=$LAUNCHER_PID / 워커 PID=$WORKER_PID"
timeout 12s ./scripts/monitor.sh "$WORKER_PID" /dev/null 0.10
```

**앱 메시지 확인**

```bash
ps -p "$WORKER_PID" -o pid,rss,stat,comm
cat /tmp/agent-demo.log
```

Before보다 오래 생존하는지 확인 [분석 리포트](reports/oom-report.md)와 비교

**정리 후 다음 단계**

```bash
kill -TERM "$WORKER_PID"
wait "$LAUNCHER_PID" 2>/dev/null || :
```

## 4. CPU Before

CPU 설정 100 CPU 상승과 보호 종료 관찰(기존 증거: 약 30초, 실행마다 차이)

**실행·관제**

```bash
export MEMORY_LIMIT=512 CPU_MAX_OCCUPY=100 MULTI_THREAD_ENABLE=false
./agent-app-leak/agent-leak-app-arm64 > /tmp/agent-demo.log 2>&1 &
LAUNCHER_PID=$!
sleep 1
WORKER_PID=$(pgrep -P "$LAUNCHER_PID")
echo "실행기 PID=$LAUNCHER_PID / 워커 PID=$WORKER_PID"
./scripts/monitor.sh "$WORKER_PID" /dev/null 0.10
```

**앱 메시지 확인**

```bash
cat /tmp/agent-demo.log
```

`CPU Threshold Violated!` 메시지 확인 [분석 리포트](reports/cpu-report.md)와 비교

**정리 후 다음 단계**

```bash
wait "$LAUNCHER_PID" 2>/dev/null || :
```

## 5. CPU After

CPU 설정 100 → 20 40초 관찰 후 관제 중지

**실행·관제**

```bash
export MEMORY_LIMIT=512 CPU_MAX_OCCUPY=20 MULTI_THREAD_ENABLE=false
./agent-app-leak/agent-leak-app-arm64 > /tmp/agent-demo.log 2>&1 &
LAUNCHER_PID=$!
sleep 1
WORKER_PID=$(pgrep -P "$LAUNCHER_PID")
echo "실행기 PID=$LAUNCHER_PID / 워커 PID=$WORKER_PID"
timeout 40s ./scripts/monitor.sh "$WORKER_PID" /dev/null 0.10
```

**앱 메시지 확인**

```bash
ps -p "$WORKER_PID" -o pid,rss,stat,comm
cat /tmp/agent-demo.log
```

냉각(Starting cooldown) 로그와 관찰 기간 내 생존 확인 [분석 리포트](reports/cpu-report.md)와 비교

**정리 후 다음 단계**

```bash
kill -TERM "$WORKER_PID"
wait "$LAUNCHER_PID" 2>/dev/null || :
```

## 6. 교착상태 Before

멀티스레드 true 14초 관찰 후 관제 중지

**실행·관제**

```bash
export MEMORY_LIMIT=512 CPU_MAX_OCCUPY=20 MULTI_THREAD_ENABLE=true
./agent-app-leak/agent-leak-app-arm64 > /tmp/agent-demo.log 2>&1 &
LAUNCHER_PID=$!
sleep 1
WORKER_PID=$(pgrep -P "$LAUNCHER_PID")
echo "실행기 PID=$LAUNCHER_PID / 워커 PID=$WORKER_PID"
timeout 14s ./scripts/monitor.sh "$WORKER_PID" /dev/null 0.10
```

**앱 메시지 확인**

```bash
ps -p "$WORKER_PID" -o pid,rss,stat,comm
cat /tmp/agent-demo.log
```

WAITING/BLOCKED 이후 로그 무진행과 PID 유지 확인 [분석 리포트](reports/deadlock-report.md)와 비교

**스레드 대기·로그 무진행 확인**

```bash
ps -ef
ps -L -p "$WORKER_PID" -o pid,tid,pcpu,pmem,stat,wchan:24,comm
```

**정리 후 다음 단계**

```bash
kill -TERM "$WORKER_PID"
wait "$LAUNCHER_PID" 2>/dev/null || :
```

## 7. 교착상태 After

멀티스레드 true → false 14초 관찰 후 관제 중지

**실행·관제**

```bash
export MEMORY_LIMIT=512 CPU_MAX_OCCUPY=20 MULTI_THREAD_ENABLE=false
./agent-app-leak/agent-leak-app-arm64 > /tmp/agent-demo.log 2>&1 &
LAUNCHER_PID=$!
sleep 1
WORKER_PID=$(pgrep -P "$LAUNCHER_PID")
echo "실행기 PID=$LAUNCHER_PID / 워커 PID=$WORKER_PID"
timeout 14s ./scripts/monitor.sh "$WORKER_PID" /dev/null 0.10
```

**앱 메시지 확인**

```bash
ps -p "$WORKER_PID" -o pid,rss,stat,comm
cat /tmp/agent-demo.log
```

작업 완료 및 메모리·CPU 작업 로그 갱신 확인 [분석 리포트](reports/deadlock-report.md)와 비교

**정리 후 다음 단계**

```bash
kill -TERM "$WORKER_PID"
wait "$LAUNCHER_PID" 2>/dev/null || :
```

## 8. 시연 종료

```bash
exit
```

`exit` 시 컨테이너와 임시 파일 자동 삭제(`--rm`)
