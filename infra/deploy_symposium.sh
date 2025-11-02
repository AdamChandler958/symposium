#!/bin/bash

echo "Checking for Docker Engine readiness..."
MAX_WAIT_SECONDS=60
SLEEP_INTERVAL=5
ELAPSED_TIME=0

while ! docker info > /dev/null 2>&1; do
    if [ "$ELAPSED_TIME" -ge "$MAX_WAIT_SECONDS" ]; then
        echo "Error: Docker Engine did not start within $MAX_WAIT_SECONDS seconds. Aborting deployment."
        exit 1
    fi
    echo "Docker not ready yet. Waiting ${SLEEP_INTERVAL}s..."
    sleep $SLEEP_INTERVAL
    ELAPSED_TIME=$((ELAPSED_TIME + SLEEP_INTERVAL))
done

echo "Docker Engine is ready! Proceeding with deployment."

echo "Deploying symposium..."
docker compose -f ~/symposium/infra/docker-compose.yml pull promtail loki grafana
docker compose -f ~/symposium/infra/docker-compose.yml -p symposium up -d --build processing-service fetching-service discord-api