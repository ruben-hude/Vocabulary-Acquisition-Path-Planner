"""Persistent reading dates for learning media."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path


class ReadingHistory:
    """Store the current read state and all reading dates for each book."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self._books: dict[str, dict[str, object]] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        with self.path.open(encoding="utf-8") as file:
            data = json.load(file)
        books = data.get("books", {})
        if isinstance(books, dict):
            self._books = books

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as file:
            json.dump({"books": self._books}, file, indent=2)
            file.write("\n")

    def is_read(self, book_id: str) -> bool:
        """Return whether the book is currently marked as read."""
        book = self._books.get(book_id, {})
        return bool(book.get("is_read", False))

    def last_read_at(self, book_id: str) -> str | None:
        """Return the most recent reading date, if one is recorded."""
        book = self._books.get(book_id, {})
        read_at = book.get("read_at", [])
        if not isinstance(read_at, list) or not read_at:
            return None
        return str(read_at[-1])

    def mark_read(
        self,
        book_id: str,
        source_path: Path,
        read_at: date | datetime | str | None = None,
    ) -> None:
        """Record a reading event and mark the book as currently read."""
        book = self._books.setdefault(
            book_id,
            {"source_path": str(source_path), "read_at": []},
        )
        book["source_path"] = str(source_path)
        reading_dates = book.setdefault("read_at", [])
        if isinstance(reading_dates, list):
            if read_at is None:
                reading_date = datetime.now(timezone.utc).isoformat(
                    timespec="seconds"
                )
            elif isinstance(read_at, datetime):
                reading_date = read_at.isoformat(timespec="seconds")
            elif isinstance(read_at, date):
                reading_date = read_at.isoformat()
            else:
                reading_date = read_at
            reading_dates.append(reading_date)
        book["is_read"] = True
        self._save()

    def mark_unread(self, book_id: str, source_path: Path) -> None:
        """Clear the current read state without deleting reading history."""
        book = self._books.setdefault(
            book_id,
            {"source_path": str(source_path), "read_at": []},
        )
        book["source_path"] = str(source_path)
        book["is_read"] = False
        self._save()