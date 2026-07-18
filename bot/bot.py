"""
Бот приёма заявок с лендинга — с меню, каталогом услуг и живым чатом.

Что умеет:
- Главное меню: заявка, каталог услуг с ценами, FAQ, «мои заявки», вопрос инженеру.
- Форма заявки (имя → задача → телефон → почта) с предпросмотром и
  редактированием любого поля перед отправкой.
- Каталог услуг по категориям — цены совпадают с прайсом сайта
  (src/data/pricing.ts); из карточки услуги можно сразу оформить заявку.
- Заявки сохраняются в SQLite: у каждой номер и статус (новая → в работе →
  закрыта). Клиент видит свои заявки, владелец переключает статусы кнопками
  под заявкой — клиенту приходит уведомление.
- Чат с инженером: клиент пишет вопрос, владелец отвечает кнопкой «Ответить»
  прямо из Telegram — бот пересылает сообщения в обе стороны.
- Deep-links с сайта (t.me/<бот>?start=<slug>) работают как раньше: бот знает,
  с какой кнопки или из какого набора калькулятора пришёл клиент.

Если задан OLLAMA_URL — описание задачи прогоняется через локальную LLM
(структурированный разбор в заявке), а на вопросы в чате бот присылает
предварительный ответ ИИ, пока инженер не ответил лично.

Если заданы ESPOCRM_URL и ESPOCRM_API_KEY — каждая заявка дополнительно
создаётся лидом в EspoCRM. Доставка заявки владельцу от CRM не зависит.

Настройка — через переменные окружения (см. .env.example и README.md).
"""

import asyncio
import html
import logging
import os
import re
import sqlite3
import time
from datetime import datetime, timedelta, timezone

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandObject, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BotCommand,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_CHAT_ID = int(os.environ["ADMIN_CHAT_ID"])
OLLAMA_URL = os.environ.get("OLLAMA_URL", "")  # напр. http://127.0.0.1:11434
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma2")
# на CPU генерация медленная — таймаут с запасом; заявки от LLM не зависят
OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "180"))
ESPOCRM_URL = os.environ.get("ESPOCRM_URL", "")  # напр. https://qopq.online:8443
ESPOCRM_API_KEY = os.environ.get("ESPOCRM_API_KEY", "")
LEADS_DB = os.environ.get("LEADS_DB", "leads.db")

SITE_URL = "https://opsmith.ru"
CALENDLY_URL = "https://calendly.com/opsmith/30min"

