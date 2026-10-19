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
TICKS_PER_SECOND=$(getconf CLK_TCK)

while kill -0 "$PID" 2>/dev/null; do
    PROCESS_ROW=$(ps -p "$PID" -o rss= -o vsz= -o stat= -o nlwp= -o comm= 2>/dev/null) || break
    if [ -z "$PROCESS_ROW" ]; then
        break
    fi

    read -r RSS_KB VSZ_KB STATE THREADS PROCESS <<EOF
$PROCESS_ROW
EOF
    CURRENT_TICKS=$(awk '{ print $14 + $15 }' "/proc/$PID/stat" 2>/dev/null) || break
    CURRENT_WALL=$(awk '{ print $1 }' /proc/uptime)
    CPU="0.0"
    if [ -n "$PREVIOUS_TICKS" ] && [ -n "$PREVIOUS_WALL" ]; then
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
    RSS_MB=$(awk -v value="$RSS_KB" 'BEGIN { printf "%.1f", value / 1024 }')
    VSZ_MB=$(awk -v value="$VSZ_KB" 'BEGIN { printf "%.1f", value / 1024 }')
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    printf '[%s] PROCESS:%s PID:%s CPU:%s%% RSS:%sMB VSZ:%sMB STATE:%s THREADS:%s\n' \
        "$TIMESTAMP" "$PROCESS" "$PID" "$CPU" "$RSS_MB" "$VSZ_MB" "$STATE" "$THREADS" \
        | tee -a "$OUTPUT_FILE"
    sleep "$INTERVAL"
done
