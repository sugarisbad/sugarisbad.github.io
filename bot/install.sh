#!/usr/bin/env bash
# Установка бота заявок как systemd-сервиса (Debian/Ubuntu).
#
#   git clone https://github.com/sugarisbad/landing.git
#   cd landing/bot
#   sudo ./install.sh
#
# Скрипт идемпотентен: повторный запуск обновит bot.py и перезапустит сервис,
# не трогая существующий /opt/tgbot/.env.
set -euo pipefail

DIR=/opt/tgbot
SRC="$(cd "$(dirname "$0")" && pwd)"

[ "$(id -u)" -eq 0 ] || { echo "Запустите через sudo: sudo ./install.sh"; exit 1; }

command -v python3 >/dev/null || { echo "Нужен python3: apt install -y python3"; exit 1; }
python3 -m venv --help >/dev/null 2>&1 || { echo "Нужен venv: apt install -y python3-venv"; exit 1; }

# служебный пользователь без шелла
id tgbot &>/dev/null || useradd -r -s /usr/sbin/nologin tgbot

mkdir -p "$DIR"
cp "$SRC/bot.py" "$SRC/requirements.txt" "$DIR/"

# .env: берём готовый рядом со скриптом, иначе спрашиваем
if [ ! -f "$DIR/.env" ]; then
  if [ -f "$SRC/.env" ]; then
    cp "$SRC/.env" "$DIR/.env"
  else
    read -rp "BOT_TOKEN: " token
    read -rp "ADMIN_CHAT_ID: " chat
    printf 'BOT_TOKEN=%s\nADMIN_CHAT_ID=%s\n' "$token" "$chat" > "$DIR/.env"
  fi
fi
chmod 600 "$DIR/.env"

[ -d "$DIR/venv" ] || python3 -m venv "$DIR/venv"
"$DIR/venv/bin/pip" install -q --upgrade pip
"$DIR/venv/bin/pip" install -q -r "$DIR/requirements.txt"

chown -R tgbot:tgbot "$DIR"

cp "$SRC/tgbot.service" /etc/systemd/system/tgbot.service
systemctl daemon-reload
systemctl enable tgbot
systemctl restart tgbot

echo
echo "Готово. Проверка:"
echo "  systemctl status tgbot     — состояние сервиса"
echo "  journalctl -u tgbot -f     — живые логи"
echo "Теперь напишите боту /start и пройдите форму — заявка придёт вам в личку."
