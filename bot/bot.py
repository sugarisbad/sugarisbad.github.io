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
from aiogram.filters import Command, CommandObject, CommandStart
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

# Deep-link payload (t.me/<bot>?start=<slug>) → откуда пришёл клиент.
# Слаги должны совпадать с src/data/site.ts на сайте.
SOURCES = {
    # пакеты
    "plan-vps": "Пакет «Настройка VPS»",
    "plan-monitoring": "Пакет «Мониторинг и алерты»",
    "plan-ai": "Пакет «Self-hosted ИИ»",
    "plan-system": "Пакет «Система под ключ»",
    # прайс: серверы и безопасность
    "vps-setup": "Настройка VPS «под ключ»",
    "audit": "Аудит существующего сервера",
    "nginx-ssl": "nginx: домены, SSL, реверс-прокси",
    "migration": "Миграция на новый сервер",
    "backup": "Резервное копирование",
    # прайс: Docker и CI/CD
    "dockerize": "Docker-изация приложения",
    "compose": "docker-compose стек",
    "cicd": "CI/CD пайплайн",
    "mass-deploy": "Массовое развёртывание",
    # прайс: мониторинг
    "monitoring": "Мониторинг + алерты в Telegram",
    "balancer": "Балансировка нагрузки",
    "failover": "Автоматический failover",
    # прайс: ИИ
    "ollama": "Self-hosted ИИ (Ollama)",
    "tg-bot": "ИИ-агент / Telegram-бот",
    "turnkey": "Система под ключ",
    # прайс: поддержка
    "subscription": "Абонентское администрирование",
    "consult": "Разовая консультация",
    "incident": "Срочный выезд в инцидент",
    # общие кнопки «Оставить заявку» по страницам
    "src-home": "кнопка на главной странице",
    "src-cases": "кнопка на странице кейсов",
    "src-services": "кнопка на странице услуг и цен",
    "src-work": "кнопка на странице «Как я работаю»",
}

# Для этих слагов бот упоминает услугу в приветствии (страницы-источники — нет).
SERVICE_SLUGS = {s for s in SOURCES if not s.startswith("src-")}

# Калькулятор на сайте кодирует выбранные позиции однобуквенными кодами
# (payload вида calc-adg). Коды должны совпадать с calcCodes в src/data/site.ts.
CALC_ITEMS: dict[str, tuple[str, int, str]] = {
    # код: (название, стартовая цена ₽, суффикс цены)
    "a": ("Настройка VPS «под ключ»", 7000, ""),
    "b": ("Аудит существующего сервера", 4000, ""),
    "c": ("nginx: домены, SSL, реверс-прокси", 5000, ""),
    "d": ("Миграция на новый сервер", 12000, ""),
    "e": ("Резервное копирование", 8000, ""),
    "f": ("Docker-изация приложения", 10000, ""),
    "g": ("docker-compose стек", 15000, ""),
    "h": ("CI/CD пайплайн", 15000, ""),
    "i": ("Массовое развёртывание", 25000, ""),
    "j": ("Мониторинг + алерты в Telegram", 15000, ""),
    "k": ("Балансировка нагрузки", 18000, ""),
    "l": ("Автоматический failover", 30000, ""),
    "m": ("Self-hosted ИИ (Ollama)", 20000, ""),
    "n": ("ИИ-агент / Telegram-бот", 40000, ""),
    "o": ("Система под ключ", 160000, ""),
    "p": ("Абонентское администрирование", 10000, "/мес"),
    "q": ("Разовая консультация", 4000, "/час"),
    "r": ("Срочный выезд в инцидент", 6000, ""),
}


def parse_calc(slug: str) -> tuple[str, str]:
    """calc-<коды> → (текст состава заказа, краткий источник). Пустые строки, если не калькулятор."""
    if not slug.startswith("calc-"):
        return "", ""
    total = 0
    monthly = 0
    lines = []
    for code in slug[5:]:
        item = CALC_ITEMS.get(code)
        if not item:
            continue
        name, price, suffix = item
        lines.append(f"· {name} — от {price:,} ₽{suffix}".replace(",", " "))
        if suffix == "/мес":
            monthly += price
        else:
            total += price
    if not lines:
        return "", ""
    summary = f"Итого: от {total:,} ₽".replace(",", " ")
    if monthly:
        summary += f" + от {monthly:,} ₽/мес".replace(",", " ")
    order = "\n".join(lines) + f"\n{summary}"
    return order, f"Калькулятор на сайте ({len(lines)} поз.)"


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
async def cmd_start(message: Message, state: FSMContext, command: CommandObject) -> None:
    await state.clear()
    slug = (command.args or "").strip()
    order, calc_source = parse_calc(slug)
    source = calc_source or SOURCES.get(slug, "")
    await state.update_data(source=source, source_slug=slug if source else "", order=order)
    await state.set_state(Form.name)

    if order:
        intro = (
            "Привет! Получил ваш заказ из калькулятора:\n\n"
            f"<b>{html.escape(order)}</b>\n\n"
        )
    elif slug in SERVICE_SLUGS:
        intro = f"Привет! Вижу, вас интересует <b>{html.escape(source)}</b> — отличный выбор.\n"
    else:
        intro = "Привет! "
    await message.answer(
        intro + "Я приму вашу заявку и сразу передам её инженеру opsmith — "
        "он ответит в течение дня.\n\nКак вас зовут?",
        parse_mode="HTML",
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
        "Готово, заявка ушла! 🚀\nИнженер opsmith свяжется с вами в течение дня. Спасибо!",
        reply_markup=ReplyKeyboardRemove(),
    )
    await send_lead(
        bot, message, data["name"], data["task"], data.get("phone", ""), email,
        data.get("source", ""), data.get("order", ""),
    )


async def send_lead(
    bot: Bot, message: Message, name: str, task: str, phone: str, email: str,
    source: str = "", order: str = "",
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
    ]
    if source:
        parts.append(f"🔗 <b>Откуда:</b> {html.escape(source)}")
    if order:
        parts.append(f"🧮 <b>Заказ из калькулятора:</b>\n{html.escape(order)}")
    parts.append(f"📝 <b>Задача:</b>\n{html.escape(task)}")
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
