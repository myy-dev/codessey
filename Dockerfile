FROM python:3.13-slim

ARG APP_UID=10001
ARG APP_GID=10001

RUN apt-get update \
    && apt-get install -y --no-install-recommends procps \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid "${APP_GID}" appuser \
    && useradd --uid "${APP_UID}" --gid "${APP_GID}" --create-home appuser

WORKDIR /app
COPY . /app
RUN chmod +x /app/bin/* /app/scripts/*.sh /app/scripts/*.py \
    && mkdir -p /tmp/agent-home/upload_files /tmp/agent-home/api_keys /tmp/agent-logs \
    && printf '%s\n' 'agent_api_key_test' > /tmp/agent-home/api_keys/secret.key \
    && chown -R appuser:appuser /app /tmp/agent-home /tmp/agent-logs

ENV PYTHONPATH=/app/src \
    AGENT_HOME=/tmp/agent-home \
    AGENT_UPLOAD_DIR=/tmp/agent-home/upload_files \
    AGENT_LOG_DIR=/tmp/agent-logs \
    AGENT_PORT=15034 \
    MEMORY_LIMIT=50 \
    CPU_MAX_OCCUPY=20 \
    MULTI_THREAD_ENABLE=true \
    AGENT_SCENARIO=normal

EXPOSE 15034
USER appuser
ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]
CMD ["python3", "-m", "agent_leak_app"]
