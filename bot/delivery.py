"""Разбиение сообщений и сохраняемые задания доставки Telegram."""

import html
from html.parser import HTMLParser

from aiogram.client.session.middlewares.base import BaseRequestMiddleware
from aiogram.methods import SendMessage
from aiogram.types import BufferedInputFile, InlineKeyboardMarkup, Message


def text_length(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


class HTMLChunks(HTMLParser):
    """Разрезает текст, закрывая и открывая теги на границах частей."""

    def __init__(self, limit: int):
        super().__init__(convert_charrefs=True)
        self.limit = limit
        self.stack = []
        self.current = []
        self.size = 0
        self.chunks = []

    def flush(self):
        if not self.size:
            return
        self.chunks.append("".join(self.current) + "".join(
            f"</{tag}>" for tag, _ in reversed(self.stack)
        ))
        self.current = [raw for _, raw in self.stack]
        self.size = 0

    def handle_starttag(self, tag, attrs):
        raw = self.get_starttag_text()
        self.current.append(raw)
        self.stack.append((tag, raw))

    def handle_endtag(self, tag):
        self.current.append(f"</{tag}>")
        if self.stack and self.stack[-1][0] == tag:
            self.stack.pop()

    def handle_data(self, data):
        for char in data:
            size = 2 if ord(char) > 0xFFFF else 1
            if self.size + size > self.limit:
                self.flush()
            self.current.append(html.escape(char, quote=False))
            self.size += size


def split_text(text: str, html_mode: bool = False, limit: int = 3500) -> list[str]:
    if limit < 2:
        raise ValueError("Message limit must be at least 2")
    if html_mode:
        parser = HTMLChunks(limit)
        parser.feed(text)
        parser.close()
        parser.flush()
        return parser.chunks or [text]
    chunks, current, size = [], [], 0
    for char in text:
        width = 2 if ord(char) > 0xFFFF else 1
        if size + width > limit:
            chunks.append("".join(current))
            current, size = [], 0
        current.append(char)
        size += width
    if current:
        chunks.append("".join(current))
    return chunks or [text]


class SplitMessages(BaseRequestMiddleware):
    async def __call__(self, make_request, bot, method):
        if not isinstance(method, SendMessage) or text_length(method.text) <= 3500:
            return await make_request(bot, method)
        # В проекте используются HTML или обычный текст, не Markdown/entities.
        if method.entities:
            return await make_request(bot, method)
        parts = split_text(method.text, method.parse_mode == "HTML")
        result = None
        for i, text in enumerate(parts):
            part = method.model_copy(update={
                "text": text,
                "reply_markup": method.reply_markup if i == len(parts) - 1 else None,
            })
            result = await make_request(bot, part)
        return result


def message_jobs(chat_id: int, text: str, markup=None, html_mode=True) -> list[dict]:
    parts = split_text(text, html_mode)
    jobs = []
    for i, part in enumerate(parts):
        job = {"kind": "message", "chat_id": chat_id, "text": part,
               "parse_mode": "HTML" if html_mode else None}
        if markup is not None and i == len(parts) - 1:
            job["reply_markup"] = markup.model_dump(mode="json", exclude_none=True)
        jobs.append(job)
    return jobs


MEDIA_KINDS = ("document", "voice", "video", "audio", "animation", "video_note", "sticker")


def attachment_from(message: Message) -> dict | None:
    if message.photo:
        return {"kind": "photo", "file_id": message.photo[-1].file_id,
                "caption": message.caption or ""}
    for kind in MEDIA_KINDS:
        media = getattr(message, kind, None)
        if media:
            return {"kind": kind, "file_id": media.file_id,
                    "caption": message.caption or "",
                    "name": getattr(media, "file_name", None) or ""}
    return None


def attachment_jobs(chat_id: int, attachments: list[dict], markup=None) -> list[dict]:
    jobs = []
    for attachment in attachments:
        # Подпись отправляется отдельным текстом: у вложений лимит всего 1024.
        jobs.append({**attachment, "chat_id": chat_id, "caption": ""})
        if attachment.get("caption"):
            jobs.extend(message_jobs(chat_id, attachment["caption"], html_mode=False))
    if jobs and markup is not None:
        jobs[-1]["reply_markup"] = markup.model_dump(mode="json", exclude_none=True)
    return jobs


def conversation_text(text: str, attachments: list[dict]) -> str:
    lines = [text] if text else []
    for item in attachments:
        lines.append(f"[Вложение: {item['kind']} {item.get('name', '')}]".rstrip())
        if item.get("caption"):
            lines.append(item["caption"])
    return "\n".join(lines)


async def deliver(bot, payload: dict):
    data = dict(payload)
    kind = data.pop("kind")
    data.pop("name", None)
    if data.get("reply_markup"):
        data["reply_markup"] = InlineKeyboardMarkup.model_validate(data["reply_markup"])
    if kind == "message":
        return await bot.send_message(**data)
    if kind == "text_file":
        content = data.pop("content")
        filename = data.pop("filename")
        return await bot.send_document(
            document=BufferedInputFile(content.encode("utf-8"), filename=filename), **data
        )
    if kind not in ("photo", *MEDIA_KINDS):
        raise ValueError(f"Unknown delivery kind: {kind}")
    data[kind] = data.pop("file_id")
    if kind in ("sticker", "video_note"):
        data.pop("caption", None)
    return await getattr(bot, f"send_{kind}")(**data)
