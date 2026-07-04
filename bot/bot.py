"""
Бот приёма заявок с лендинга.

Клиент проходит короткую форму: имя → описание задачи → телефон (опц.) →
почта (опц.). Бот собирает заявку в аккуратное сообщение и отправляет
владельцу (ADMIN_CHAT_ID) вместе со всеми контактами клиента.

Если задан OLLAMA_URL — описание задачи дополнительно прогоняется через
локальную LLM, и к заявке прикладывается структурированный разбор
(суть, подходящая услуга, срочность). Без Ollama бот работает так же,
просто без блока «Разбор».

Настройка — через переменные окружения (см. .env.example и README.md).
"""

import asyncio
import html
import logging
import os
import re
from datetime import datetime, timedelta, timezone

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_CHAT_ID = int(os.environ["ADMIN_CHAT_ID"])
OLLAMA_URL = os.environ.get("OLLAMA_URL", "")  # напр. http://127.0.0.1:11434
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma2")

MSK = timezone(timedelta(hours=3))
PHONE_RE = re.compile(r"^\+?[\d\s\-()]{7,20}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("orders-bot")

router = Router()


class Form(StatesGroup):
    name = State()
    task = State()
    phone = State()
    email = State()


SKIP = "Пропустить"
CANCEL = "Отмена"


def kb(*rows: list[KeyboardButton]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=list(rows), resize_keyboard=True, one_time_keyboard=True)


KB_SKIP = kb([KeyboardButton(text=SKIP)], [KeyboardButton(text=CANCEL)])
KB_PHONE = kb(
    [KeyboardButton(text="📞 Отправить мой номер", request_contact=True)],
    [KeyboardButton(text=SKIP)],
    [KeyboardButton(text=CANCEL)],
)


# ── LLM-разбор задачи (опционально, через локальную Ollama) ──────────────────

async def analyze_task(text: str) -> str:
    if not OLLAMA_URL:
        return ""
    prompt = (
        "Ты — ассистент DevOps-инженера. Клиент оставил заявку. Составь короткий "
        "разбор по-русски, строго в формате:\n"
        "Суть: <одно предложение — что нужно клиенту>\n"
        "Услуга: <какая услуга подходит: настройка VPS / Docker и CI/CD / мониторинг / "
        "Telegram-бот / self-hosted ИИ / система под ключ / консультация>\n"
        "Срочность: <низкая / средняя / высокая — по тексту заявки>\n"
        "Вопросы: <1-2 уточняющих вопроса клиенту>\n"
        f"\nТекст заявки:\n{text}"
    )
    try:
        import aiohttp

        async with aiohttp.ClientSession() as s:
            async with s.post(
                f"{OLLAMA_URL.rstrip('/')}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
                timeout=aiohttp.ClientTimeout(total=60),
            ) as r:
                data = await r.json()
                return (data.get("response") or "").strip()
    except Exception as e:  # разбор — приятный бонус, заявка важнее
        log.warning("Ollama недоступна: %s", e)
        return ""


# ── диалог с клиентом ────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(Form.name)
    await message.answer(
        "Привет! Я приму вашу заявку и сразу передам её Даниле — "
        "он ответит в течение дня.\n\nКак вас зовут?",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(Command("cancel"))
@router.message(F.text == CANCEL)
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Ок, отменил. Начать заново — /start", reply_markup=ReplyKeyboardRemove()
    )


@router.message(Form.name, F.text)
async def form_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if len(name) < 2 or len(name) > 80:
        await message.answer("Напишите, пожалуйста, имя текстом (2–80 символов).")
        return
    await state.update_data(name=name)
    await state.set_state(Form.task)
    await message.answer(
        f"Приятно познакомиться, {name}!\n\n"
        "Опишите задачу свободным текстом: что за проект, что нужно сделать, "
        "какие сроки. Пишите как умеете — переведу на технический сам 🙂"
    )


@router.message(Form.task, F.text)
async def form_task(message: Message, state: FSMContext) -> None:
    task = message.text.strip()
    if len(task) < 15:
        await message.answer(
            "Расскажите чуть подробнее (хотя бы пару предложений) — "
            "так оценка будет точнее."
        )
        return
    await state.update_data(task=task)
    await state.set_state(Form.phone)
    await message.answer(
        "Принял! Оставите телефон для связи? Можно отправить кнопкой ниже, "
        "написать вручную или пропустить.",
        reply_markup=KB_PHONE,
    )


@router.message(Form.phone, F.contact)
async def form_phone_contact(message: Message, state: FSMContext) -> None:
    await state.update_data(phone=message.contact.phone_number)
    await ask_email(message, state)


@router.message(Form.phone, F.text)
async def form_phone_text(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if text == SKIP:
        await state.update_data(phone="")
    elif PHONE_RE.match(text):
        await state.update_data(phone=text)
    else:
        await message.answer("Не похоже на номер. Попробуйте ещё раз или нажмите «Пропустить».")
        return
    await ask_email(message, state)


async def ask_email(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.email)
    await message.answer(
        "И почта — если удобнее переписываться письмами (или «Пропустить»).",
        reply_markup=KB_SKIP,
    )


@router.message(Form.email, F.text)
async def form_email(message: Message, state: FSMContext, bot: Bot) -> None:
    text = message.text.strip()
    if text == SKIP:
        email = ""
    elif EMAIL_RE.match(text):
        email = text
    else:
        await message.answer("Не похоже на почту. Ещё раз — или нажмите «Пропустить».")
        return

    data = await state.get_data()
    await state.clear()
    await message.answer(
        "Готово, заявка ушла! 🚀\nДанила свяжется с вами в течение дня. Спасибо!",
        reply_markup=ReplyKeyboardRemove(),
    )
    await send_lead(bot, message, data["name"], data["task"], data.get("phone", ""), email)


async def send_lead(
    bot: Bot, message: Message, name: str, task: str, phone: str, email: str
) -> None:
    user = message.from_user
    tg_line = (
        f"@{user.username}"
        if user.username
        else f'<a href="tg://user?id={user.id}">профиль без юзернейма</a>'
    )
    analysis = await analyze_task(task)

    parts = [
        "🆕 <b>Новая заявка с сайта</b>",
        "",
        f"👤 <b>Имя:</b> {html.escape(name)}",
        f"📝 <b>Задача:</b>\n{html.escape(task)}",
    ]
    if analysis:
        parts += ["", f"🤖 <b>Разбор (локальная LLM):</b>\n{html.escape(analysis)}"]
    parts += [
        "",
        "📇 <b>Контакты:</b>",
        f"✈ Telegram: {tg_line} (id {user.id})",
        f"📞 Телефон: {html.escape(phone) if phone else '—'}",
        f"✉ Почта: {html.escape(email) if email else '—'}",
        "",
        f"🕒 {datetime.now(MSK):%d.%m.%Y %H:%M} МСК",
    ]
    try:
        await bot.send_message(
            ADMIN_CHAT_ID, "\n".join(parts), parse_mode="HTML",
            disable_web_page_preview=True,
        )
        log.info("Заявка от %s (id %s) доставлена", name, user.id)
    except Exception:
        log.exception("Не удалось доставить заявку админу")


# ── любой текст вне формы ────────────────────────────────────────────────────

@router.message(F.text)
async def fallback(message: Message, state: FSMContext) -> None:
    if await state.get_state() is None:
        await message.answer("Чтобы оставить заявку, нажмите /start 🙂")


async def main() -> None:
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    log.info("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
