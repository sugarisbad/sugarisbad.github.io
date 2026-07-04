# Бот приёма заявок

Telegram-бот, который принимает заявки от клиентов с лендинга: проводит человека
по короткой форме (имя → задача → телефон → почта), а затем присылает владельцу
аккуратно оформленную заявку со всеми контактами клиента — можно ответить в
Telegram, позвонить или написать на почту.

Опционально: если на сервере есть [Ollama](https://ollama.com), бот прогоняет
текст заявки через локальную LLM и прикладывает разбор — суть задачи, подходящая
услуга, срочность и уточняющие вопросы.

## Как выглядит заявка

```
🆕 Новая заявка с сайта

👤 Имя: Иван
🔗 Откуда: Пакет «Настройка VPS»
📝 Задача:
Нужен сервер для интернет-магазина, чтобы не падал...

🤖 Разбор (локальная LLM):
Суть: клиенту нужен отказоустойчивый хостинг магазина
Услуга: настройка VPS + мониторинг
Срочность: средняя
Вопросы: какой движок магазина? какой трафик?

📇 Контакты:
✈ Telegram: @ivan (id 123456789)
📞 Телефон: +7 900 000-00-00
✉ Почта: ivan@mail.ru

🕒 04.07.2026 15:20 МСК
```

## Запуск

1. **Создайте бота**: напишите [@BotFather](https://t.me/BotFather) → `/newbot` →
   придумайте имя и юзернейм (например `sugarisbad_orders_bot`) → получите токен.
2. **Узнайте свой chat id**: спросите у [@userinfobot](https://t.me/userinfobot).
3. **Запустите**:

   ```bash
   cd bot
   python -m venv venv && . venv/bin/activate     # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env                            # впишите BOT_TOKEN и ADMIN_CHAT_ID
   export $(grep -v '^#' .env | xargs)             # или задайте переменные вручную
   python bot.py
   ```

4. **Проверьте**: напишите боту `/start`, пройдите форму — заявка должна
   прийти вам в личку.

## Деплой на сервер (systemd) — одной командой

```bash
git clone https://github.com/sugarisbad/landing.git
cd landing/bot
sudo ./install.sh        # спросит BOT_TOKEN и ADMIN_CHAT_ID, если нет .env
```

Скрипт создаёт служебного пользователя `tgbot`, ставит бота в `/opt/tgbot`
с виртуальным окружением, устанавливает systemd-юнит и запускает сервис.
Повторный запуск скрипта обновляет `bot.py` и перезапускает сервис,
не трогая `.env`.

Управление:

```bash
systemctl status tgbot        # состояние
journalctl -u tgbot -f        # живые логи
sudo systemctl restart tgbot  # перезапуск
```

<details>
<summary>Ручная установка (если не хочется скриптом)</summary>

```bash
sudo useradd -r -s /usr/sbin/nologin tgbot
sudo mkdir -p /opt/tgbot && sudo cp bot.py requirements.txt .env /opt/tgbot/
cd /opt/tgbot && sudo python3 -m venv venv && sudo venv/bin/pip install -r requirements.txt
sudo chown -R tgbot:tgbot /opt/tgbot
sudo cp tgbot.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now tgbot
```
</details>

## Отслеживание источника заявки (deep-links)

Каждая кнопка «Заказать» на сайте ведёт в бота со своим кодом:
`t.me/<бот>?start=vps-setup`, `?start=plan-ai`, `?start=src-cases` и т.д.
Бот расшифровывает код (словарь `SOURCES` в `bot.py`) и добавляет в заявку
строку «🔗 Откуда: …» — видно, какая услуга или страница привела клиента.
Если добавляете услугу на сайт — добавьте её слаг и в `SOURCES`.

## Подключение к сайту

После создания бота впишите ссылку на него в `src/data/site.ts`:

```ts
botUrl: 'https://t.me/<юзернейм_бота>',
```

На странице появится кнопка «🤖 Оставить заявку в боте» в блоке контактов.

## LLM-разбор (опционально)

На сервере с Ollama добавьте в `.env`:

```
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=gemma2
```

Если Ollama недоступна, бот просто пришлёт заявку без блока «Разбор» —
доставка заявки никогда не зависит от LLM.
