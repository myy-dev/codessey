#!/usr/bin/env sh
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
ARCHITECTURE=$(uname -m)

case "$ARCHITECTURE" in
    x86_64|amd64)
        BINARY="$PROJECT_ROOT/bin/agent-app-leak-x86"
        ;;
    arm64|aarch64)
        BINARY="$PROJECT_ROOT/bin/agent-app-leak-arm64"
        ;;
    *)
        echo "Unsupported architecture: $ARCHITECTURE" >&2
        exit 2
        ;;
esac

printf 'Selected binary wrapper: %s (%s)\n' "$BINARY" "$ARCHITECTURE" >&2
exec "$BINARY" "$@"
