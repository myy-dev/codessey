#!/usr/bin/env sh
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
LAB_ROOT=${LAB_ROOT:-"$PROJECT_ROOT/.lab"}
AGENT_HOME_VALUE="$LAB_ROOT/agent-home"
LOG_DIR_VALUE="$LAB_ROOT/logs"

mkdir -p "$AGENT_HOME_VALUE/upload_files"
mkdir -p "$AGENT_HOME_VALUE/api_keys"
mkdir -p "$LOG_DIR_VALUE"
printf '%s\n' 'agent_api_key_test' > "$AGENT_HOME_VALUE/api_keys/secret.key"

ENV_FILE="$LAB_ROOT/env.sh"
{
    printf "export AGENT_HOME='%s'\n" "$AGENT_HOME_VALUE"
    printf "export AGENT_UPLOAD_DIR='%s/upload_files'\n" "$AGENT_HOME_VALUE"
    printf "export AGENT_KEY_PATH='%s/api_keys'\n" "$AGENT_HOME_VALUE"
    printf "export AGENT_LOG_DIR='%s'\n" "$LOG_DIR_VALUE"
    printf "export AGENT_PORT='15034'\n"
    printf "export MEMORY_LIMIT='50'\n"
    printf "export CPU_MAX_OCCUPY='20'\n"
    printf "export MULTI_THREAD_ENABLE='true'\n"
} > "$ENV_FILE"

printf 'Lab environment created: %s\n' "$LAB_ROOT"
printf 'Load variables with: . %s\n' "$ENV_FILE"
