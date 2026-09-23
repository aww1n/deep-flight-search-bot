from pathlib import Path

import pytest

from flight_bot.store import ConversationStore


@pytest.mark.asyncio
async def test_conversation_lifecycle(tmp_path: Path) -> None:
    store = ConversationStore(tmp_path / "bot.db")
    assert await store.get(42) is None
    await store.set(42, "resp_1")
    assert await store.get(42) == "resp_1"
    await store.set(42, "resp_2")
    assert await store.get(42) == "resp_2"
    await store.clear(42)
    assert await store.get(42) is None

