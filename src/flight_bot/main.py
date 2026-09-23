import asyncio
import logging
from importlib.resources import files

from .config import load_settings
from .service import FlightSearchService
from .store import ConversationStore
from .telegram import TelegramBot


async def main() -> None:
    settings = load_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    store = ConversationStore(settings.database_path)
    search = FlightSearchService(
        api_key=settings.openai_api_key.get_secret_value(),
        model=settings.openai_model,
        reasoning_effort=settings.openai_reasoning_effort,
        instructions=files("flight_bot").joinpath("system_ru.md").read_text(encoding="utf-8"),
    )

    async def on_message(chat_id: int, text: str) -> str:
        previous_response_id = await store.get(chat_id)
        answer, response_id = await search.respond(text, previous_response_id)
        await store.set(chat_id, response_id)
        return answer

    bot = TelegramBot(
        token=settings.telegram_bot_token.get_secret_value(),
        on_message=on_message,
        on_reset=store.clear,
    )
    await bot.run()


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
