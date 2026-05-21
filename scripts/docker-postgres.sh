#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="gizigo-pg"
PORT="5433"
USER="gizigo"
PASSWORD="devpw"
DB="gizigo"
IMAGE="postgres:16"

cmd="${1:-up}"

case "$cmd" in
    up)
        if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
            echo "==> ${CONTAINER_NAME} already running on :${PORT}"
            exit 0
        fi
        if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
            echo "==> Starting existing ${CONTAINER_NAME}"
            docker start "${CONTAINER_NAME}" >/dev/null
        else
            echo "==> Creating ${CONTAINER_NAME} on :${PORT}"
            docker run -d \
                --name "${CONTAINER_NAME}" \
                -p "127.0.0.1:${PORT}:5432" \
                -e "POSTGRES_PASSWORD=${PASSWORD}" \
                -e "POSTGRES_USER=${USER}" \
                -e "POSTGRES_DB=${DB}" \
                "${IMAGE}" >/dev/null
        fi
        echo "==> Postgres ready at postgresql://${USER}:${PASSWORD}@127.0.0.1:${PORT}/${DB}"
        ;;
    down)
        echo "==> Stopping ${CONTAINER_NAME}"
        docker stop "${CONTAINER_NAME}" >/dev/null 2>&1 || true
        ;;
    nuke)
        echo "==> Removing ${CONTAINER_NAME}"
        docker stop "${CONTAINER_NAME}" >/dev/null 2>&1 || true
        docker rm "${CONTAINER_NAME}" >/dev/null 2>&1 || true
        ;;
    *)
        echo "Usage: $0 {up|down|nuke}" >&2
        exit 1
        ;;
esac
