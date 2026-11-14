"""Проверки сценариев без подключения к Telegram и без рабочей базы."""

import asyncio
import html
import json
import logging
import os
import sqlite3
import sys
import tempfile
import time
import unittest
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
temp_parent = Path(os.environ["LOCALAPPDATA"]) / "Temp" / "opencode" if os.name == "nt" else Path(tempfile.gettempdir())
temp_parent.mkdir(parents=True, exist_ok=True)
ROOT = tempfile.TemporaryDirectory(prefix="bot-tests-", dir=temp_parent)
os.environ.update(BOT_TOKEN="123456789:TEST_TOKEN_ONLY", ADMIN_CHAT_ID="42",
                  LEADS_DB=str(Path(ROOT.name) / "app.db"),
                  LOG_DIR=str(Path(ROOT.name) / "logs"), OLLAMA_URL="",
                  ESPOCRM_URL="", ESPOCRM_API_KEY="")

from aiogram import Bot, Dispatcher
from aiogram.client.session.base import BaseSession
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import SimpleEventIsolation
from aiogram.methods import SendMessage
from aiogram.types import Message, Update, User

import bot as app
from admin import build_admin_router
from delivery import SplitMessages, message_jobs, split_text, text_length
from maintenance import deliver_once, schedule_reminders
from storage import SQLiteStorage, Store


def tearDownModule():
    app.store.close()
    for handler in list(logging.getLogger().handlers):
        logging.getLogger().removeHandler(handler)
        handler.close()
    ROOT.cleanup()


class FakeSession(BaseSession):
    def __init__(self):
        super().__init__()
        self.calls = []
        self.failures = []

    async def close(self):
        pass

    async def stream_content(self, *args, **kwargs):
        yield b""

    async def make_request(self, bot, method, timeout=None):
        if self.failures:
            raise self.failures.pop(0)
        self.calls.append(method)
        if method.__api_method__ == "getMe":
            return User(id=bot.id, is_bot=True, first_name="Test", username="test_bot")
        if method.__api_method__.startswith(("send", "editMessage")) and hasattr(method, "chat_id"):
            return Message(message_id=len(self.calls), date=datetime.now(timezone.utc),
                           chat={"id": int(method.chat_id), "type": "private"},
                           from_user={"id": bot.id, "is_bot": True, "first_name": "Test"},
                           text=getattr(method, "text", None))
        return True


