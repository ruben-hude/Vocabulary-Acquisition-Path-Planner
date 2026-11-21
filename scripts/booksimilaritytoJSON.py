"""Precompute pairwise book similarities in ``data/raw/similarity_books.json``.

For ``id1 -> id2``, similarity is the share of id2's recognized word
occurrences whose word group also occurs in id1. Change
``_similarity_from_common_groups`` to use a different definition.
"""

import json
from pathlib import Path

from vocabulary_acquisition_path_planner.models.media import Media

PROJECT_ROOT = Path(__file__).resolve().parents[1]
METADATA_PATH = PROJECT_ROOT / "data" / "books_metadata.json"
BOOK_DIRECTORY = PROJECT_ROOT / "data" / "raw" / "gutenberg_books"
OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "similarity_books.json"


def load_books_by_id() -> dict[int, Media]:
    """Load downloaded text files as Media objects, keyed by book ID."""
    return {
        int(book_path.stem.removeprefix("book_")): Media.from_text_file(book_path)
        for book_path in sorted(BOOK_DIRECTORY.glob("book_*.txt"))
    }


def build_book_similarity_json(
    books: dict[str, object],
    books_by_id: dict[int, Media],
) -> dict[str, dict[str, float]]:
    """
    Build the JSON-ready matrix, including both similarity directions.

    Similarity keys are book IDs; each row maps another ID to the share of
    that target book's recognized word occurrences found in the source book.
    """
    book_ids = [int(book_id) for book_id in books]
    similarities = {str(book_id): {} for book_id in book_ids}
    occurrences = {
        book_id: books_by_id[book_id].word_group_occurrences
        for book_id in book_ids
    }
    group_sets = {
        book_id: set(book_occurrences)
        for book_id, book_occurrences in occurrences.items()
    }
    total_occurrences = {
        book_id: sum(book_occurrences.values())
        for book_id, book_occurrences in occurrences.items()
    }

    for index, book_id in enumerate(book_ids):
        for other_book_id in book_ids[index + 1 :]:
            common_groups = group_sets[book_id] & group_sets[other_book_id]
            for source_id, target_id in (
                (book_id, other_book_id),
                (other_book_id, book_id),
            ):
                similarities[str(source_id)][str(target_id)] = (
                    _similarity_from_common_groups(
                        common_groups,
                        occurrences[target_id],
                        total_occurrences[target_id],
                    )
                )

    return similarities


def _similarity_from_common_groups(
    common_groups: set[str],
    target_occurrences: dict[str, int],
    target_total: int,
) -> float:
    if not target_total:
        return 0.0
    common_occurrences = sum(
        target_occurrences[group_id] for group_id in common_groups
    )
    return common_occurrences / target_total


def similarity_id(
    book_id: int,
    other_book_id: int,
    books_by_id: dict[int, Media],
) -> float:
    """Return id2's occurrence coverage by id1's groups.

    Counts all target occurrences for groups present in the source. The
    denominator is the total number of recognized word-group occurrences in
    the target Media. The shared calculation is in
    ``_similarity_from_common_groups``.
    """
    source_groups = set(books_by_id[book_id].word_group_occurrences)
    target_occurrences = books_by_id[other_book_id].word_group_occurrences
    target_total = sum(target_occurrences.values())
    common_groups = source_groups & set(target_occurrences)
    return _similarity_from_common_groups(
        common_groups,
        target_occurrences,
        target_total,
    )


def check_book_ids(books: dict, books_by_id: dict[int, Media]) -> None:
    metadata_ids = {int(book_id) for book_id in books}
    file_ids = set(books_by_id)

    missing_files = sorted(metadata_ids - file_ids)
    missing_metadata = sorted(file_ids - metadata_ids)

    if missing_files or missing_metadata:
        raise ValueError(
            f"IDs dans les métadonnées sans fichier texte : {missing_files}\n"
            f"Fichiers texte sans ID dans les métadonnées : {missing_metadata}"
        )

    print(f"{len(metadata_ids)} IDs correspondent.")

if __name__ == "__main__":
    with open(METADATA_PATH, "r", encoding="utf-8") as metadata_file:
        books = json.load(metadata_file)
    Books = load_books_by_id()
    check_book_ids(books, Books)
    similarity_dict = build_book_similarity_json(books, Books)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as output_file:
        json.dump(similarity_dict, output_file, ensure_ascii=False, indent=2)
