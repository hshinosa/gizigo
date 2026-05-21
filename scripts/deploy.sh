#!/usr/bin/env bash
set -euo pipefail

REMOTE_HOST="${REMOTE_HOST:-vpsgw}"
REMOTE_PATH="/opt/gizigo"
DOMAIN="gizigo.jmola.my.id"
PG_PORT="5434"
PG_PASSWORD="${PG_PASSWORD:-$(openssl rand -hex 24)}"

echo "==> Building web bundle"
( cd apps/web && pnpm vite build )

echo "==> Rsyncing source to ${REMOTE_HOST}:${REMOTE_PATH}"
rsync -avz --delete \
  --exclude '.git' \
  --exclude '.venv' \
  --exclude 'node_modules' \
  --exclude 'dist' \
  --exclude '__pycache__' \
  --exclude '.pytest_cache' \
  --exclude '.ruff_cache' \
  --exclude 'submission-bundle' \
  --exclude '*.log' \
  ./ "${REMOTE_HOST}:${REMOTE_PATH}/"

echo "==> Rsyncing built web bundle to /var/www/gizigo"
rsync -avz --delete apps/web/dist/ "${REMOTE_HOST}:/var/www/gizigo/"

echo "==> Remote: postgres + venv + systemd + nginx"
ssh "${REMOTE_HOST}" \
  REMOTE_PATH="${REMOTE_PATH}" \
  DOMAIN="${DOMAIN}" \
  PG_PORT="${PG_PORT}" \
  PG_PASSWORD="${PG_PASSWORD}" \
  bash -s <<'REMOTE'
set -euo pipefail

if ! docker ps --format '{{.Names}}' | grep -q '^gizigo-pg$'; then
  if docker ps -a --format '{{.Names}}' | grep -q '^gizigo-pg$'; then
    docker rm -f gizigo-pg
  fi
  docker run -d \
    --name gizigo-pg \
    --restart unless-stopped \
    -p 127.0.0.1:${PG_PORT}:5432 \
    -e POSTGRES_PASSWORD="${PG_PASSWORD}" \
    -e POSTGRES_USER=gizigo \
    -e POSTGRES_DB=gizigo \
    -v /var/lib/gizigo-pg:/var/lib/postgresql/data \
    postgres:16
  echo "Waiting for postgres ready..."
  sleep 8
fi
docker exec -i gizigo-pg psql -U gizigo -d gizigo < ${REMOTE_PATH}/scripts/db-init.sql

if [ ! -d "${REMOTE_PATH}/services/api/.venv" ]; then
  python3 -m venv "${REMOTE_PATH}/services/api/.venv"
fi
"${REMOTE_PATH}/services/api/.venv/bin/pip" install --quiet --upgrade pip wheel
"${REMOTE_PATH}/services/api/.venv/bin/pip" install --quiet -e "${REMOTE_PATH}/services/api"

cat > "${REMOTE_PATH}/services/api/.env" <<ENVEOF
OPENAI_BASE_URL=http://43.228.214.145:8317/v1
OPENAI_API_KEY=sk-ama
OPENAI_MODEL=gpt-5.4-mini
DATABASE_URL=postgresql://gizigo:${PG_PASSWORD}@127.0.0.1:${PG_PORT}/gizigo
CORS_ALLOWED_ORIGIN=https://${DOMAIN}
HUMANIZER_LLM_ENABLED=false
API_HOST=127.0.0.1
API_PORT=8001
LOG_LEVEL=info
ENVEOF
chmod 600 "${REMOTE_PATH}/services/api/.env"

cp "${REMOTE_PATH}/scripts/gizigo-api.service" /etc/systemd/system/gizigo-api.service
systemctl daemon-reload
systemctl enable --now gizigo-api.service
sleep 3
systemctl status gizigo-api --no-pager --lines=5 || true

mkdir -p /var/www/letsencrypt
mkdir -p /var/www/gizigo

if [ ! -d /etc/letsencrypt/live/${DOMAIN} ]; then
  cat > /etc/nginx/sites-available/gizigo-temp.conf <<NGINXEOF
server {
    listen 80;
    server_name ${DOMAIN};
    location /.well-known/acme-challenge/ { root /var/www/letsencrypt; }
    location / { return 200 "GiziGo bootstrapping..."; }
}
NGINXEOF
  ln -sf /etc/nginx/sites-available/gizigo-temp.conf /etc/nginx/sites-enabled/gizigo-temp.conf
  nginx -t && systemctl reload nginx
  /snap/bin/certbot certonly --webroot -w /var/www/letsencrypt \
    -d ${DOMAIN} --non-interactive --agree-tos -m hshino@${DOMAIN#*.} \
    --preferred-challenges http
  rm -f /etc/nginx/sites-enabled/gizigo-temp.conf /etc/nginx/sites-available/gizigo-temp.conf
fi

cp "${REMOTE_PATH}/scripts/nginx-gizigo.conf" /etc/nginx/sites-available/gizigo.conf
ln -sf /etc/nginx/sites-available/gizigo.conf /etc/nginx/sites-enabled/gizigo.conf
nginx -t && systemctl reload nginx

echo
echo "==> Health check via local proxy..."
curl -sSf http://127.0.0.1:8001/v1/health | head -c 300 || echo "API not responding"
echo
echo "==> Health check via https..."
curl -sSfk https://${DOMAIN}/v1/health | head -c 300 || true
echo
echo "==> DONE"
REMOTE
