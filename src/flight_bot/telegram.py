import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from .text import split_message

logger = logging.getLogger(__name__)

MessageHandler = Callable[[int, str], Awaitable[str]]
ResetHandler = Callable[[int], Awaitable[None]]


class TelegramBot:
    def __init__(
        self,
        *,
        token: str,
        on_message: MessageHandler,
        on_reset: ResetHandler,
    ) -> None:
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.on_message = on_message
        self.on_reset = on_reset
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(70.0, connect=15.0))

    async def api(self, method: str, payload: dict[str, Any] | None = None) -> Any:
        response = await self.client.post(f"{self.base_url}/{method}", json=payload or {})
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise RuntimeError(data.get("description", "Telegram API error"))
        return data.get("result")

    async def send(self, chat_id: int, text: str) -> None:
        for chunk in split_message(text):
            await self.api(
                "sendMessage",
                {
                    "chat_id": chat_id,
                    "text": chunk,
                    "link_preview_options": {"is_disabled": True},
                },
            )

    async def set_commands(self) -> None:
        await self.api(
            "setMyCommands",
            {
                "commands": [
                    {"command": "start", "description": "Как пользоваться ботом"},
                    {"command": "new", "description": "Начать новый поиск"},
                    {"command": "help", "description": "Подсказка и пример запроса"},
                ]
            },
        )

    async def handle_update(self, update: dict[str, Any]) -> None:
        message = update.get("message")
        if not message or not isinstance(message.get("text"), str):
            return
        chat_id = int(message["chat"]["id"])
        text = message["text"].strip()

        if text in {"/start", "/help"}:
            await self.send(chat_id, welcome_text())
            return
        if text == "/new":
            await self.on_reset(chat_id)
            await self.send(chat_id, "Новый поиск начат. Пришлите маршрут и даты.")
            return

        await self.api("sendChatAction", {"chat_id": chat_id, "action": "typing"})
        try:
            answer = await self.on_message(chat_id, text)
        except Exception:
            logger.exception("Failed to process message for chat_id=%s", chat_id)
            await self.send(
                chat_id,
                "Поиск не завершился из-за технической ошибки. Попробуйте ещё раз чуть позже.",
            )
            return
        await self.send(chat_id, answer)

    async def run(self) -> None:
        await self.api("deleteWebhook", {"drop_pending_updates": False})
        await self.set_commands()
        offset: int | None = None
        logger.info("Telegram long polling started")
        try:
            while True:
                payload: dict[str, Any] = {
                    "timeout": 50,
                    "allowed_updates": ["message"],
                }
                if offset is not None:
                    payload["offset"] = offset
                try:
                    updates = await self.api("getUpdates", payload)
                    for update in updates:
                        offset = int(update["update_id"]) + 1
                        await self.handle_update(update)
                except httpx.HTTPError:
                    logger.exception("Telegram network error; retrying")
                    await asyncio.sleep(3)
        finally:
            await self.client.aclose()


def welcome_text() -> str:
    return (
        "✈️ Deep Flight Search ищет не только обычный билет, но и отдельные сегменты, "
        "альтернативные аэропорты и наземный транспорт.\n\n"
        "Пришлите одним сообщением:\n"
        "• откуда и куда;\n"
        "• даты туда и обратно;\n"
        "• допустимую гибкость дат;\n"
        "• число взрослых и детей;\n"
        "• гражданство;\n"
        "• нужен ли багаж;\n"
        "• допустимы ли отдельные билеты и ночёвки.\n\n"
        "Пример: Москва → Санья, 10–20 ноября 2026, ±2 дня, 2 взрослых, "
        "гражданство РФ, багаж 23 кг, self-transfer разрешён.\n\n"
        "Команда /new очищает текущий диалог. Цены динамические и требуют проверки "
        "на странице продавца."
    )