MSK = timezone(timedelta(hours=3))
PHONE_RE = re.compile(r"^\+?[\d\s\-()]{7,20}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# пауза между отправками заявок одним пользователем (защита от даблкликов и спама)
LEAD_COOLDOWN_S = 120
_last_lead_at: dict[int, float] = {}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("orders-bot")

router = Router()


class Form(StatesGroup):
    name = State()
    task = State()
    phone = State()
    email = State()
    confirm = State()


class ChatMode(StatesGroup):
    active = State()  # клиент пишет инженеру


class AdminReply(StatesGroup):
    wait = State()  # владелец пишет ответ клиенту


SKIP = "Пропустить"
CANCEL = "Отмена"

# Deep-link payload (t.me/<bot>?start=<slug>) → откуда пришёл клиент.
# Слаги должны совпадать с src/data/pricing.ts на сайте.
# EN-страницы шлют те же слаги с суффиксом -en (см. cmd_start).
SOURCES = {
    # прайс: серверы и безопасность
    "vps-setup": "Настройка VPS/VDS «под ключ»",
    "audit": "Аудит сервера и безопасности",
    "hardening": "Хардненинг: fail2ban, ufw, SSH, обновления",
    "nginx-ssl": "nginx: домены, SSL, реверс-прокси",
    "migration": "Миграция на новый сервер",
    "backup": "Автоматическое резервное копирование",
    "mail": "Self-hosted почта: DKIM/SPF/DMARC",
    # прайс: Docker и CI/CD
    "dockerize": "Docker-изация приложения",
    "compose": "docker-compose стек",
    "cicd": "CI/CD пайплайн",
    "registry": "Приватный Docker Registry",
    "iac": "Инфраструктура как код (Ansible / Terraform)",
    # прайс: Kubernetes
    "k8s-cluster": "Кластер Kubernetes под ключ",
    "k8s-migrate": "Миграция приложений в Kubernetes",
    "gitops": "Helm-чарты и GitOps (ArgoCD)",
    "k8s-audit": "Аудит и оптимизация кластера",
    # прайс: облака
    "cloud-migrate": "Миграция в облако / между облаками",
    "cost-opt": "Оптимизация облачных расходов",
    "multi-env": "Стейджинг и дев-окружения",
    # прайс: мониторинг и SRE
    "monitoring": "Мониторинг + алерты в Telegram",
    "logging": "Централизованные логи (Loki / ELK)",
    "balancer": "Балансировка нагрузки",
    "failover": "Автоматический failover",
    "loadtest": "Нагрузочное тестирование",
    # прайс: базы данных
    "db-setup": "Установка и тюнинг PostgreSQL / MySQL",
    "db-replica": "Репликация и бэкапы БД",
    "db-migrate": "Миграция БД без простоя",
    # прайс: ИИ
    "ollama": "Self-hosted ИИ (Ollama)",
    "ai-bot": "ИИ-агент / Telegram-бот",
    "turnkey": "Система под ключ",
    # прайс: поддержка
    "subscription": "Абонентское администрирование",
    "consult": "Разовая консультация",
    "incident": "Срочное реагирование на инцидент",
    "hourly": "Часовая ставка инженера",
    # кнопка «Не нашли свою задачу?» на странице услуг
    "custom": "индивидуальная задача (вне прайса)",
    # общие кнопки «Оставить заявку» по страницам
    "src-home": "кнопка на главной странице",
    "src-cases": "кнопка на странице кейсов",
    "src-services": "кнопка на странице услуг и цен",
    "src-work": "кнопка на странице «Процесс»",
}

# Для этих слагов бот упоминает услугу в приветствии (страницы-источники — нет).
SERVICE_SLUGS = {s for s in SOURCES if not s.startswith("src-")}

# Калькулятор на сайте кодирует выбранные позиции однобуквенными кодами
# (payload вида calc-adG; регистр значим). Коды, цены и «от» должны совпадать
# с src/data/pricing.ts.
CALC_ITEMS: dict[str, tuple[str, int, str, bool]] = {
    # код: (название, стартовая цена ₽, суффикс цены, цена «от …»)
    "a": ("Настройка VPS/VDS «под ключ»", 8400, "", True),
    "b": ("Аудит сервера и безопасности", 4800, "", False),
    "c": ("Хардненинг: fail2ban, ufw, SSH, обновления", 7200, "", True),
    "d": ("nginx: домены, SSL, реверс-прокси", 6000, "", True),
    "e": ("Миграция на новый сервер", 14400, "", True),
    "f": ("Автоматическое резервное копирование", 9600, "", True),
    "g": ("Self-hosted почта: DKIM/SPF/DMARC", 18000, "", True),
    "h": ("Docker-изация приложения", 12000, "", True),
    "i": ("docker-compose стек (БД, кэш, очереди)", 18000, "", True),
    "j": ("CI/CD пайплайн (GitLab CI / GitHub Actions)", 18000, "", True),
    "k": ("Приватный Docker Registry", 9600, "", True),
    "l": ("Инфраструктура как код (Ansible / Terraform)", 30000, "", True),
    "m": ("Кластер Kubernetes под ключ (k3s / k8s)", 48000, "", True),
    "n": ("Миграция приложений в Kubernetes", 36000, "", True),
    "o": ("Helm-чарты и GitOps (ArgoCD)", 24000, "", True),
    "p": ("Аудит и оптимизация кластера", 14400, "", True),
    "q": ("Миграция в облако / между облаками", 24000, "", True),
    "r": ("Оптимизация облачных расходов", 18000, "", True),
    "s": ("Стейджинг и дев-окружения", 14400, "", True),
    "t": ("Мониторинг + алерты в Telegram", 18000, "", True),
    "u": ("Централизованные логи (Loki / ELK)", 16800, "", True),
    "v": ("Балансировка нагрузки", 21600, "", True),
    "w": ("Автоматический failover", 36000, "", True),
    "x": ("Нагрузочное тестирование", 14400, "", True),
    "y": ("Установка и тюнинг PostgreSQL / MySQL", 12000, "", True),
    "z": ("Репликация и бэкапы БД", 18000, "", True),
    "A": ("Миграция БД без простоя", 24000, "", True),
    "B": ("Self-hosted ИИ (Ollama)", 24000, "", True),
    "C": ("ИИ-агент / Telegram-бот", 48000, "", True),
    "D": ("Система под ключ", 192000, "", True),
    "E": ("Абонентское администрирование", 12000, "/мес", True),
    "F": ("Разовая консультация", 4800, "", False),
    "G": ("Срочное реагирование на инцидент", 7200, "", True),
    "H": ("Часовая ставка инженера", 3600, "/час", True),
}


# Связки: если все коды связки есть в заказе — применяется комбо-скидка.
# Составы и суммы должны совпадать с BUNDLES в src/data/pricing.ts.
CALC_BUNDLES: list[tuple[str, int, str]] = [
    ("at", 2500, "Сервер под присмотром"),
    ("hij", 6000, "Деплой без рук"),
    ("BC", 7200, "ИИ в контуре"),
    ("mo", 9000, "Kubernetes + GitOps"),
    ("adcf", 4500, "Старт: сервер под ключ"),
    ("ef", 2400, "Переезд без потерь"),
    ("yz", 3000, "База под защитой"),
    ("tu", 3500, "Полная наблюдаемость"),
    ("vw", 5000, "Высокая доступность"),
    ("tw", 4000, "Отказоустойчивость 24/7"),
    ("jk", 2500, "Конвейер поставки"),
]

# Каталог в боте: категории прайса → коды позиций из CALC_ITEMS.
CATEGORIES: list[tuple[str, str]] = [
    ("🖥 Серверы и безопасность", "abcdefg"),
    ("🐳 Docker и CI/CD", "hijkl"),
    ("☸️ Kubernetes", "mnop"),
    ("☁️ Облака", "qrs"),
    ("📈 Мониторинг и SRE", "tuvwx"),
    ("🗄 Базы данных", "yzA"),
    ("🤖 ИИ и автоматизация", "BCD"),
    ("🛟 Поддержка и консультации", "EFGH"),
]

# FAQ — тексты совпадают с блоком FAQ на сайте (src/i18n/ru.ts).
FAQ: list[tuple[str, str]] = [
    ("Сколько стоит настройка VPS?",
     "От 8 400 ₽ за базовую настройку под Docker: пользователи и SSH-ключи через "
     "cloud-init, firewall, автообновления. Точная смета фиксируется письменно "
     "после короткого созвона и не растёт по ходу работы."),
    ("Работаете с уже существующей инфраструктурой?",
     "Да. Начинаем с аудита: смотрим, что развёрнуто, находим риски и узкие места, "
     "возвращаемся с планом. Ничего не ломаем и не переносим без согласования — "
     "сначала план, потом изменения."),
    ("Что, если что-то сломается после сдачи?",
     "На все работы действует гарантийный период: если проблема в нашей настройке — "
     "чиним бесплатно. Дальше по желанию — абонентская поддержка от 12 000 ₽/мес "
     "с мониторингом и реакцией на инциденты."),
    ("Какие сроки типичны?",
     "Настройка VPS — 1–2 дня, мониторинг — 2–3 дня, self-hosted ИИ — от недели, "
     "системы под ключ — от месяца. Сроки фиксируются в смете вместе с ценой."),
    ("Вам нужен root-доступ к нашим серверам?",
     "На время работ — да, через отдельного пользователя с вашим контролем. После "
     "сдачи все доступы остаются у вас, наши учётки удаляются или отзываются. "
     "Всё воспроизводится из кода в вашем репозитории."),
    ("Как происходит оплата?",
     "По этапам из сметы: часть до начала, часть после сдачи с проверкой результата. "
     "Для абонентки — ежемесячно. Работаем по договору с самозанятым/ИП."),
]

STATUS_LABELS = {"new": "🆕 новая", "work": "🔧 в работе", "done": "✅ закрыта"}


# ── база заявок (SQLite) ─────────────────────────────────────────────────────

db = sqlite3.connect(LEADS_DB)
db.row_factory = sqlite3.Row
db.execute(
    """CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        username TEXT,
        name TEXT,
        task TEXT,
        phone TEXT,
        email TEXT,
        source TEXT,
        order_text TEXT,
        status TEXT NOT NULL DEFAULT 'new'
    )"""
)
db.commit()


def db_add_lead(user_id: int, username: str, name: str, task: str,
                phone: str, email: str, source: str, order_text: str) -> int:
    cur = db.execute(
        "INSERT INTO leads (ts, user_id, username, name, task, phone, email, source, order_text) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (datetime.now(MSK).isoformat(timespec="seconds"), user_id, username,
         name, task, phone, email, source, order_text),
    )
    db.commit()
    return cur.lastrowid


