FROM ubuntu:24.04

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends procps \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --user-group appuser

WORKDIR /app
COPY agent-app-leak/agent-leak-app-arm64 /app/agent-app-leak/
COPY scripts/monitor.sh /app/scripts/
RUN chmod +x /app/agent-app-leak/agent-leak-app-arm64 /app/scripts/monitor.sh \
    && mkdir -p /app/.lab/manual /tmp/agent-home/upload_files /tmp/agent-home/api_keys /tmp/agent-logs \
    && printf '%s\n' 'agent_api_key_test' > /tmp/agent-home/api_keys/secret.key \
    && chown -R appuser:appuser /app/.lab /tmp/agent-home /tmp/agent-logs

ENV AGENT_HOME=/tmp/agent-home \
    AGENT_UPLOAD_DIR=/tmp/agent-home/upload_files \
    AGENT_KEY_PATH=/tmp/agent-home/api_keys \
    AGENT_LOG_DIR=/tmp/agent-logs \
    AGENT_PORT=15034

USER appuser
CMD ["/app/agent-app-leak/agent-leak-app-arm64"]
