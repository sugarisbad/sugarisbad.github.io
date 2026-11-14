"""Фоновая доставка, напоминания, бэкапы и ограниченные по размеру логи."""

import asyncio
import json
import logging
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from delivery import deliver, message_jobs

log = logging.getLogger("orders-bot")


def configure_logging(directory: str, token: str):
    Path(directory).mkdir(parents=True, exist_ok=True)

    class RedactedFormatter(logging.Formatter):
        def format(self, record):
            return super().format(record).replace(token, "[BOT_TOKEN]")

    handler = RotatingFileHandler(
        Path(directory) / "bot.log", maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8",
    )
    handler.setFormatter(RedactedFormatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)


async def deliver_once(store, bot):
    for row in store.due():
        try:
            payload = json.loads(row["payload"])
            reminder = payload.pop("_reminder", None)
            if reminder:
                current = store.db.execute(
                    "SELECT next_reminder FROM followups WHERE user_id=?", (reminder["user"],)
                ).fetchone()
                if not current or current["next_reminder"] != reminder["next"]:
                    store.delivered(row)
                    continue
            await deliver(bot, payload)
        except TelegramRetryAfter as error:
            store.delivery_failed(row, str(error), error.retry_after + 1)
        except (TelegramBadRequest, TelegramForbiddenError) as error:
            store.delivery_failed(row, str(error), 0, permanent=True)
            log.warning("Доставка #%s требует внимания: %s", row["id"], error)
        except Exception as error:
            delay = min(3600, 5 * 2 ** min(row["attempts"], 10))
            store.delivery_failed(row, str(error), delay)
            log.warning("Доставка #%s отложена на %s сек.: %s", row["id"], delay, error)
        else:
            store.delivered(row)


async def delivery_loop(store, bot):
    while True:
        try:
            await deliver_once(store, bot)
        except Exception:
            log.exception("Ошибка обработчика очереди")
        await asyncio.sleep(1)


def schedule_reminders(store, admin_id: int, repeat_seconds: int, now=None):
    now = time.time() if now is None else now
    rows = store.db.execute(
        "SELECT * FROM followups WHERE next_reminder<=? ORDER BY next_reminder LIMIT 20", (now,)
    ).fetchall()
    for row in rows:
        lead_id = row["lead_id"]
        title = f"заявке #{lead_id}" if lead_id else f"клиенту {row['user_id']}"
        markup_rows = [[InlineKeyboardButton(text="✍️ Ответить", callback_data=f"re:{row['user_id']}")]]
        if lead_id:
            markup_rows[0].append(InlineKeyboardButton(text="📋 Заявка", callback_data=f"adm:lead:{lead_id}"))
        markup_rows.append([
            InlineKeyboardButton(text="Через 1 час", callback_data=f"adm:snooze:{row['user_id']}:1"),
            InlineKeyboardButton(text="Завтра", callback_data=f"adm:snooze:{row['user_id']}:24"),
        ])
        with store.db:
            jobs = message_jobs(admin_id, f"⏰ Нужен ответ по {title}.",
                                InlineKeyboardMarkup(inline_keyboard=markup_rows))
            jobs[0]["_reminder"] = {"user": row["user_id"], "next": now + repeat_seconds}
            store.enqueue(jobs, f"reminder:{row['user_id']}:{row['next_reminder']}")
            store.db.execute("UPDATE followups SET next_reminder=? WHERE user_id=?",
                             (now + repeat_seconds, row["user_id"]))


async def maintenance_loop(store, admin_id: int, backup_dir: str, backup_keep: int, repeat_seconds: int):
    last_backup = None
    last_cleanup = 0
    while True:
        try:
            schedule_reminders(store, admin_id, repeat_seconds)
            today = datetime.now().date()
            if today != last_backup:
                path = await asyncio.to_thread(store.backup, backup_dir, backup_keep)
                log.info("Резервная копия проверена: %s", path)
                last_backup = today
            if time.time() - last_cleanup > 86400:
                with store.db:
                    store.db.execute("DELETE FROM outbox WHERE status='sent' AND sent<?",
                                     (time.time() - 30 * 86400,))
                last_cleanup = time.time()
        except Exception:
            log.exception("Ошибка обслуживания")
        await asyncio.sleep(60)