class TextReader(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text = ""
        self.stack = []

    def handle_starttag(self, tag, attrs):
        self.stack.append(tag)

    def handle_endtag(self, tag):
        assert self.stack.pop() == tag

    def handle_data(self, data):
        self.text += data


class PersistenceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=ROOT.name)
        self.path = Path(self.directory.name) / "test.db"
        self.store = Store(str(self.path), reminder_seconds=60)
        self.session = FakeSession()
        self.bot = Bot("987654:TEST", session=self.session)

    def tearDown(self):
        self.store.close()
        self.directory.cleanup()

    async def test_migration_preserves_existing_lead(self):
        self.store.close()
        self.path.unlink()
        legacy = sqlite3.connect(self.path)
        legacy.execute("CREATE TABLE leads(id INTEGER PRIMARY KEY,ts TEXT,user_id INTEGER,username TEXT,"
                       "name TEXT,task TEXT,phone TEXT,email TEXT,source TEXT,order_text TEXT,status TEXT)")
        legacy.execute("INSERT INTO leads(id,ts,user_id,name,task,status) VALUES(7,'2026-01-01',101,'Иван','Задача','new')")
        legacy.commit()
        legacy.close()
        self.store = Store(str(self.path))
        row = self.store.get_lead(7)
        self.assertEqual((row["name"], row["task"], row["attachments"]), ("Иван", "Задача", "[]"))

    async def test_lead_and_notification_commit_together_and_deduplicate(self):
        def broken(_):
            raise ValueError("format failure")
        with self.assertRaises(ValueError):
            self.store.create_lead(101, "test", {"task": "Задача"}, "same", broken)
        self.assertEqual(self.store.list_leads()[1], 0)
        first = self.store.create_lead(101, "test", {"task": "Задача"}, "same",
                                       lambda lead: message_jobs(42, str(lead)))
        second = self.store.create_lead(101, "test", {}, "same", broken)
        self.assertEqual(first, (second[0], True))
        self.assertFalse(second[1])
        self.assertEqual(self.store.queue_counts(), {"pending": 1})

    async def test_session_and_queue_survive_reopen(self):
        key = StorageKey(bot_id=987654, chat_id=101, user_id=101)
        storage = SQLiteStorage(self.store)
        await storage.set_state(key, app.Form.phone)
        await storage.set_data(key, {"name": "Иван", "attachments": [{"kind": "photo", "file_id": "abc"}]})
        with self.store.db:
            self.store.enqueue(message_jobs(42, "pending"), "restart")
        self.store.close()
        self.store = Store(str(self.path))
        storage = SQLiteStorage(self.store)
        self.assertEqual(await storage.get_state(key), "Form:phone")
        self.assertEqual((await storage.get_data(key))["attachments"][0]["file_id"], "abc")
        await deliver_once(self.store, self.bot)
        self.assertEqual(self.store.queue_counts(), {})

    async def test_failed_delivery_retries_without_resending_completed_parts(self):
        with self.store.db:
            self.store.enqueue(message_jobs(42, "a" * 4000), "long")
        await deliver_once(self.store, self.bot)
        self.session.failures = [OSError("offline")]
        await deliver_once(self.store, self.bot)
        self.assertEqual(len(self.session.calls), 1)
        row = self.store.db.execute("SELECT * FROM outbox WHERE status='pending'").fetchone()
        self.assertEqual(row["attempts"], 1)
        self.assertGreater(row["next_attempt"], time.time())
        with self.store.db:
            self.store.db.execute("UPDATE outbox SET next_attempt=0")
        await deliver_once(self.store, self.bot)
        self.assertEqual([len(m.text) for m in self.session.calls], [3500, 500])

    async def test_rate_limit_and_permanent_error_are_distinguished(self):
        with self.store.db:
            self.store.enqueue(message_jobs(42, "hello"), "rate")
            self.store.enqueue(message_jobs(101, "hello"), "blocked")
        method = SendMessage(chat_id=42, text="hello")
        self.session.failures = [
            TelegramRetryAfter(method=method, message="slow down", retry_after=40),
            TelegramForbiddenError(method=method, message="blocked"),
        ]
        await deliver_once(self.store, self.bot)
        self.assertEqual(self.store.queue_counts(), {"failed": 1, "pending": 1})
        pending = self.store.db.execute("SELECT * FROM outbox WHERE status='pending'").fetchone()
        self.assertGreater(pending["next_attempt"], time.time() + 39)

    async def test_reply_clears_reminder_only_after_all_parts_delivered(self):
        with self.store.db:
            self.store.wait_for_reply(101, now=10)
            self.store.enqueue(message_jobs(101, "a" * 4000), "reply", {"reply_to": 101, "cutoff": 20})
        self.session.failures = [TelegramForbiddenError(method=SendMessage(chat_id=101, text="a"), message="blocked")]
        await deliver_once(self.store, self.bot)  # first part fails permanently
        await deliver_once(self.store, self.bot)  # last part succeeds
        self.assertEqual(self.store.db.execute("SELECT COUNT(*) FROM followups").fetchone()[0], 1)
        with self.store.db:
            self.store.db.execute("UPDATE outbox SET status='pending',next_attempt=0 WHERE status='failed'")
        await deliver_once(self.store, self.bot)
        self.assertEqual(self.store.db.execute("SELECT COUNT(*) FROM followups").fetchone()[0], 0)

    async def test_new_message_after_queued_reply_still_requires_response(self):
        with self.store.db:
            self.store.wait_for_reply(101, now=10)
            self.store.enqueue(message_jobs(101, "answer"), "reply", {"reply_to": 101, "cutoff": 20})
            self.store.wait_for_reply(101, now=30)
        await deliver_once(self.store, self.bot)
        row = self.store.db.execute("SELECT * FROM followups").fetchone()
        self.assertEqual(row["since"], 30)

    async def test_reminder_deduplication_and_cancellation_after_response(self):
        with self.store.db:
            self.store.wait_for_reply(101, now=1)
        schedule_reminders(self.store, 42, 3600, now=62)
        schedule_reminders(self.store, 42, 3600, now=63)
        self.assertEqual(self.store.queue_counts(), {"pending": 1})
        with self.store.db:
            self.store.db.execute("DELETE FROM followups")
        await deliver_once(self.store, self.bot)
        self.assertEqual(self.session.calls, [])

    async def test_backup_is_consistent_and_restorable(self):
        self.store.create_lead(101, "", {"task": "Задача"}, "b", lambda _: message_jobs(42, "notify"))
        destination = await asyncio.to_thread(self.store.backup, str(Path(self.directory.name) / "backups"), 2)
        copy = sqlite3.connect(destination)
        try:
            self.assertEqual(copy.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(copy.execute("SELECT COUNT(*) FROM leads").fetchone()[0], 1)
            self.assertEqual(copy.execute("SELECT COUNT(*) FROM outbox").fetchone()[0], 1)
        finally:
            copy.close()

    async def test_backup_retention_keeps_only_selected_daily_copies(self):
        directory = Path(self.directory.name) / "backups"
        directory.mkdir()
        for day in ("01", "02", "03"):
            (directory / f"leads-2000-01-{day}.db").touch()
        await asyncio.to_thread(self.store.backup, str(directory), 2)
        self.assertEqual(len(list(directory.glob("leads-*.db"))), 2)
        self.assertTrue((directory / "leads-2000-01-03.db").exists())

    async def test_unicode_search_and_literal_wildcards(self):
        self.store.create_lead(101, "example", {"name": "ИВАН", "task": "100% готовность"}, "s", lambda _: [])
        self.assertEqual(self.store.list_leads(query="иван")[1], 1)
        self.assertEqual(self.store.list_leads(query="100%")[1], 1)
        self.assertEqual(self.store.list_leads(query="100_")[1], 0)


class SplittingTests(unittest.IsolatedAsyncioTestCase):
    async def test_html_emoji_and_entities_are_preserved(self):
        raw = '<b>Задача</b>\n<a href="https://example.com/?a=1&amp;b=2">' + html.escape("🙂<& тест " * 1500) + "</a>"
        parts = split_text(raw, html_mode=True)
        original = TextReader()
        original.feed(raw)
        texts = []
        for part in parts:
            parsed = TextReader()
            parsed.feed(part)
            self.assertFalse(parsed.stack)
            self.assertLessEqual(text_length(parsed.text), 3500)
            texts.append(parsed.text)
        self.assertEqual("".join(texts), original.text)

    async def test_message_middleware_keeps_buttons_on_last_part(self):
        session = FakeSession()
        session.middleware(SplitMessages())
        bot = Bot("987654:TEST", session=session)
        await bot.send_message(101, "<b>" + "🙂" * 3000 + "</b>", parse_mode="HTML",
                               reply_markup=app.ikb([app.btn("Next", "next")]))
        self.assertEqual(len(session.calls), 2)
        self.assertIsNone(session.calls[0].reply_markup)
        self.assertIsNotNone(session.calls[-1].reply_markup)


class FlowTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.dp = Dispatcher(storage=SQLiteStorage(app.store), events_isolation=SimpleEventIsolation())
        cls.dp.include_router(build_admin_router(app.store, 42))
        cls.dp.include_router(app.router)

    async def asyncSetUp(self):
        with app.db:
            for table in ("notes", "conversation", "followups", "outbox", "sessions", "leads"):
                app.db.execute(f"DELETE FROM {table}")
        app._last_lead_at.clear()
        self.session = FakeSession()
        self.session.middleware(SplitMessages())
        self.bot = Bot(os.environ["BOT_TOKEN"], session=self.session)
        self.seq = 100

    async def event(self, uid=101, text=None, callback=None, **media):
        self.seq += 1
        user = {"id": uid, "is_bot": False, "first_name": "Иван"}
        message = {"message_id": self.seq, "date": int(time.time()),
                   "chat": {"id": uid, "type": "private", "first_name": "Иван"},
                   "from": user, **media}
        if text is not None:
            message["text"] = text
            if text.startswith("/"):
                message["entities"] = [{"type": "bot_command", "offset": 0, "length": len(text.split()[0])}]
        if callback is not None:
            message["from"] = {"id": self.bot.id, "is_bot": True, "first_name": "Bot"}
            payload = {"callback_query": {"id": str(self.seq), "from": user, "message": message,
                                           "chat_instance": "test", "data": callback}}
        else:
            payload = {"message": message}
        await self.dp.feed_update(self.bot, Update.model_validate({"update_id": self.seq, **payload}))

    async def state(self, uid=101):
        return self.dp.fsm.get_context(bot=self.bot, chat_id=uid, user_id=uid)

    async def ready_form(self):
        await self.event(callback="lead")
        state = await self.state()
        self.assertEqual(await state.get_state(), app.Form.task.state)
        await self.event(text="Нужно настроить сервер для магазина")
        await self.event(text=app.CONTACT_HERE)
        self.assertEqual(await state.get_state(), app.Form.confirm.state)
        return state

    async def test_admin_entry_is_visible_only_to_owner_on_every_menu_path(self):
        for uid in (101, 42):
            for event in ({"text": "/start"}, {"callback": "menu"}, {"text": "/help"}):
                self.session.calls.clear()
                await self.event(uid=uid, **event)
                markups = [getattr(call, "reply_markup", None) for call in self.session.calls]
                buttons = [button.callback_data for markup in markups
                           if hasattr(markup, "inline_keyboard")
                           for row in markup.inline_keyboard for button in row]
                self.assertEqual("adm:home" in buttons, uid == 42, (uid, event))

    async def test_hidden_admin_commands_do_not_open_panel_or_change_client_draft(self):
        state = await self.ready_form()
        original = await state.get_data()
        for command in ("/admin", "/leads", "/find Иван", "/stats"):
            self.session.calls.clear()
            await self.event(text=command)
            self.assertEqual(await state.get_state(), app.Form.confirm.state)
            self.assertEqual(await state.get_data(), original)
            for call in self.session.calls:
                text = getattr(call, "text", "") or ""
                self.assertNotIn("Управление заявками", text)
                markup = getattr(call, "reply_markup", None)
                if hasattr(markup, "inline_keyboard"):
                    self.assertFalse(any(
                        (button.callback_data or "").startswith(("adm:", "st:", "re:"))
                        for row in markup.inline_keyboard for button in row
                    ))

    async def test_all_admin_callback_families_are_inaccessible_to_clients(self):
        state = await self.ready_form()
        original = await state.get_data()
        for callback in ("adm:home", "adm:list:all:0", "adm:search", "adm:lead:1",
                         "adm:files:1", "adm:history:1", "adm:note:1", "adm:queue",
                         "adm:retry", "adm:waiting", "adm:snooze:101:1", "re:42", "st:1:done"):
            self.session.calls.clear()
            await self.event(callback=callback)
            self.assertEqual([call.__api_method__ for call in self.session.calls], ["answerCallbackQuery"])
            self.assertEqual(await state.get_state(), app.Form.confirm.state)
            self.assertEqual(await state.get_data(), original)
        self.assertEqual(app.store.queue_counts(), {})

    async def test_admin_commands_are_registered_only_for_owner_chat(self):
        await app.configure_commands(self.bot)
        registrations = [call for call in self.session.calls if call.__api_method__ == "setMyCommands"]
        private_scope_seen = False
        for call in registrations:
            commands = {command.command for command in call.commands}
            admin_commands = commands & {"admin", "leads", "find", "stats"}
            if admin_commands:
                self.assertEqual(call.scope.type, "chat")
                self.assertEqual(call.scope.chat_id, 42)
            if call.scope and call.scope.type == "all_private_chats":
                private_scope_seen = True
                self.assertFalse(admin_commands)
        self.assertTrue(private_scope_seen)
        self.assertTrue(any("admin" in {c.command for c in call.commands} for call in registrations))

    async def test_short_form_resume_media_and_double_click(self):
        await self.event(callback="lead")
        await self.event(photo=[{"file_id": "photo-id", "file_unique_id": "photo-unique", "width": 100, "height": 100}],
                         caption="Ошибка на сервере")
        await self.event(text="/start")
        await self.event(callback="draft:resume")
        await self.event(text=app.ATTACH_DONE)
        await self.event(text=app.CONTACT_HERE)
        state = await self.state()
        data = await state.get_data()
        await self.event(callback=f"send:{data['submission_key']}")
        await self.event(callback=f"send:{data['submission_key']}")
        row = app.db.execute("SELECT * FROM leads").fetchone()
        self.assertEqual(app.store.list_leads()[1], 1)
        self.assertEqual((row["name"], row["phone"], row["email"]), ("Иван", "", ""))
        self.assertEqual(json.loads(row["attachments"])[0]["file_id"], "photo-id")
        self.assertIsNone(await state.get_state())
        payloads = [json.loads(r["payload"]) for r in app.db.execute("SELECT * FROM outbox")]
        self.assertTrue(any(p["kind"] == "photo" for p in payloads))

    async def test_stale_send_cannot_submit_new_draft(self):
        state = await self.ready_form()
        await self.event(callback="send:wrong-draft")
        self.assertEqual(app.store.list_leads()[1], 0)
        self.assertEqual(await state.get_state(), app.Form.confirm.state)

    async def test_phone_and_edit_name(self):
        await self.event(callback="lead")
        await self.event(text="Настройка сервера и мониторинга")
        await self.event(text=app.CONTACT_PHONE)
        await self.event(contact={"phone_number": "+79991234567", "first_name": "Иван", "user_id": 101})
        state = await self.state()
        self.assertEqual(await state.get_state(), app.Form.confirm.state)
        await self.event(callback="edit:name")
        await self.event(text="Пётр")
        self.assertEqual((await state.get_data())["name"], "Пётр")
        self.assertEqual(await state.get_state(), app.Form.confirm.state)

    async def test_admin_authorization_notes_status_and_media_reply(self):
        state = await self.ready_form()
        data = await state.get_data()
        await self.event(callback=f"send:{data['submission_key']}")
        lead_id = app.db.execute("SELECT id FROM leads").fetchone()[0]
        await self.event(callback=f"st:{lead_id}:done")
        await self.event(callback=f"st:{lead_id}:done", chat={"id": 42, "type": "private"})
        self.assertEqual(app.store.get_lead(lead_id)["status"], "new")
        await self.event(uid=42, text="/admin")
        await self.event(uid=42, callback=f"adm:note:{lead_id}")
        await self.event(uid=42, text="Созвон в понедельник")
        self.assertEqual(app.db.execute("SELECT COUNT(*) FROM notes").fetchone()[0], 1)
        await self.event(uid=42, callback=f"st:{lead_id}:work")
        self.assertEqual(app.store.get_lead(lead_id)["status"], "work")
        await self.event(uid=42, callback="re:101")
        await self.event(uid=42, voice={"file_id": "voice-id", "file_unique_id": "voice-unique", "duration": 2})
        payloads = [json.loads(r["payload"]) for r in app.db.execute("SELECT * FROM outbox")]
        self.assertTrue(any(p["kind"] == "voice" and p["chat_id"] == 101 for p in payloads))
        await self.event(uid=42, callback="adm:finish")
        self.assertIsNone(await (await self.state(42)).get_state())

    async def test_direct_media_is_durable_and_exportable(self):
        state = await self.ready_form()
        await self.event(callback=f"send:{(await state.get_data())['submission_key']}")
        lead_id = app.db.execute("SELECT id FROM leads").fetchone()[0]
        await self.event(callback="chat")
        await self.event(document={"file_id": "doc-id", "file_unique_id": "doc-unique", "file_name": "error.txt"})
        await self.event(uid=42, callback=f"adm:history:{lead_id}")
        jobs = [json.loads(r["payload"]) for r in app.db.execute("SELECT payload FROM outbox")]
        self.assertTrue(any(p["kind"] == "document" for p in jobs))
        export = next(p for p in jobs if p["kind"] == "text_file")
        self.assertIn("error.txt", export["content"])
        for _ in range(len(jobs)):
            await deliver_once(app.store, self.bot)
        self.assertEqual(app.store.queue_counts(), {})
        documents = [m for m in self.session.calls if m.__api_method__ == "sendDocument"]
        self.assertEqual(len(documents), 2)
        self.assertEqual(documents[-1].document.filename, "dialog-101.txt")


if __name__ == "__main__":
    unittest.main()
