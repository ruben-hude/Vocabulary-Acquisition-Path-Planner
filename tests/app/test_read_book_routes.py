import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes import pathhandler, profilehandler
from app.services import real_data
from vocabulary_acquisition_path_planner.models.media import Media


def _client_with_books(tmp_path, monkeypatch):
    project_root = tmp_path
    books_path = project_root / "data" / "raw" / "gutenberg_books"
    books_path.mkdir(parents=True)
    history_path = project_root / "data" / "processed" / "reading_history.json"
    metadata_path = project_root / "data" / "books_metadata.json"
    metadata_path.write_text(
        json.dumps({
            "11": {"title": "Source Book", "author": "Author One"},
            "98": {"title": "Target Book", "author": "Author Two"},
        }),
        encoding="utf-8",
    )

    for book_id in ("11", "98"):
        (books_path / f"book_{book_id}.txt").write_text(
            "play " * (10 if book_id == "11" else 1),
            encoding="utf-8",
        )

    monkeypatch.setattr(real_data, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(real_data, "BOOKS_PATH", books_path)
    monkeypatch.setattr(real_data, "HISTORY_PATH", history_path)
    monkeypatch.setattr(pathhandler, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(pathhandler, "BOOKS_PATH", books_path)
    monkeypatch.setattr(pathhandler, "READING_HISTORY_PATH", history_path)
    monkeypatch.setattr(pathhandler, "BOOKS_METADATA_PATH", metadata_path)

    media_by_name = {
        "book_11.txt": Media({"play": 10}),
        "book_98.txt": Media({"play": 1}),
    }
    monkeypatch.setattr(
        pathhandler.Media,
        "from_text_file",
        classmethod(lambda cls, path: media_by_name[Path(path).name]),
    )

    app = FastAPI()
    app.include_router(pathhandler.router)
    app.include_router(profilehandler.router)
    return TestClient(app)


def test_read_state_changes_initial_vocabulary_for_path_calculation(
    tmp_path, monkeypatch
):
    with _client_with_books(tmp_path, monkeypatch) as client:
        catalog = client.get("/api/books").json()["books"]
        assert next(book for book in catalog if book["id"] == "98") == {
            "id": "98",
            "name": "book_98",
            "title": "Target Book",
            "author": "Author Two",
            "path": "data\\raw\\gutenberg_books\\book_98.txt",
        }

        before_read = client.get(
            "/api/path/98?comprehension_threshold=0.8"
        )
        assert before_read.status_code == 200
        assert before_read.json() == []

        marked = client.put("/api/read-books/11")
        assert marked.status_code == 200
        assert marked.json() == {"id": "11", "is_read": True}
        assert [book["id"] for book in client.get("/api/read-books").json()] == [
            "book_11.txt"
        ]

        after_read = client.get(
            "/api/path/98?comprehension_threshold=0.8"
        )
        assert after_read.status_code == 200
        assert [step["id"] for step in after_read.json()] == ["98"]

        unmarked = client.delete("/api/read-books/11")
        assert unmarked.status_code == 200
        assert unmarked.json() == {"id": "11", "is_read": False}
        assert client.get(
            "/api/path/98?comprehension_threshold=0.8"
        ).json() == []


def test_read_books_resolves_legacy_filename_ids(tmp_path, monkeypatch):
    with _client_with_books(tmp_path, monkeypatch) as client:
        history_path = tmp_path / "data" / "processed" / "reading_history.json"
        history_path.parent.mkdir(parents=True, exist_ok=True)
        history_path.write_text(
            json.dumps({
                "books": {
                    "book_11.txt": {
                        "source_path": str(tmp_path / "missing" / "book_11.txt"),
                        "read_at": ["2026-10-07"],
                        "is_read": True,
                    }
                }
            }),
            encoding="utf-8",
        )

        response = client.get("/api/read-books")

    assert response.status_code == 200
    assert [book["id"] for book in response.json()] == ["book_11.txt"]


def test_read_target_skips_loading_library_media(tmp_path, monkeypatch):
    with _client_with_books(tmp_path, monkeypatch) as client:
        assert client.put("/api/read-books/98").status_code == 200

        def unexpected_media_load(cls, path):
            raise AssertionError("A read target should return before loading media")

        monkeypatch.setattr(
            pathhandler.Media,
            "from_text_file",
            classmethod(unexpected_media_load),
        )

        response = client.get("/api/path/98?comprehension_threshold=0.8")

    assert response.status_code == 200
    assert response.json() == []


def test_read_state_routes_reject_unknown_books(tmp_path, monkeypatch):
    with _client_with_books(tmp_path, monkeypatch) as client:
        response = client.put("/api/read-books/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found"
