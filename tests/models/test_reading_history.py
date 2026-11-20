"""Tests for persistent reading history."""

import json
from datetime import date

from vocabulary_acquisition_path_planner.models.reading_history import (
    ReadingHistory,
)


def test_reading_history_persists_state_and_all_reading_dates(tmp_path):
    history_path = tmp_path / "reading_history.json"
    book_path = tmp_path / "book_84.txt"

    history = ReadingHistory(history_path)
    assert history.is_read(book_path.name) is False

    history.mark_read(book_path.name, book_path)
    history.mark_unread(book_path.name, book_path)

    reloaded = ReadingHistory(history_path)
    assert reloaded.is_read(book_path.name) is False

    data = json.loads(history_path.read_text(encoding="utf-8"))
    book = data["books"][book_path.name]
    assert book["source_path"] == str(book_path)
    assert len(book["read_at"]) == 1
    assert book["read_at"][0].endswith("+00:00")


def test_reading_history_records_repeated_reads(tmp_path):
    history = ReadingHistory(tmp_path / "reading_history.json")
    book_path = tmp_path / "book_84.txt"

    history.mark_read(book_path.name, book_path)
    history.mark_unread(book_path.name, book_path)
    history.mark_read(book_path.name, book_path)

    data = json.loads(history.path.read_text(encoding="utf-8"))
    assert len(data["books"][book_path.name]["read_at"]) == 2


def test_reading_history_accepts_an_explicit_reading_date(tmp_path):
    history = ReadingHistory(tmp_path / "reading_history.json")
    book_path = tmp_path / "book_84.txt"

    history.mark_read(book_path.name, book_path, date(2026, 9, 21))

    assert history.last_read_at(book_path.name) == "2026-09-21"