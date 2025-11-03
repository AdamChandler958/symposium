#!/bin/bash

echo "Tearing down symposium..."
docker compose -f ~/symposium/infra/docker-compose.yml -p symposium down processing-service fetching-service discord-api