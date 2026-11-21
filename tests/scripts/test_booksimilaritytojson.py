import json

import pytest

from scripts.booksimilaritytoJSON import (
    BOOK_DIRECTORY,
    METADATA_PATH,
    build_book_similarity_json,
    check_book_ids,
    similarity_id,
)
from vocabulary_acquisition_path_planner.models.media import Media


def test_downloaded_text_ids_match_metadata_ids():
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    text_book_ids = {
        int(book_path.stem.removeprefix("book_"))
        for book_path in BOOK_DIRECTORY.glob("book_*.txt")
    }

    check_book_ids(metadata, {book_id: Media() for book_id in text_book_ids})


def test_similarity_is_target_occurrence_coverage_and_directional():
    books = {
        1: Media({"read": 1}),
        2: Media({"read": 2, "play": 3}),
    }

    assert similarity_id(1, 2, books) == pytest.approx(0.4)
    assert similarity_id(2, 1, books) == 1.0


def test_empty_target_has_zero_similarity():
    books = {1: Media({"read": 1}), 2: Media()}

    assert similarity_id(1, 2, books) == 0.0


def test_similarity_matrix_contains_both_directions_without_self_pairs():
    books = {
        1: Media({"read": 1}),
        2: Media({"read": 2, "play": 3}),
    }

    assert build_book_similarity_json({"1": {}, "2": {}}, books) == {
        "1": {"2": 0.4},
        "2": {"1": 1.0},
    }


def test_check_book_ids_rejects_text_without_metadata():
    with pytest.raises(ValueError, match="Fichiers texte sans ID"):
        check_book_ids({"1": {}}, {1: Media(), 2: Media()})
