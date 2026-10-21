#!/usr/bin/env sh
# 명령 실패(-e)·미설정 변수 사용(-u) 시 종료
set -eu

# 사용 예: ./scripts/monitor.sh 123 .lab/manual/test-monitor.log 0.10
# 입력: 워커 PID, 출력 파일, 대기 시간(선택, 기본 1초)
if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
    echo "Usage: $0 <pid> <output-file> [interval-seconds]" >&2
    exit 2
fi

PID=$1
OUTPUT_FILE=$2
INTERVAL=${3:-1}

# 출력 디렉터리 생성 및 로그 초기화(기존 내용 삭제)
mkdir -p "$(dirname -- "$OUTPUT_FILE")"
: > "$OUTPUT_FILE"

PREVIOUS_TICKS=""
PREVIOUS_WALL=""
TICKS_PER_SECOND=$(getconf CLK_TCK)

# kill -0: 종료 신호 없이 프로세스 존재·신호 권한 확인
while kill -0 "$PID" 2>/dev/null; do
    # rss: 상주 메모리, vsz: 가상 메모리(각 KiB)
    # stat: 상태, nlwp: 스레드 수, comm: 프로세스 이름('='은 제목 생략)
    PROCESS_ROW=$(ps -p "$PID" -o rss= -o vsz= -o stat= -o nlwp= -o comm= 2>/dev/null) || break
    if [ -z "$PROCESS_ROW" ]; then
        break
    fi

    read -r RSS_KB VSZ_KB STATE THREADS PROCESS <<EOF
$PROCESS_ROW
EOF
    # stat 14·15번째 필드: 사용자·커널 영역의 누적 CPU tick(이름에 공백 없음 전제)
    CURRENT_TICKS=$(awk '{ print $14 + $15 }' "/proc/$PID/stat" 2>/dev/null) || break
    # uptime 첫 필드: 부팅 후 경과 시간(초)
    CURRENT_WALL=$(awk '{ print $1 }' /proc/uptime)
    # 첫 샘플: 비교값 부재로 0.0 기록(무부하 판정 아님)
    CPU="0.0"
    if [ -n "$PREVIOUS_TICKS" ] && [ -n "$PREVIOUS_WALL" ]; then
        # 구간 CPU(%) = (tick 증가량 / 초당 tick 수) / 경과 초 × 100
        # 코어 1개 사용 기준 100%(ps의 수명 평균과 구분)
        CPU=$(awk \
            -v current="$CURRENT_TICKS" \
            -v previous="$PREVIOUS_TICKS" \
            -v ticks="$TICKS_PER_SECOND" \
            -v current_wall="$CURRENT_WALL" \
            -v previous_wall="$PREVIOUS_WALL" \
            'BEGIN {
                elapsed = current_wall - previous_wall
                if (elapsed <= 0) elapsed = 0.001
                printf "%.1f", ((current - previous) / ticks / elapsed) * 100
            }')
    fi
    PREVIOUS_TICKS=$CURRENT_TICKS
    PREVIOUS_WALL=$CURRENT_WALL
    # 메모리 단위 변환: KiB → MiB(출력 표기는 MB)
    RSS_MB=$(awk -v value="$RSS_KB" 'BEGIN { printf "%.1f", value / 1024 }')
    VSZ_MB=$(awk -v value="$VSZ_KB" 'BEGIN { printf "%.1f", value / 1024 }')
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    # 화면 출력 및 파일 추가 기록(tee -a)
    printf '[%s] PROCESS:%s PID:%s CPU:%s%% RSS:%sMB VSZ:%sMB STATE:%s THREADS:%s\n' \
        "$TIMESTAMP" "$PROCESS" "$PID" "$CPU" "$RSS_MB" "$VSZ_MB" "$STATE" "$THREADS" \
        | tee -a "$OUTPUT_FILE"
    # 실제 측정 간격: 대기 시간 + 측정 명령 실행 시간
    sleep "$INTERVAL"
done