def db_user_leads(user_id: int) -> list[sqlite3.Row]:
    return db.execute(
        "SELECT * FROM leads WHERE user_id = ? ORDER BY id DESC LIMIT 10", (user_id,)
    ).fetchall()


def db_set_status(lead_id: int, status: str) -> sqlite3.Row | None:
    db.execute("UPDATE leads SET status = ? WHERE id = ?", (status, lead_id))
    db.commit()
    return db.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()


def db_stats() -> dict:
    by_status = {r["status"]: r["n"] for r in db.execute(
        "SELECT status, COUNT(*) AS n FROM leads GROUP BY status")}
    week_from = (datetime.now(MSK) - timedelta(days=7)).isoformat(timespec="seconds")
    week = db.execute(
        "SELECT COUNT(*) AS n FROM leads WHERE ts >= ?", (week_from,)).fetchone()["n"]
    return {"by_status": by_status, "total": sum(by_status.values()), "week": week}


# ── утилиты ──────────────────────────────────────────────────────────────────

def fmt_rub(n: int) -> str:
    """12345 → '12 345' (пробел — разделитель тысяч, названия не трогаем)."""
    return f"{n:,}".replace(",", " ")


def item_price(code: str) -> str:
    name, price, suffix, from_flag = CALC_ITEMS[code]
    return f"{'от ' if from_flag else ''}{fmt_rub(price)} ₽{suffix}"


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
        name, price, suffix, from_flag = item
        prefix = "от " if from_flag else ""
        lines.append(f"· {name} — {prefix}{fmt_rub(price)} ₽{suffix}")
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
    total = max(total, 0)
    summary = f"Итого: от {fmt_rub(total)} ₽"
    if monthly:
        summary += f" + от {fmt_rub(monthly)} ₽/мес"
    order = "\n".join(lines) + f"\n{summary}"
    return order, f"Калькулятор на сайте ({n_items} поз.)"


