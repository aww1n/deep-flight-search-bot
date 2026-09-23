import asyncio
import sqlite3
from pathlib import Path


class ConversationStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.execute("PRAGMA journal_mode=WAL")
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    chat_id INTEGER PRIMARY KEY,
                    previous_response_id TEXT,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    async def get(self, chat_id: int) -> str | None:
        async with self._lock:
            return await asyncio.to_thread(self._get_sync, chat_id)

    def _get_sync(self, chat_id: int) -> str | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT previous_response_id FROM conversations WHERE chat_id = ?", (chat_id,)
            ).fetchone()
        return row[0] if row else None

    async def set(self, chat_id: int, response_id: str) -> None:
        async with self._lock:
            await asyncio.to_thread(self._set_sync, chat_id, response_id)

    def _set_sync(self, chat_id: int, response_id: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO conversations (chat_id, previous_response_id)
                VALUES (?, ?)
                ON CONFLICT(chat_id) DO UPDATE SET
                    previous_response_id = excluded.previous_response_id,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (chat_id, response_id),
            )

    async def clear(self, chat_id: int) -> None:
        async with self._lock:
            await asyncio.to_thread(self._clear_sync, chat_id)

    def _clear_sync(self, chat_id: int) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM conversations WHERE chat_id = ?", (chat_id,))

