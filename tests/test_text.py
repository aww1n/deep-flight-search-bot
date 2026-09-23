import pytest

from flight_bot.text import split_message


def test_short_message_is_unchanged() -> None:
    assert split_message("hello", limit=10) == ["hello"]


def test_long_message_is_split_without_data_loss() -> None:
    text = "alpha beta gamma delta"
    chunks = split_message(text, limit=10)
    assert all(len(chunk) <= 10 for chunk in chunks)
    assert " ".join(chunks) == text


def test_hard_split_for_unbroken_text() -> None:
    chunks = split_message("abcdefghij", limit=4)
    assert chunks == ["abcd", "efgh", "ij"]


def test_rejects_invalid_limit() -> None:
    with pytest.raises(ValueError):
        split_message("hello", limit=0)

