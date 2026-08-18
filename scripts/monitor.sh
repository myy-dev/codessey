#!/usr/bin/env sh
set -eu

if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
    echo "Usage: $0 <pid> <output-file> [interval-seconds]" >&2
    exit 2
fi

PID=$1
OUTPUT_FILE=$2
INTERVAL=${3:-1}

mkdir -p "$(dirname -- "$OUTPUT_FILE")"
: > "$OUTPUT_FILE"

PREVIOUS_TICKS=""
PREVIOUS_WALL=""
TICKS_PER_SECOND=$(getconf CLK_TCK 2>/dev/null || printf '100')

thread_count() {
    if [ -d "/proc/$PID/task" ]; then
        find "/proc/$PID/task" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' '
    else
        ps -M -p "$PID" 2>/dev/null | awk 'NR > 1 { count++ } END { print count + 0 }'
    fi
}

while kill -0 "$PID" 2>/dev/null; do
    PROCESS_ROW=$(ps -p "$PID" -o %cpu= -o rss= -o vsz= -o stat= -o comm= 2>/dev/null || true)
    if [ -z "$PROCESS_ROW" ]; then
        break
    fi

    CPU=$(printf '%s\n' "$PROCESS_ROW" | awk '{ print $1 }')
    if [ -r "/proc/$PID/stat" ]; then
        CURRENT_TICKS=$(awk '{ print $14 + $15 }' "/proc/$PID/stat" 2>/dev/null || true)
        CURRENT_WALL=$(awk '{ print $1 }' /proc/uptime 2>/dev/null || true)
        if [ -n "$PREVIOUS_TICKS" ] && [ -n "$CURRENT_TICKS" ] && [ -n "$PREVIOUS_WALL" ] && [ -n "$CURRENT_WALL" ]; then
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
        else
            CPU="0.0"
        fi
        PREVIOUS_TICKS=$CURRENT_TICKS
        PREVIOUS_WALL=$CURRENT_WALL
    fi
    RSS_KB=$(printf '%s\n' "$PROCESS_ROW" | awk '{ print $2 }')
    VSZ_KB=$(printf '%s\n' "$PROCESS_ROW" | awk '{ print $3 }')
    STATE=$(printf '%s\n' "$PROCESS_ROW" | awk '{ print $4 }')
    PROCESS=$(printf '%s\n' "$PROCESS_ROW" | awk '{ print $5 }')
    RSS_MB=$(awk -v value="$RSS_KB" 'BEGIN { printf "%.1f", value / 1024 }')
    VSZ_MB=$(awk -v value="$VSZ_KB" 'BEGIN { printf "%.1f", value / 1024 }')
    THREADS=$(thread_count)
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    printf '[%s] PROCESS:%s PID:%s CPU:%s%% RSS:%sMB VSZ:%sMB STATE:%s THREADS:%s\n' \
        "$TIMESTAMP" "$PROCESS" "$PID" "$CPU" "$RSS_MB" "$VSZ_MB" "$STATE" "$THREADS" \
        | tee -a "$OUTPUT_FILE"
    sleep "$INTERVAL"
done