def kb(*rows: list[KeyboardButton]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=list(rows), resize_keyboard=True, one_time_keyboard=True)


def ikb(*rows: list[InlineKeyboardButton]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=list(rows))


def btn(text: str, data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=data)


KB_SKIP = kb([KeyboardButton(text=SKIP)], [KeyboardButton(text=CANCEL)])
KB_PHONE = kb(
    [KeyboardButton(text="📞 Отправить мой номер", request_contact=True)],
    [KeyboardButton(text=SKIP)],
    [KeyboardButton(text=CANCEL)],
)


def main_menu_kb() -> InlineKeyboardMarkup:
    return ikb(
        [btn("📝 Оставить заявку", "lead")],
        [btn("🛠 Услуги и цены", "svc"), btn("❓ FAQ", "faq")],
        [btn("💬 Вопрос инженеру", "chat"), btn("📂 Мои заявки", "my")],
        [
            InlineKeyboardButton(text="🌐 Сайт", url=SITE_URL),
            InlineKeyboardButton(text="📅 Созвон 30 мин", url=CALENDLY_URL),
        ],
    )


MENU_TEXT = (
    "👋 Это бот <b>opsmith</b> — DevOps-инженерия: серверы, Docker, CI/CD, "
    "Kubernetes, мониторинг, базы данных, self-hosted ИИ.\n\n"
    "Чем помочь?"
)


async def show_menu(message: Message) -> None:
    await message.answer(MENU_TEXT, parse_mode="HTML", reply_markup=main_menu_kb())


# ── LLM (опционально, через локальную Ollama) ────────────────────────────────

async def ollama_generate(prompt: str, max_tokens: int = 300) -> str:
    if not OLLAMA_URL:
        return ""
    try:
        import aiohttp

        async with aiohttp.ClientSession() as s:
            async with s.post(
                f"{OLLAMA_URL.rstrip('/')}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    # без «размышлений»: на CPU они съедают весь лимит токенов
                    "think": False,
                    # stop: gemma4:e2b иногда пишет служебный <channel|> и
                    # повторяет ответ — обрезаем; другим моделям не мешает
                    "options": {"num_predict": max_tokens, "stop": ["<channel|>"]},
                },
                timeout=aiohttp.ClientTimeout(total=OLLAMA_TIMEOUT),
            ) as r:
                if r.status != 200:
                    log.warning("Ollama ответила %s: %s", r.status, (await r.text())[:200])
                    return ""
                data = await r.json()
                return (data.get("response") or "").strip()
    except Exception as e:  # LLM — приятный бонус, основной сценарий важнее
        log.warning("Ollama недоступна: %r", e)
        return ""


async def analyze_task(text: str) -> str:
    return await ollama_generate(
        "Ты — ассистент DevOps-инженера. Клиент оставил заявку. Сразу выдай ответ "
        "по формату ниже — без вступлений, плана и рассуждений.\n"
        "Короткий разбор по-русски, строго в формате:\n"
        "Суть: <одно предложение — что нужно клиенту>\n"
        "Услуга: <какая услуга подходит: настройка VPS / Docker и CI/CD / мониторинг / "
        "Telegram-бот / self-hosted ИИ / система под ключ / консультация>\n"
        "Срочность: <низкая / средняя / высокая — по тексту заявки>\n"
        "Вопросы: <1-2 уточняющих вопроса клиенту>\n"
        f"\nТекст заявки:\n{text}",
        max_tokens=350,
    )


async def draft_answer(question: str) -> str:
    return await ollama_generate(
        "Ты — ассистент DevOps-студии opsmith (настройка VPS, Docker и CI/CD, "
        "Kubernetes, мониторинг, базы данных, self-hosted ИИ, Telegram-боты). "
        "Клиент задал вопрос в Telegram-боте. Сразу напиши ответ — без плана "
        "и рассуждений. По-русски, дружелюбно и коротко (до 80 слов). "
        "Не выдумывай цены и сроки — если спрашивают точную стоимость, скажи, "
        "что смету зафиксирует инженер после короткого разговора, и предложи "
        "оставить заявку.\n\n"
        f"Вопрос клиента:\n{question}",
        max_tokens=220,
    )


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


# ── команды и главное меню ───────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, command: CommandObject) -> None:
    await state.clear()
    slug = (command.args or "").strip()
    if not slug:
        await show_menu(message)
        return

    # EN-страницы сайта шлют те же метки с суффиксом -en — фиксируем язык клиента
    lang_en = slug.endswith("-en") and not slug.startswith("calc-")
    if lang_en:
        slug = slug[: -len("-en")]
    order, calc_source = parse_calc(slug)
    source = calc_source or SOURCES.get(slug, "")
    if source and lang_en:
        source += " · EN-версия сайта"
    await state.update_data(source=source, source_slug=slug if source else "", order=order)

    if order:
        intro = (
            "Привет! Получил ваш заказ из калькулятора:\n\n"
            f"<b>{html.escape(order)}</b>\n\n"
        )
    elif slug in SERVICE_SLUGS:
        intro = f"Привет! Вижу, вас интересует <b>{html.escape(source)}</b> — отличный выбор.\n"
    else:
        intro = "Привет! "
    await start_form(message, state, intro)


