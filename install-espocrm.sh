#!/usr/bin/env bash
# Установка EspoCRM (Docker) с автоматическим HTTPS на qopq.online.
# Запуск от root:  bash install-espocrm.sh
set -euo pipefail

DOMAIN="qopq.online"
DIR="/opt/espocrm"

# --- Docker, если ещё не стоит ---
if ! command -v docker >/dev/null 2>&1; then
  echo "==> Устанавливаю Docker…"
  curl -fsSL https://get.docker.com | sh
fi

# --- Пароли генерируем на месте, в файлы конфигов они не попадают в открытом виде в репозитории ---
DB_ROOT_PASS=$(openssl rand -hex 16)
DB_PASS=$(openssl rand -hex 16)
ADMIN_PASS=$(openssl rand -base64 12 | tr -d '/+=')

mkdir -p "$DIR"
cd "$DIR"

cat > .env <<EOF
DB_ROOT_PASS=$DB_ROOT_PASS
DB_PASS=$DB_PASS
ADMIN_PASS=$ADMIN_PASS
EOF
chmod 600 .env

cat > Caddyfile <<EOF
$DOMAIN {
    reverse_proxy espocrm:80
}
EOF

cat > docker-compose.yml <<'EOF'
services:
  db:
    image: mariadb:11
    restart: unless-stopped
    environment:
      MARIADB_ROOT_PASSWORD: ${DB_ROOT_PASS}
      MARIADB_DATABASE: espocrm
      MARIADB_USER: espocrm
      MARIADB_PASSWORD: ${DB_PASS}
    volumes:
      - db-data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "healthcheck.sh", "--connect", "--innodb_initialized"]
      interval: 10s
      retries: 10

  espocrm:
    image: espocrm/espocrm
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    environment:
      ESPOCRM_DATABASE_PLATFORM: Mysql
      ESPOCRM_DATABASE_HOST: db
      ESPOCRM_DATABASE_USER: espocrm
      ESPOCRM_DATABASE_PASSWORD: ${DB_PASS}
      ESPOCRM_ADMIN_USERNAME: admin
      ESPOCRM_ADMIN_PASSWORD: ${ADMIN_PASS}
      ESPOCRM_SITE_URL: https://qopq.online
    volumes:
      - espocrm-data:/var/www/html

  daemon:
    image: espocrm/espocrm
    restart: unless-stopped
    depends_on:
      - espocrm
    entrypoint: docker-daemon.sh
    volumes:
      - espocrm-data:/var/www/html

  caddy:
    image: caddy:2
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy-data:/data
      - caddy-config:/config

volumes:
  db-data:
  espocrm-data:
  caddy-data:
  caddy-config:
EOF

echo "==> Запускаю контейнеры…"
docker compose up -d

echo
echo "======================================================"
echo " EspoCRM разворачивается на https://$DOMAIN"
echo " Первый запуск занимает 1–2 минуты (инициализация БД)."
echo
echo " Логин:  admin"
echo " Пароль: $ADMIN_PASS"
echo
echo " Пароли также сохранены в $DIR/.env (chmod 600)."
echo " Статус:  docker compose -f $DIR/docker-compose.yml ps"
echo " Логи:    docker compose -f $DIR/docker-compose.yml logs -f espocrm"
echo "======================================================"
