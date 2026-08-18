#!/usr/bin/env sh
set -eu

: "${AGENT_KEY_PATH:=/tmp/agent-home/api_keys}"
export AGENT_KEY_PATH

exec "$@"
