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
2. **Узнайте свой chat id**: запустите бота (шаг 3) и напишите ему `/id`,
   либо спросите у @userinfobot заранее.
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

## Деплой на сервер (systemd)

```bash
sudo useradd -r -s /usr/sbin/nologin tgbot
sudo mkdir -p /opt/tgbot && sudo cp bot.py requirements.txt .env /opt/tgbot/
cd /opt/tgbot && sudo python3 -m venv venv && sudo venv/bin/pip install -r requirements.txt
sudo chown -R tgbot:tgbot /opt/tgbot
sudo cp tgbot.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now tgbot
systemctl status tgbot
```

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