async def start_form(message: Message, state: FSMContext, intro: str = "") -> None:
    """Запуск формы заявки: спрашиваем имя (данные source/order уже в state)."""
    await state.set_state(Form.name)
    # кнопка с именем из Telegram-профиля — чтобы не печатать руками
    first_name = (message.chat.first_name or "").strip()
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


@router.message(Command("menu"))
@router.message(Command("help"))
async def cmd_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Команды:\n"
        "/start — начать сначала\n"
        "/services — услуги и цены\n"
        "/faq — частые вопросы\n"
        "/ask — задать вопрос инженеру\n"
        "/status — мои заявки\n"
        "/cancel — отменить текущее действие",
        reply_markup=ReplyKeyboardRemove(),
    )
    await show_menu(message)


@router.message(Command("cancel"))
@router.message(F.text == CANCEL)
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Ок, отменил.", reply_markup=ReplyKeyboardRemove())
    await show_menu(message)


@router.callback_query(F.data == "menu")
async def cb_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    try:
        await callback.message.edit_text(
            MENU_TEXT, parse_mode="HTML", reply_markup=main_menu_kb()
        )
    except Exception:
        await show_menu(callback.message)


# ── каталог услуг ────────────────────────────────────────────────────────────

def categories_kb() -> InlineKeyboardMarkup:
    rows = [[btn(title, f"svc:{i}")] for i, (title, _) in enumerate(CATEGORIES)]
    rows.append([btn("‹ Меню", "menu")])
    return ikb(*rows)


@router.message(Command("services"))
async def cmd_services(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "🛠 <b>Услуги и цены</b>\nВыберите направление:",
        parse_mode="HTML", reply_markup=categories_kb(),
    )


