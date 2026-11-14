"""Админка в Telegram: поиск, заметки, ответы и контроль доставки."""

import html
import json
import time
from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from delivery import attachment_from, attachment_jobs, conversation_text, message_jobs

STATUS_LABELS = {"new": "🆕 новая", "work": "🔧 в работе", "done": "✅ закрыта"}


def is_admin(user_id: int | None, chat_id: int | None, admin_id: int) -> bool:
    return user_id == admin_id and chat_id == admin_id


class AdminInput(StatesGroup):
    search = State()
    note = State()
    reply = State()


def button(text, data):
    return InlineKeyboardButton(text=text, callback_data=data)


def keyboard(*rows):
    return InlineKeyboardMarkup(inline_keyboard=list(rows))


def admin_lead_kb(lead_id: int, client_id: int):
    return keyboard(
        [button("✍️ Ответить", f"re:{client_id}"), button("📋 Подробнее", f"adm:lead:{lead_id}")],
        [button("🔧 В работу", f"st:{lead_id}:work"), button("✅ Закрыта", f"st:{lead_id}:done")],
    )


def build_admin_router(store, admin_id: int) -> Router:
    router = Router(name="admin")
    # Личная админка: и автор нажатия, и чат должны принадлежать владельцу.
    router.message.filter(F.chat.id == admin_id, F.from_user.id == admin_id)
    router.callback_query.filter(F.message.chat.id == admin_id, F.from_user.id == admin_id)

    async def home(message):
        counts = {r["status"]: r["n"] for r in store.db.execute(
            "SELECT status,COUNT(*) n FROM leads GROUP BY status")}
        queue = store.queue_counts()
        waiting = store.db.execute("SELECT COUNT(*) FROM followups").fetchone()[0]
        await message.answer(
            "🗂 <b>Управление заявками</b>\n\n"
            f"Новые: {counts.get('new', 0)} · в работе: {counts.get('work', 0)} · "
            f"закрыты: {counts.get('done', 0)}\n"
            f"Ожидают ответа: {waiting}\n"
            f"Очередь доставки: {queue.get('pending', 0)} · ошибки: {queue.get('failed', 0)}",
            parse_mode="HTML", reply_markup=keyboard(
                [button("🆕 Новые", "adm:list:new:0"), button("🔧 В работе", "adm:list:work:0")],
                [button("✅ Закрытые", "adm:list:done:0"), button("📋 Все", "adm:list:all:0")],
                [button("🔎 Поиск", "adm:search"), button("⏰ Без ответа", "adm:waiting")],
                [button("📤 Доставка", "adm:queue")],
            ),
        )

    async def show_list(message, status="all", page=0, query=""):
        rows, total = store.list_leads("all" if status == "search" else status, query, page)
        buttons = [[button(
            f"#{r['id']} · {r['name'] or r['username'] or r['user_id']} · {STATUS_LABELS[r['status']]}"[:64],
            f"adm:lead:{r['id']}")] for r in rows]
        navigation = []
        if page > 0:
            navigation.append(button("‹ Назад", f"adm:list:{status}:{page - 1}"))
        if (page + 1) * 8 < total:
            navigation.append(button("Далее ›", f"adm:list:{status}:{page + 1}"))
        if navigation:
            buttons.append(navigation)
        buttons.append([button("‹ Админка", "adm:home")])
        await message.answer(
            f"📋 Найдено заявок: <b>{total}</b>" +
            (f"\nПоиск: {html.escape(query)}" if query else "") +
            (f"\nСтраница {page + 1}" if total else ""),
            parse_mode="HTML", reply_markup=keyboard(*buttons),
        )

    async def show_lead(message, lead_id):
        row = store.get_lead(lead_id)
        if not row:
            await message.answer("Заявка не найдена.")
            return
        lines = [
            f"📋 <b>Заявка #{lead_id}</b> · {STATUS_LABELS[row['status']]}",
            f"Дата: {html.escape(row['ts'])}",
            f"Имя: {html.escape(row['name'] or '—')}",
            f"Telegram: @{html.escape(row['username'])}" if row["username"]
            else f"Telegram ID: {row['user_id']}",
            f"Телефон: {html.escape(row['phone'] or '—')}",
            f"Почта: {html.escape(row['email'] or '—')}",
            f"Источник: {html.escape(row['source'] or '—')}",
            f"\n<b>Задача:</b>\n{html.escape(row['task'] or '—')}",
        ]
        if row["order_text"]:
            lines.append(f"\n<b>Состав заказа:</b>\n{html.escape(row['order_text'])}")
        notes = store.db.execute(
            "SELECT * FROM notes WHERE lead_id=? ORDER BY id DESC LIMIT 10", (lead_id,)
        ).fetchall()
        if notes:
            lines.append("\n<b>Последние заметки:</b>")
            lines.extend(f"• {html.escape(r['ts'])}: {html.escape(r['text'])}" for r in reversed(notes))
        attachments = json.loads(row["attachments"])
        buttons = [
            [button("✍️ Ответить", f"re:{row['user_id']}"), button("🗒 Заметка", f"adm:note:{lead_id}")],
            [button("🆕 Новая", f"st:{lead_id}:new"), button("🔧 В работу", f"st:{lead_id}:work"),
             button("✅ Закрыта", f"st:{lead_id}:done")],
        ]
        if attachments:
            buttons.append([button(f"📎 Вложения ({len(attachments)})", f"adm:files:{lead_id}")])
        buttons.append([button("💬 Переписка файлом", f"adm:history:{lead_id}")])
        buttons.append([button("‹ Админка", "adm:home")])
        await message.answer("\n".join(lines), parse_mode="HTML", reply_markup=keyboard(*buttons))

    @router.message(Command("admin", "leads"))
    async def command_home(message: Message, state: FSMContext):
        await state.clear()
        await home(message)

    @router.callback_query(F.data == "adm:home")
    async def callback_home(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        await state.clear()
        await home(callback.message)

    @router.callback_query(F.data.regexp(r"^adm:list:(all|new|work|done|search):\d+$"))
    async def callback_list(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        _, _, status, page = callback.data.split(":")
        data = await state.get_data()
        await show_list(callback.message, status, int(page), data.get("query", "") if status == "search" else "")

    @router.callback_query(F.data.regexp(r"^adm:lead:\d+$"))
    async def callback_lead(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        await state.clear()
        await show_lead(callback.message, int(callback.data.split(":")[-1]))

    @router.callback_query(F.data == "adm:search")
    async def callback_search(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        await state.clear()
        await state.set_state(AdminInput.search)
        await callback.message.answer("Напишите номер заявки, имя, @username, контакт или слова из задачи. /cancel — отмена.")

    @router.message(Command("find"))
    async def command_find(message: Message, state: FSMContext, command: CommandObject):
        await state.clear()
        await state.set_state(AdminInput.search)
        query = (command.args or "").strip().lstrip("@")
        if not query:
            await message.answer("Пример: /find #12 или /find Иван")
            return
        await state.update_data(query=query)
        await show_list(message, "search", query=query)

    @router.message(AdminInput.search, F.text, ~F.text.startswith("/"), F.text != "Отмена")
    async def search_text(message: Message, state: FSMContext):
        query = message.text.strip().lstrip("@")
        await state.update_data(query=query)
        await show_list(message, "search", query=query)

    @router.callback_query(F.data.regexp(r"^adm:note:\d+$"))
    async def callback_note(callback: CallbackQuery, state: FSMContext):
        lead_id = int(callback.data.split(":")[-1])
        if not store.get_lead(lead_id):
            await callback.answer("Заявка не найдена", show_alert=True)
            return
        await callback.answer()
        await state.clear()
        await state.set_state(AdminInput.note)
        await state.update_data(note_lead=lead_id)
        await callback.message.answer(f"Заметка к заявке #{lead_id} (видна только вам). /cancel — отмена.")

    @router.message(AdminInput.note, F.text, ~F.text.startswith("/"), F.text != "Отмена")
    async def note_text(message: Message, state: FSMContext):
        data = await state.get_data()
        lead_id = data["note_lead"]
        with store.db:
            store.db.execute("INSERT INTO notes(lead_id,ts,text) VALUES(?,?,?)",
                             (lead_id, datetime.now(timezone.utc).isoformat(timespec="seconds"), message.text))
        await state.clear()
        await show_lead(message, lead_id)

    @router.callback_query(F.data.regexp(r"^adm:files:\d+$"))
    async def callback_files(callback: CallbackQuery):
        row = store.get_lead(int(callback.data.split(":")[-1]))
        if not row:
            await callback.answer("Заявка не найдена")
            return
        with store.db:
            store.enqueue(attachment_jobs(admin_id, json.loads(row["attachments"])), f"files:{callback.id}")
        await callback.answer("Вложения поставлены в очередь")

    @router.callback_query(F.data.regexp(r"^st:\d+:(new|work|done)$"))
    async def callback_status(callback: CallbackQuery):
        _, raw_id, status = callback.data.split(":")
        lead_id = int(raw_id)
        row = store.get_lead(lead_id)
        if not row:
            await callback.answer("Заявка не найдена")
            return
        if row["status"] == status:
            await callback.answer("Этот статус уже установлен")
            return
        notice = {
            "new": f"🆕 Заявка #{lead_id} вновь открыта.",
            "work": f"🔧 Ваша заявка #{lead_id} взята в работу.",
            "done": f"✅ Заявка #{lead_id} закрыта. Спасибо за обращение! /start — новая заявка.",
        }[status]
        with store.db:
            store.db.execute("UPDATE leads SET status=? WHERE id=?", (status, lead_id))
            store.enqueue(message_jobs(row["user_id"], notice), f"status:{callback.id}")
            if status == "done":
                store.db.execute("DELETE FROM followups WHERE user_id=? AND lead_id=?", (row["user_id"], lead_id))
        await callback.answer("Статус сохранён")
        await show_lead(callback.message, lead_id)

    @router.callback_query(F.data.regexp(r"^adm:history:\d+$"))
    async def callback_history(callback: CallbackQuery):
        lead = store.get_lead(int(callback.data.split(":")[-1]))
        if not lead:
            await callback.answer("Заявка не найдена")
            return
        rows = store.db.execute(
            "SELECT * FROM conversation WHERE user_id=? ORDER BY id", (lead["user_id"],)
        ).fetchall()
        if not rows:
            await callback.answer("Переписка пока не записана", show_alert=True)
            return
        content = "\n\n".join(f"{r['ts']} · {r['direction']}\n{r['text']}" for r in rows)
        with store.db:
            store.enqueue([{"kind": "text_file", "chat_id": admin_id,
                            "filename": f"dialog-{lead['user_id']}.txt", "content": content}],
                          f"history:{callback.id}")
        await callback.answer("Переписка поставлена в очередь")

    @router.callback_query(F.data.regexp(r"^re:\d+$"))
    async def callback_reply(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        target_id = int(callback.data.split(":")[1])
        await state.clear()
        await state.set_state(AdminInput.reply)
        await state.update_data(reply_to=target_id)
        await callback.message.answer(
            f"✍️ Ответ клиенту {target_id}. Можно отправлять текст, файлы, фото и голосовые.",
            reply_markup=keyboard([button("Закончить ответ", "adm:finish")]),
        )

    @router.callback_query(F.data == "adm:finish")
    async def callback_finish(callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        await state.clear()
        await home(callback.message)

    @router.message(AdminInput.reply, lambda message: not message.text or (
        not message.text.startswith("/") and message.text != "Отмена"
    ))
    async def reply_message(message: Message, state: FSMContext):
        data = await state.get_data()
        target_id = data.get("reply_to")
        attachment = attachment_from(message)
        if not target_id or not (message.text or attachment):
            await message.answer("Поддерживаются текст, документы, фото, видео, аудио и голосовые.")
            return
        markup = keyboard([button("↩️ Ответить", "chat")])
        text = "👨‍🔧 <b>Сообщение от инженера opsmith:</b>"
        if message.text:
            text += "\n\n" + html.escape(message.text)
        jobs = message_jobs(target_id, text, markup if not attachment else None)
        if attachment:
            jobs += attachment_jobs(target_id, [attachment], markup)
        with store.db:
            store.enqueue(jobs, f"reply:{message.chat.id}:{message.message_id}",
                          effect={"reply_to": target_id, "cutoff": time.time()})
            store.record_message(f"reply:{message.chat.id}:{message.message_id}", target_id, "Инженер",
                                 conversation_text(message.text or "", [attachment] if attachment else []))
        await message.answer(
            "Ответ сохранён и поставлен в очередь доставки. Можно дописать.",
            reply_markup=keyboard([button("Закончить ответ", "adm:finish")]),
        )

    @router.callback_query(F.data == "adm:waiting")
    async def callback_waiting(callback: CallbackQuery):
        await callback.answer()
        rows = store.db.execute("SELECT * FROM followups ORDER BY since LIMIT 30").fetchall()
        buttons = []
        for row in rows:
            title = f"#{row['lead_id']}" if row["lead_id"] else str(row["user_id"])
            buttons.append([button(f"✍️ Ответить · {title}", f"re:{row['user_id']}"),
                            button("Через 1 ч", f"adm:snooze:{row['user_id']}:1")])
        buttons.append([button("‹ Админка", "adm:home")])
        await callback.message.answer(
            "⏰ Ожидают ответа (до 30 самых старых)." if rows else "Все обращения обработаны ✅",
            reply_markup=keyboard(*buttons),
        )

    @router.callback_query(F.data.regexp(r"^adm:snooze:\d+:(1|24)$"))
    async def callback_snooze(callback: CallbackQuery):
        _, _, uid, hours = callback.data.split(":")
        with store.db:
            store.db.execute("UPDATE followups SET next_reminder=? WHERE user_id=?",
                             (time.time() + int(hours) * 3600, int(uid)))
        await callback.answer(f"Напомню через {hours} ч., если ответ ещё понадобится.")

    @router.callback_query(F.data == "adm:queue")
    async def callback_queue(callback: CallbackQuery):
        await callback.answer()
        counts = store.queue_counts()
        errors = store.db.execute(
            "SELECT id,chat_id,last_error FROM outbox WHERE status='failed' ORDER BY id DESC LIMIT 5"
        ).fetchall()
        text = f"📤 Ожидают: {counts.get('pending', 0)}\nОшибки: {counts.get('failed', 0)}"
        for row in errors:
            text += f"\n\n#{row['id']} → {row['chat_id']}: {html.escape(row['last_error'] or '')}"
        await callback.message.answer(text, parse_mode="HTML", reply_markup=keyboard(
            [button("🔄 Повторить неудачные", "adm:retry")], [button("‹ Админка", "adm:home")]))

    @router.callback_query(F.data == "adm:retry")
    async def callback_retry(callback: CallbackQuery):
        with store.db:
            store.db.execute("UPDATE outbox SET status='pending',next_attempt=?,attempts=0 WHERE status='failed'",
                             (time.time(),))
        await callback.answer("Повторная доставка запланирована")

    return router
