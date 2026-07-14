"""
Бот приёма заявок с лендинга.

Клиент проходит короткую форму: имя → описание задачи → телефон (опц.) →
почта (опц.). Бот собирает заявку в аккуратное сообщение и отправляет
владельцу (ADMIN_CHAT_ID) вместе со всеми контактами клиента.

Если задан OLLAMA_URL — описание задачи дополнительно прогоняется через
локальную LLM, и к заявке прикладывается структурированный разбор
(суть, подходящая услуга, срочность). Без Ollama бот работает так же,
просто без блока «Разбор».

Если заданы ESPOCRM_URL и ESPOCRM_API_KEY — каждая заявка дополнительно
создаётся лидом в EspoCRM. Доставка заявки владельцу от CRM не зависит.

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
ESPOCRM_URL = os.environ.get("ESPOCRM_URL", "")  # напр. https://qopq.online:8443
ESPOCRM_API_KEY = os.environ.get("ESPOCRM_API_KEY", "")

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
    # связки со страницы услуг
    "bundle-server": "Связка «Сервер под присмотром» (от 23 900 ₽)",
    "bundle-deploy": "Связка «Деплой без рук» (от 42 000 ₽)",
    "bundle-ai": "Связка «ИИ в контуре» (от 64 800 ₽)",
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
    "a": ("Настройка VPS «под ключ»", 8400, ""),
    "b": ("Аудит существующего сервера", 4800, ""),
    "c": ("nginx: домены, SSL, реверс-прокси", 6000, ""),
    "d": ("Миграция на новый сервер", 14400, ""),
    "e": ("Резервное копирование", 9600, ""),
    "f": ("Docker-изация приложения", 12000, ""),
    "g": ("docker-compose стек", 18000, ""),
    "h": ("CI/CD пайплайн", 18000, ""),
    "i": ("Массовое развёртывание", 30000, ""),
    "j": ("Мониторинг + алерты в Telegram", 18000, ""),
    "k": ("Балансировка нагрузки", 21600, ""),
    "l": ("Автоматический failover", 36000, ""),
    "m": ("Self-hosted ИИ (Ollama)", 24000, ""),
    "n": ("ИИ-агент / Telegram-бот", 48000, ""),
    "o": ("Система под ключ", 192000, ""),
    "p": ("Абонентское администрирование", 12000, "/мес"),
    "q": ("Разовая консультация", 4800, "/час"),
    "r": ("Срочный выезд в инцидент", 7200, ""),
}


# Связки: если все коды связки есть в заказе — применяется комбо-скидка.
# Составы и суммы должны совпадать с bundleCodes/bundles на сайте.
CALC_BUNDLES: list[tuple[str, int, str]] = [
    ("aj", 2500, "Сервер под присмотром"),
    ("fgh", 6000, "Деплой без рук"),
    ("mn", 7200, "ИИ в контуре"),
]


def fmt_rub(n: int) -> str:
    """12345 → '12 345' (пробел — разделитель тысяч, названия не трогаем)."""
    return f"{n:,}".replace(",", " ")


def parse_calc(slug: str) -> tuple[str, str]:
    """calc-<коды> → (текст состава заказа, краткий источник). Пустые строки, если не калькулятор."""
    if not slug.startswith("calc-"):
        return "", ""
    codes = slug[5:]
    total = 0
    monthly = 0
    lines = []
    for code in codes:
        item = CALC_ITEMS.get(code)
        if not item:
            continue
        name, price, suffix = item
        lines.append(f"· {name} — от {fmt_rub(price)} ₽{suffix}")
        if suffix == "/мес":
            monthly += price
        else:
            total += price
    if not lines:
        return "", ""
    n_items = len(lines)
    for combo_codes, discount, name in CALC_BUNDLES:
        if all(c in codes for c in combo_codes):
            total -= discount
            lines.append(f"🎁 Комбо «{name}» — скидка {fmt_rub(discount)} ₽")
    summary = f"Итого: от {fmt_rub(total)} ₽"
    if monthly:
        summary += f" + от {fmt_rub(monthly)} ₽/мес"
    order = "\n".join(lines) + f"\n{summary}"
    return order, f"Калькулятор на сайте ({n_items} поз.)"


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


# ── лид в EspoCRM (опционально) ──────────────────────────────────────────────

async def create_crm_lead(
    name: str, task: str, phone: str, email: str,
    source: str, order: str, tg_username: str, tg_id: int,
) -> None:
    if not (ESPOCRM_URL and ESPOCRM_API_KEY):
        return
    desc_parts = []
    if source:
        desc_parts.append(f"Откуда: {source}")
    if order:
        desc_parts.append(f"Заказ из калькулятора:\n{order}")
    if task:
        desc_parts.append(f"Задача:\n{task}")
    tg = f"@{tg_username}" if tg_username else f"id {tg_id}"
    desc_parts.append(f"Telegram: {tg} (id {tg_id})")
    payload = {
        "lastName": name,
        "description": "\n\n".join(desc_parts),
    }
    if phone:
        payload["phoneNumber"] = phone
    if email:
        payload["emailAddress"] = email
    try:
        import aiohttp

        async with aiohttp.ClientSession() as s:
            async with s.post(
                f"{ESPOCRM_URL.rstrip('/')}/api/v1/Lead",
                json=payload,
                headers={"X-Api-Key": ESPOCRM_API_KEY},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as r:
                if r.status in (200, 201):
                    log.info("Лид создан в CRM (%s)", name)
                else:
                    log.warning("CRM ответила %s: %s", r.status, (await r.text())[:300])
    except Exception as e:  # CRM — бонус, заявка важнее
        log.warning("CRM недоступна: %s", e)


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

    # кнопка с именем из Telegram-профиля — чтобы не печатать руками
    first_name = (message.from_user.first_name or "").strip()
    name_rows = []
    if 2 <= len(first_name) <= 80:
        name_rows.append([KeyboardButton(text=first_name)])
    name_rows.append([KeyboardButton(text=CANCEL)])

    await message.answer(
        intro + "Я приму вашу заявку и сразу передам её инженеру opsmith — "
        "он ответит в течение дня.\n\n"
        "Как вас зовут? Напишите или нажмите кнопку ниже.",
        parse_mode="HTML",
        reply_markup=kb(*name_rows),
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
    data = await state.get_data()
    if data.get("order"):
        # состав заказа уже известен из калькулятора — описание опционально
        await message.answer(
            f"Приятно познакомиться, {name}!\n\n"
            "Состав заказа у меня уже есть. Хотите добавить пару слов о проекте "
            "и сроках? Напишите — или нажмите «Пропустить».",
            reply_markup=KB_SKIP,
        )
    else:
        await message.answer(
            f"Приятно познакомиться, {name}!\n\n"
            "Опишите задачу свободным текстом: что за проект, что нужно сделать, "
            "какие сроки. Пишите как умеете — переведу на технический сам 🙂",
            reply_markup=kb([KeyboardButton(text=CANCEL)]),
        )


@router.message(Form.task, F.text)
async def form_task(message: Message, state: FSMContext) -> None:
    task = message.text.strip()
    data = await state.get_data()
    has_order = bool(data.get("order"))
    if task == SKIP and has_order:
        task = ""
    elif len(task) < 15 and not has_order:
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
    analysis = await analyze_task(task) if task else ""

    parts = [
        "🆕 <b>Новая заявка с сайта</b>",
        "",
        f"👤 <b>Имя:</b> {html.escape(name)}",
    ]
    if source:
        parts.append(f"🔗 <b>Откуда:</b> {html.escape(source)}")
    if order:
        parts.append(f"🧮 <b>Заказ из калькулятора:</b>\n{html.escape(order)}")
    if task:
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
    await create_crm_lead(
        name, task, phone, email, source, order, user.username or "", user.id
    )


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
