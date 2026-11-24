import json

import pytest

from app.routes import pathhandler
from vocabulary_acquisition_path_planner.models.media import Media


@pytest.fixture
def book_files(tmp_path, monkeypatch):
    for book_id in (1, 2, 3):
        (tmp_path / f"book_{book_id}.txt").touch()
    monkeypatch.setattr(pathhandler, "BOOKS_PATH", tmp_path)
    return tmp_path


def test_books_include_metadata_titles(book_files, monkeypatch):
    metadata_path = book_files.parent / "books_metadata.json"
    metadata_path.write_text(
        json.dumps({
            "1": {"title": "First Book"},
            "2": {"title": "Second Book"},
            "3": {"title": "Third Book"},
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(pathhandler, "BOOKS_METADATA_PATH", metadata_path)
    monkeypatch.setattr(pathhandler, "PROJECT_ROOT", book_files)
    pathhandler.load_books_metadata.cache_clear()

    try:
        result = pathhandler.get_books()
    finally:
        pathhandler.load_books_metadata.cache_clear()

    assert [book["title"] for book in result["books"]] == [
        "First Book",
        "Second Book",
        "Third Book",
    ]


def test_get_book_includes_metadata_and_content(book_files, monkeypatch):
    (book_files / "book_1.txt").write_text("Book text", encoding="utf-8")
    metadata_path = book_files.parent / "books_metadata.json"
    metadata_path.write_text(
        json.dumps({
            "1": {
                "title": "First Book",
                "author": "A. Writer",
                "first_publish_year": 1890,
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(pathhandler, "BOOKS_METADATA_PATH", metadata_path)
    pathhandler.load_books_metadata.cache_clear()

    try:
        result = pathhandler.get_book(1)
    finally:
        pathhandler.load_books_metadata.cache_clear()

    assert result == {
        "id": 1,
        "name": "First Book",
        "date": 1890,
        "author": "A. Writer",
        "content": "Book text",
    }


def test_similarities_uses_the_precomputed_matrix(book_files, monkeypatch):
    matrix_path = book_files.parent / "similarity_books.json"
    matrix_path.write_text(
        json.dumps({
            "1": {"2": 0.25, "3": 0.5},
            "2": {"1": 0.75, "3": 0.6},
            "3": {"1": 0.4, "2": 0.3},
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(pathhandler, "SIMILARITIES_PATH", matrix_path)
    pathhandler.load_similarities.cache_clear()

    try:
        result = pathhandler.get_similarities()
    finally:
        pathhandler.load_similarities.cache_clear()

    assert result["links"] == [
        {"source": 1, "target": 2, "similar_percent": 0.25},
        {"source": 1, "target": 3, "similar_percent": 0.5},
        {"source": 2, "target": 3, "similar_percent": 0.6},
    ]


def test_user_similarity_combines_vocabulary_from_all_read_books(
    book_files, monkeypatch
):
    media_by_id = {
        1: Media({"shared": 6}),
        2: Media({"shared": 5}),
        3: Media({"shared": 2, "unseen": 2}),
    }
    monkeypatch.setattr(
        pathhandler.Media,
        "from_text_file",
        lambda book_path: media_by_id[
            int(book_path.stem.removeprefix("book_"))
        ],
    )

    result = pathhandler.get_user_similarities([1, 2])
    similarities_by_target = {
        link["target"]: link["similar_percent"]
        for link in result["links"]
    }

    assert similarities_by_target[3] == 0.5


def test_user_similarity_deduplicates_read_book_ids(book_files, monkeypatch):
    media_by_id = {
        1: Media({"shared": 6}),
        2: Media({"shared": 5}),
        3: Media({"shared": 2, "unseen": 2}),
    }
    monkeypatch.setattr(
        pathhandler.Media,
        "from_text_file",
        lambda book_path: media_by_id[
            int(book_path.stem.removeprefix("book_"))
        ],
    )

    result = pathhandler.get_user_similarities([1, 1, 2])
    similarities_by_target = {
        link["target"]: link["similar_percent"]
        for link in result["links"]
    }

    assert similarities_by_target[3] == 0.5
