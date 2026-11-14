"""SQLite: заявки, постоянные состояния, очередь и резервные копии."""

import json
import sqlite3
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage

from delivery import conversation_text


class Store:
    def __init__(self, path: str, reminder_seconds=7200):
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.reminder_seconds = reminder_seconds
        self.db = sqlite3.connect(self.path, timeout=10)
        self.db.row_factory = sqlite3.Row
        self.db.create_function("casefold", 1, lambda value: (value or "").casefold())
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL,
                user_id INTEGER NOT NULL, username TEXT, name TEXT, task TEXT,
                phone TEXT, email TEXT, source TEXT, order_text TEXT,
                status TEXT NOT NULL DEFAULT 'new'
            );
            CREATE TABLE IF NOT EXISTS sessions (
                key TEXT PRIMARY KEY, state TEXT, data TEXT NOT NULL DEFAULT '{}'
            );
            CREATE TABLE IF NOT EXISTS outbox (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_key TEXT NOT NULL, part INTEGER NOT NULL,
                chat_id INTEGER NOT NULL, payload TEXT NOT NULL,
                effect TEXT, status TEXT NOT NULL DEFAULT 'pending',
                attempts INTEGER NOT NULL DEFAULT 0, next_attempt REAL NOT NULL,
                created REAL NOT NULL, sent REAL, last_error TEXT,
                UNIQUE(batch_key, part)
            );
            CREATE INDEX IF NOT EXISTS outbox_due ON outbox(status, next_attempt);
            CREATE INDEX IF NOT EXISTS outbox_chat ON outbox(chat_id, status, id);
            CREATE TABLE IF NOT EXISTS followups (
                user_id INTEGER PRIMARY KEY, lead_id INTEGER,
                since REAL NOT NULL, last_message REAL NOT NULL, next_reminder REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL REFERENCES leads(id),
                ts TEXT NOT NULL, text TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS conversation (
                id INTEGER PRIMARY KEY AUTOINCREMENT, event_key TEXT NOT NULL UNIQUE,
                user_id INTEGER NOT NULL, ts TEXT NOT NULL,
                direction TEXT NOT NULL, text TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS conversation_user ON conversation(user_id, id);
        """)
        columns = {r["name"] for r in self.db.execute("PRAGMA table_info(leads)")}
        upgrading = "submission_key" not in columns
        for name, definition in (
            ("submission_key", "TEXT"),
            ("attachments", "TEXT NOT NULL DEFAULT '[]'"),
        ):
            if name not in columns:
                self.db.execute(f"ALTER TABLE leads ADD COLUMN {name} {definition}")
        self.db.execute("CREATE UNIQUE INDEX IF NOT EXISTS lead_submission ON leads(submission_key)")
        self.db.execute("CREATE INDEX IF NOT EXISTS lead_user ON leads(user_id, id)")
        if upgrading:
            now = time.time()
            self.db.execute(
                "INSERT OR IGNORE INTO followups(user_id,lead_id,since,last_message,next_reminder) "
                "SELECT user_id,MAX(id),?,?,? FROM leads WHERE status='new' GROUP BY user_id",
                (now, now, now + self.reminder_seconds),
            )
        self.db.commit()

    def close(self):
        self.db.close()

    def enqueue(self, jobs: list[dict], key: str, effect=None):
        """Вызывать внутри with store.db для атомарности с заявкой/статусом."""
        now = time.time()
        inserted = 0
        for i, payload in enumerate(jobs):
            cur = self.db.execute(
                "INSERT OR IGNORE INTO outbox "
                "(batch_key,part,chat_id,payload,effect,next_attempt,created) VALUES(?,?,?,?,?,?,?)",
                (key, i, payload["chat_id"], json.dumps(payload, ensure_ascii=False),
                 json.dumps(effect) if effect and i == len(jobs) - 1 else None, now, now),
            )
            inserted += cur.rowcount
        return inserted

    def wait_for_reply(self, user_id: int, lead_id=None, now=None):
        now = time.time() if now is None else now
        self.db.execute(
            "INSERT INTO followups(user_id,lead_id,since,last_message,next_reminder) VALUES(?,?,?,?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET "
            "lead_id=COALESCE(excluded.lead_id,followups.lead_id),last_message=excluded.last_message",
            (user_id, lead_id, now, now, now + self.reminder_seconds),
        )

    def create_lead(self, user_id, username, data, submission_key, jobs_factory):
        """Заявка и все части уведомления сохраняются одной транзакцией."""
        with self.db:
            existing = self.db.execute(
                "SELECT id FROM leads WHERE submission_key=?", (submission_key,)
            ).fetchone()
            if existing:
                return existing["id"], False
            cur = self.db.execute(
                "INSERT INTO leads(ts,user_id,username,name,task,phone,email,source,order_text,"
                "submission_key,attachments) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(timespec="seconds"), user_id, username,
                 data.get("name", ""), data.get("task", ""), data.get("phone", ""),
                 data.get("email", ""), data.get("source", ""), data.get("order", ""),
                 submission_key, json.dumps(data.get("attachments", []), ensure_ascii=False)),
            )
            lead_id = cur.lastrowid
            self.enqueue(jobs_factory(lead_id), f"lead:{lead_id}")
            self.wait_for_reply(user_id, lead_id)
            self.record_message(f"lead:{lead_id}", user_id, "Клиент",
                                f"Заявка #{lead_id}\n" + conversation_text(
                                    data.get("task", ""), data.get("attachments", [])))
        return lead_id, True

    def record_message(self, key, user_id, direction, text):
        self.db.execute(
            "INSERT OR IGNORE INTO conversation(event_key,user_id,ts,direction,text) VALUES(?,?,?,?,?)",
            (key, user_id, datetime.now(timezone.utc).isoformat(timespec="seconds"), direction, text),
        )

    def get_lead(self, lead_id):
        return self.db.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()

    def latest_lead(self, user_id):
        return self.db.execute(
            "SELECT * FROM leads WHERE user_id=? AND status!='done' ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()

    def list_leads(self, status="all", query="", page=0, per_page=8):
        clauses, params = [], []
        if status != "all":
            clauses.append("status=?")
            params.append(status)
        if query:
            escaped = query.casefold().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            clauses.append(
                "(CAST(id AS TEXT)=? OR CAST(user_id AS TEXT)=? OR "
                "casefold(COALESCE(name,'')||' '||COALESCE(username,'')||' '||COALESCE(task,'')"
                "||' '||COALESCE(phone,'')||' '||COALESCE(email,'')) LIKE ? ESCAPE '\\')"
            )
            params.extend((query.lstrip("#"), query, f"%{escaped}%"))
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        total = self.db.execute("SELECT COUNT(*) FROM leads" + where, params).fetchone()[0]
        rows = self.db.execute(
            "SELECT * FROM leads" + where + " ORDER BY id DESC LIMIT ? OFFSET ?",
            [*params, per_page, max(0, page) * per_page],
        ).fetchall()
        return rows, total

    def queue_counts(self):
        return {r["status"]: r["n"] for r in self.db.execute(
            "SELECT status,COUNT(*) n FROM outbox WHERE status!='sent' GROUP BY status"
        )}

    def due(self, now=None, limit=20):
        now = time.time() if now is None else now
        # Порядок частей внутри каждого чата; сбой одного чата не блокирует другие.
        return self.db.execute(
            "SELECT o.* FROM outbox o WHERE status='pending' AND next_attempt<=? "
            "AND NOT EXISTS(SELECT 1 FROM outbox p WHERE p.chat_id=o.chat_id "
            "AND p.status='pending' AND p.id<o.id) ORDER BY id LIMIT ?", (now, limit)
        ).fetchall()

    def delivered(self, row):
        with self.db:
            self.db.execute("UPDATE outbox SET status='sent',sent=?,last_error=NULL WHERE id=?",
                            (time.time(), row["id"]))
            unfinished = self.db.execute(
                "SELECT 1 FROM outbox WHERE batch_key=? AND status!='sent' LIMIT 1",
                (row["batch_key"],),
            ).fetchone()
            effect_row = self.db.execute(
                "SELECT effect FROM outbox WHERE batch_key=? AND effect IS NOT NULL",
                (row["batch_key"],),
            ).fetchone()
            if not unfinished and effect_row:
                effect = json.loads(effect_row["effect"])
                if "reply_to" in effect:
                    args = (effect["reply_to"], effect["cutoff"])
                    self.db.execute(
                        "DELETE FROM followups WHERE user_id=? AND last_message<=?", args)
                    self.db.execute(
                        "UPDATE followups SET since=last_message,next_reminder=last_message+? "
                        "WHERE user_id=? AND last_message>?", (self.reminder_seconds, *args))

    def delivery_failed(self, row, error: str, delay: float, permanent=False):
        with self.db:
            self.db.execute(
                "UPDATE outbox SET status=?,attempts=attempts+1,next_attempt=?,last_error=? WHERE id=?",
                ("failed" if permanent else "pending", time.time() + delay, error[:500], row["id"]),
            )

    def backup(self, directory: str, keep=14) -> Path:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / f"leads-{datetime.now():%Y-%m-%d}.db"
        temporary = target.with_suffix(".tmp")
        # Отдельные подключения: безопасно выполнять в рабочем потоке при WAL.
        source = sqlite3.connect(self.path, timeout=10)
        destination = sqlite3.connect(temporary)
        try:
            source.backup(destination, pages=128)
            if destination.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("Backup integrity check failed")
        finally:
            destination.close()
            source.close()
        temporary.replace(target)
        for old in sorted(directory.glob("leads-????-??-??.db"), reverse=True)[max(1, keep):]:
            old.unlink()
        return target


class SQLiteStorage(BaseStorage):
    def __init__(self, store: Store):
        self.store = store

    @staticmethod
    def key(key):
        return json.dumps(asdict(key), sort_keys=True, separators=(",", ":"))

    async def set_state(self, key, state=None):
        value = state.state if isinstance(state, State) else state
        with self.store.db:
            self.store.db.execute(
                "INSERT INTO sessions(key,state) VALUES(?,?) ON CONFLICT(key) "
                "DO UPDATE SET state=excluded.state", (self.key(key), value))

    async def get_state(self, key):
        row = self.store.db.execute("SELECT state FROM sessions WHERE key=?", (self.key(key),)).fetchone()
        return row["state"] if row else None

    async def set_data(self, key, data):
        with self.store.db:
            self.store.db.execute(
                "INSERT INTO sessions(key,data) VALUES(?,?) ON CONFLICT(key) "
                "DO UPDATE SET data=excluded.data",
                (self.key(key), json.dumps(dict(data), ensure_ascii=False)),
            )
            self.store.db.execute("DELETE FROM sessions WHERE key=? AND state IS NULL AND data='{}'",
                                  (self.key(key),))

    async def get_data(self, key):
        row = self.store.db.execute("SELECT data FROM sessions WHERE key=?", (self.key(key),)).fetchone()
        return json.loads(row["data"]) if row else {}

    async def close(self):
        # Соединение общее; владелец закроет после завершения фоновых задач.
        pass