@router.callback_query(F.data == "svc")
async def cb_services(callback: CallbackQuery) -> None:
    await callback.answer()
    try:
        await callback.message.edit_text(
            "🛠 <b>Услуги и цены</b>\nВыберите направление:",
            parse_mode="HTML", reply_markup=categories_kb(),
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("svc:"))
async def cb_category(callback: CallbackQuery) -> None:
    await callback.answer()
    try:
        idx = int(callback.data.split(":", 1)[1])
        title, codes = CATEGORIES[idx]
    except (ValueError, IndexError):
        return
    lines = [f"{title}", ""]
    rows = []
    for code in codes:
        name, *_ = CALC_ITEMS[code]
        lines.append(f"· {name} — <b>{item_price(code)}</b>")
        rows.append([btn(name[:56], f"ord:{code}")])
    lines += ["", "Нажмите услугу, чтобы оформить заявку 👇"]
    rows.append([btn("‹ Направления", "svc"), btn("‹ Меню", "menu")])
    try:
        await callback.message.edit_text(
            "\n".join(lines), parse_mode="HTML", reply_markup=ikb(*rows),
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("ord:"))
async def cb_order_item(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    code = callback.data.split(":", 1)[1]
    item = CALC_ITEMS.get(code)
    if not item:
        return
    name = item[0]
    await state.clear()
    await state.update_data(source=f"{name} (каталог в боте)", order="")
    await start_form(
        callback.message, state,
        f"Отличный выбор: <b>{html.escape(name)}</b> — {item_price(code)}.\n",
    )


@router.callback_query(F.data == "lead")
async def cb_lead(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    await start_form(callback.message, state)


# ── FAQ ──────────────────────────────────────────────────────────────────────

def faq_kb() -> InlineKeyboardMarkup:
    rows = [[btn(q, f"faq:{i}")] for i, (q, _) in enumerate(FAQ)]
    rows.append([btn("‹ Меню", "menu")])
    return ikb(*rows)


@router.message(Command("faq"))
async def cmd_faq(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "❓ <b>Частые вопросы</b>", parse_mode="HTML", reply_markup=faq_kb()
    )


@router.callback_query(F.data == "faq")
async def cb_faq(callback: CallbackQuery) -> None:
    await callback.answer()
    try:
        await callback.message.edit_text(
            "❓ <b>Частые вопросы</b>", parse_mode="HTML", reply_markup=faq_kb()
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("faq:"))
async def cb_faq_item(callback: CallbackQuery) -> None:
    await callback.answer()
    try:
        q, a = FAQ[int(callback.data.split(":", 1)[1])]
    except (ValueError, IndexError):
        return
    try:
        await callback.message.edit_text(
            f"<b>{html.escape(q)}</b>\n\n{html.escape(a)}",
            parse_mode="HTML",
            reply_markup=ikb(
                [btn("‹ Другие вопросы", "faq")],
                [btn("📝 Оставить заявку", "lead"), btn("‹ Меню", "menu")],
            ),
        )
    except Exception:
        pass


# ── мои заявки ───────────────────────────────────────────────────────────────

def my_leads_text(user_id: int) -> str:
    rows = db_user_leads(user_id)
    if not rows:
        return "У вас пока нет заявок. Оформим первую? 🙂"
    lines = ["📂 <b>Ваши заявки:</b>", ""]
    for r in rows:
        ts = datetime.fromisoformat(r["ts"]).strftime("%d.%m.%Y")
        about = r["source"] or (r["task"] or "")[:60] or "заявка"
        lines.append(
            f"<b>#{r['id']}</b> · {ts} · {STATUS_LABELS.get(r['status'], r['status'])}\n"
            f"    {html.escape(about)}"
        )
    return "\n".join(lines)


@router.message(Command("status"))
async def cmd_status(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        my_leads_text(message.from_user.id), parse_mode="HTML",
        reply_markup=ikb([btn("📝 Новая заявка", "lead"), btn("‹ Меню", "menu")]),
    )


@router.callback_query(F.data == "my")
async def cb_my(callback: CallbackQuery) -> None:
    await callback.answer()
    try:
        await callback.message.edit_text(
            my_leads_text(callback.from_user.id), parse_mode="HTML",
            reply_markup=ikb([btn("📝 Новая заявка", "lead"), btn("‹ Меню", "menu")]),
        )
    except Exception:
        pass


# ── статистика для владельца ─────────────────────────────────────────────────

@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    if message.chat.id != ADMIN_CHAT_ID:
        return
    s = db_stats()
    by = s["by_status"]
    await message.answer(
        "📊 <b>Заявки</b>\n\n"
        f"Всего: <b>{s['total']}</b> · за 7 дней: <b>{s['week']}</b>\n"
        f"🆕 Новые: {by.get('new', 0)}\n"
        f"🔧 В работе: {by.get('work', 0)}\n"
        f"✅ Закрытые: {by.get('done', 0)}",
        parse_mode="HTML",
    )


# ── форма заявки ─────────────────────────────────────────────────────────────

@router.message(Form.name, F.text)
async def form_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if len(name) < 2 or len(name) > 80:
        await message.answer("Напишите, пожалуйста, имя текстом (2–80 символов).")
        return
    await state.update_data(name=name)
    data = await state.get_data()
    if data.pop("editing", None):
        await state.update_data(editing=None)
        await show_preview(message, state)
        return
    await state.set_state(Form.task)
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
    if data.get("editing"):
        await state.update_data(editing=None)
        await show_preview(message, state)
        return
    await state.set_state(Form.phone)
    await message.answer(
        "Принял! Оставите телефон для связи? Можно отправить кнопкой ниже, "
        "написать вручную или пропустить.",
        reply_markup=KB_PHONE,
    )


@router.message(Form.phone, F.contact)
async def form_phone_contact(message: Message, state: FSMContext) -> None:
    await state.update_data(phone=message.contact.phone_number)
    await after_phone(message, state)


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
    await after_phone(message, state)


async def after_phone(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=None)
        await show_preview(message, state)
        return
    await state.set_state(Form.email)
    await message.answer(
        "И почта — если удобнее переписываться письмами (или «Пропустить»).",
        reply_markup=KB_SKIP,
    )


@router.message(Form.email, F.text)
async def form_email(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if text == SKIP:
        email = ""
    elif EMAIL_RE.match(text):
        email = text
    else:
        await message.answer("Не похоже на почту. Ещё раз — или нажмите «Пропустить».")
        return
    await state.update_data(email=email, editing=None)
    await show_preview(message, state)


def preview_text(data: dict) -> str:
    parts = ["📋 <b>Проверьте заявку перед отправкой:</b>", ""]
    parts.append(f"👤 Имя: <b>{html.escape(data.get('name', ''))}</b>")
    if data.get("source"):
        parts.append(f"🔗 Откуда: {html.escape(data['source'])}")
    if data.get("order"):
        parts.append(f"🧮 Заказ:\n{html.escape(data['order'])}")
    task = data.get("task") or "—"
    parts.append(f"📝 Задача: {html.escape(task)}")
    parts.append(f"📞 Телефон: {html.escape(data.get('phone') or '—')}")
    parts.append(f"✉ Почта: {html.escape(data.get('email') or '—')}")
    return "\n".join(parts)


def confirm_kb() -> InlineKeyboardMarkup:
    return ikb(
        [btn("✅ Всё верно — отправить", "send")],
        [btn("✏️ Имя", "edit:name"), btn("✏️ Задача", "edit:task")],
        [btn("✏️ Телефон", "edit:phone"), btn("✏️ Почта", "edit:email")],
        [btn("❌ Отмена", "abort")],
    )


async def show_preview(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.confirm)
    data = await state.get_data()
    await message.answer(
        preview_text(data), parse_mode="HTML", reply_markup=confirm_kb()
    )


@router.message(Form.confirm, F.text)
async def confirm_hint(message: Message) -> None:
    await message.answer("Нажмите кнопку под заявкой 👆 — или /cancel, чтобы отменить.")


@router.callback_query(Form.confirm, F.data.startswith("edit:"))
async def cb_edit(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    field = callback.data.split(":", 1)[1]
    await state.update_data(editing=True)
    msg = callback.message
    if field == "name":
        await state.set_state(Form.name)
        await msg.answer("Как вас зовут?", reply_markup=kb([KeyboardButton(text=CANCEL)]))
    elif field == "task":
        await state.set_state(Form.task)
        data = await state.get_data()
        markup = KB_SKIP if data.get("order") else kb([KeyboardButton(text=CANCEL)])
        await msg.answer("Опишите задачу:", reply_markup=markup)
    elif field == "phone":
        await state.set_state(Form.phone)
        await msg.answer("Телефон для связи:", reply_markup=KB_PHONE)
    elif field == "email":
        await state.set_state(Form.email)
        await msg.answer("Почта:", reply_markup=KB_SKIP)


@router.callback_query(Form.confirm, F.data == "abort")
async def cb_abort(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer("Отменено")
    await state.clear()
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await callback.message.answer("Ок, отменил.", reply_markup=ReplyKeyboardRemove())
    await show_menu(callback.message)


@router.callback_query(Form.confirm, F.data == "send")
async def cb_send(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    user_id = callback.from_user.id
    now = time.monotonic()
    if now - _last_lead_at.get(user_id, -LEAD_COOLDOWN_S) < LEAD_COOLDOWN_S:
        await callback.answer(
            "Заявка уже отправлена — инженер скоро ответит 🙂", show_alert=True
        )
        return
    _last_lead_at[user_id] = now

    data = await state.get_data()
    await state.clear()
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await callback.answer()

    lead_id = db_add_lead(
        user_id, callback.from_user.username or "",
        data.get("name", ""), data.get("task", ""), data.get("phone", ""),
        data.get("email", ""), data.get("source", ""), data.get("order", ""),
    )
    await callback.message.answer(
        f"Готово, заявка <b>#{lead_id}</b> ушла! 🚀\n"
        "Инженер opsmith свяжется с вами в течение дня. Спасибо!\n\n"
        "Статус можно смотреть в «📂 Мои заявки». Если хотите что-то добавить — "
        "жмите «💬 Вопрос инженеру».",
        parse_mode="HTML",
        reply_markup=ikb(
            [btn("📂 Мои заявки", "my"), btn("💬 Написать инженеру", "chat")],
        ),
    )
    await send_lead(bot, callback.from_user, lead_id, data)


async def send_lead(bot: Bot, user, lead_id: int, data: dict) -> None:
    name = data.get("name", "")
    task = data.get("task", "")
    phone = data.get("phone", "")
    email = data.get("email", "")
    source = data.get("source", "")
    order = data.get("order", "")
    tg_line = (
        f"@{user.username}"
        if user.username
        else f'<a href="tg://user?id={user.id}">профиль без юзернейма</a>'
    )

    parts = [
        f"🆕 <b>Заявка #{lead_id}</b>",
        "",
        f"👤 <b>Имя:</b> {html.escape(name)}",
    ]
    if source:
        parts.append(f"🔗 <b>Откуда:</b> {html.escape(source)}")
    if order:
        parts.append(f"🧮 <b>Заказ из калькулятора:</b>\n{html.escape(order)}")
    if task:
        parts.append(f"📝 <b>Задача:</b>\n{html.escape(task)}")
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
            reply_markup=admin_lead_kb(lead_id, user.id),
        )
        log.info("Заявка #%s от %s (id %s) доставлена", lead_id, name, user.id)
    except Exception:
        log.exception("Не удалось доставить заявку админу")
    # LLM-разбор — фоном: заявка не ждёт медленную генерацию
    if task:
        asyncio.create_task(send_analysis(bot, lead_id, task))
    await create_crm_lead(
        name, task, phone, email, source, order, user.username or "", user.id
    )


async def send_analysis(bot: Bot, lead_id: int, task: str) -> None:
    analysis = await analyze_task(task)
    if not analysis:
        return
    try:
        await bot.send_message(
            ADMIN_CHAT_ID,
            f"🤖 <b>Разбор заявки #{lead_id} (локальная LLM):</b>\n{html.escape(analysis)}",
            parse_mode="HTML",
        )
    except Exception:
        log.exception("Не удалось доставить разбор заявки #%s", lead_id)


# ── кнопки владельца под заявкой ─────────────────────────────────────────────

def admin_lead_kb(lead_id: int, client_id: int) -> InlineKeyboardMarkup:
    return ikb(
        [btn("✍️ Ответить", f"re:{client_id}"), btn("🔧 В работу", f"st:{lead_id}:work")],
        [btn("✅ Закрыта", f"st:{lead_id}:done")],
    )


@router.callback_query(F.data.startswith("st:"))
async def cb_set_status(callback: CallbackQuery, bot: Bot) -> None:
    if callback.message.chat.id != ADMIN_CHAT_ID:
        await callback.answer()
        return
    try:
        _, lead_id_s, status = callback.data.split(":")
        lead_id = int(lead_id_s)
    except ValueError:
        await callback.answer()
        return
    row = db_set_status(lead_id, status)
    if not row:
        await callback.answer("Заявка не найдена", show_alert=True)
        return
    label = STATUS_LABELS.get(status, status)
    await callback.answer(f"Статус: {label}")
    try:
        await callback.message.edit_text(
            callback.message.html_text + f"\n\n<b>Статус: {label}</b>",
            parse_mode="HTML", disable_web_page_preview=True,
            reply_markup=admin_lead_kb(lead_id, row["user_id"]),
        )
    except Exception:
        pass
    # уведомляем клиента о движении по заявке
    notice = {
        "work": f"🔧 Ваша заявка #{lead_id} взята в работу — инженер уже занимается ей.",
        "done": f"✅ Заявка #{lead_id} закрыта. Спасибо, что обратились! "
                "Если что-то ещё понадобится — просто напишите /start 🙂",
    }.get(status)
    if notice:
        try:
            await bot.send_message(row["user_id"], notice)
        except Exception as e:
            log.warning("Не удалось уведомить клиента %s: %s", row["user_id"], e)


@router.callback_query(F.data.startswith("re:"))
async def cb_admin_reply(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message.chat.id != ADMIN_CHAT_ID:
        await callback.answer()
        return
    try:
        target_id = int(callback.data.split(":", 1)[1])
    except ValueError:
        await callback.answer()
        return
    await state.set_state(AdminReply.wait)
    await state.update_data(reply_to=target_id)
    await callback.answer()
    await callback.message.answer(
        f"✍️ Пишите ответ — отправлю клиенту (id {target_id}). /cancel — передумать."
    )


@router.message(AdminReply.wait, F.text)
async def admin_reply_send(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    target_id = data.get("reply_to")
    await state.clear()
    if not target_id:
        return
    try:
        await bot.send_message(
            target_id,
            f"👨‍🔧 <b>Сообщение от инженера opsmith:</b>\n\n{html.escape(message.text)}",
            parse_mode="HTML",
            reply_markup=ikb([btn("↩️ Ответить", "chat")]),
        )
        await message.answer("Отправлено ✅")
    except Exception as e:
        await message.answer(f"Не удалось отправить: {e}")


# ── чат «клиент ↔ инженер» ───────────────────────────────────────────────────

CHAT_INTRO = (
    "💬 Пишите ваш вопрос — я передам его инженеру, он ответит здесь же.\n"
    "Выйти из чата — /menu."
)


@router.message(Command("ask"))
async def cmd_ask(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(ChatMode.active)
    await message.answer(CHAT_INTRO, reply_markup=kb([KeyboardButton(text=CANCEL)]))


@router.callback_query(F.data == "chat")
async def cb_chat(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    await state.set_state(ChatMode.active)
    await callback.message.answer(
        CHAT_INTRO, reply_markup=kb([KeyboardButton(text=CANCEL)])
    )


@router.message(ChatMode.active, F.text)
async def chat_relay(message: Message, state: FSMContext, bot: Bot) -> None:
    user = message.from_user
    tg_line = f"@{user.username}" if user.username else f"id {user.id}"
    try:
        await bot.send_message(
            ADMIN_CHAT_ID,
            f"💬 <b>Вопрос от клиента</b> — {html.escape(user.full_name)} "
            f"({tg_line}, id {user.id}):\n\n{html.escape(message.text)}",
            parse_mode="HTML",
            reply_markup=ikb([btn("✍️ Ответить", f"re:{user.id}")]),
        )
    except Exception:
        log.exception("Не удалось переслать вопрос админу")
        await message.answer("Что-то пошло не так — попробуйте ещё раз чуть позже 🙏")
        return
    await message.answer("Передал инженеру ✅ Он ответит здесь же.")
    # пока инженер отвечает — черновик от локальной LLM (если настроена)
    if OLLAMA_URL:
        try:
            await bot.send_chat_action(message.chat.id, "typing")
        except Exception:
            pass
        draft = await draft_answer(message.text)
        if draft:
            await message.answer(
                f"🤖 <i>А пока — предварительный ответ ИИ (инженер ответит лично):</i>\n\n"
                f"{html.escape(draft)}",
                parse_mode="HTML",
            )


# ── любой текст вне сценариев ────────────────────────────────────────────────

@router.message(StateFilter(None), F.text)
async def fallback(message: Message) -> None:
    await show_menu(message)


@router.callback_query()
async def cb_stale(callback: CallbackQuery) -> None:
    # кнопка из старого сообщения, состояние уже другое — не оставляем спиннер
    await callback.answer("Эта кнопка уже неактуальна — /start 🙂")


async def main() -> None:
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await bot.set_my_commands([
        BotCommand(command="start", description="Начать / оставить заявку"),
        BotCommand(command="services", description="Услуги и цены"),
        BotCommand(command="faq", description="Частые вопросы"),
        BotCommand(command="ask", description="Задать вопрос инженеру"),
        BotCommand(command="status", description="Мои заявки"),
        BotCommand(command="cancel", description="Отменить текущее действие"),
        BotCommand(command="help", description="Справка"),
    ])
    log.info("Бот запущен (БД заявок: %s)", LEADS_DB)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
