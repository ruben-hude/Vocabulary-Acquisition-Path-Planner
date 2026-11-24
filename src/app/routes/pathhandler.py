import json
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from vocabulary_acquisition_path_planner.models.learner_vocabulary import (
    LearnerVocabulary,
)
from vocabulary_acquisition_path_planner.models.media import Media
from vocabulary_acquisition_path_planner.search.graph import Graph
from vocabulary_acquisition_path_planner.search.path_finder import PathFinder

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BOOKS_PATH = PROJECT_ROOT / "data" / "raw" / "gutenberg_books" # Path to the folder containing the books
BOOKS_METADATA_PATH = PROJECT_ROOT / "data" / "books_metadata.json"
SIMILARITIES_PATH = PROJECT_ROOT / "data" / "raw" / "similarity_books.json"
READING_HISTORY_PATH = PROJECT_ROOT / "data" / "processed" / "reading_history.json"

router = APIRouter(prefix="/api", tags=["path"])


@router.get("/")
def get_index():
    return RedirectResponse(url="/render.html")


@router.get("/books")
def get_books():
    """
    Return downloaded books with their metadata titles and local paths.
    """
    metadata = load_books_metadata()
    books = []
    for file in BOOKS_PATH.glob("book_*.txt"):
        book_id = file.stem.removeprefix("book_")
        book_metadata = metadata.get(book_id)
        if book_metadata is None or not isinstance(book_metadata.get("title"), str):
            raise HTTPException(
                status_code=503,
                detail=f"Book title metadata is unavailable for book {book_id}.",
            )
        books.append({
            "name": file.stem,
            "title": book_metadata["title"],
            "path": str(file.relative_to(PROJECT_ROOT)),
        })
    return {"books": books}


@lru_cache(maxsize=1)
def load_books_metadata() -> dict[str, dict[str, object]]:
    """Load book metadata once per server process."""
    try:
        return json.loads(BOOKS_METADATA_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=503,
            detail="Book metadata is unavailable.",
        ) from error


@lru_cache(maxsize=1)
def load_similarities() -> dict[str, dict[str, float]]:
    """Load the precomputed book similarity matrix once per server process."""
    try:
        return json.loads(SIMILARITIES_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=503,
            detail=(
                "Precomputed similarities are unavailable. "
                "Run scripts/booksimilaritytoJSON.py first."
            ),
        ) from error


@router.get("/book/{id}")
def get_book(id: int):
    """
    Return a specific book's metadata and content.
    """
    book_path = BOOKS_PATH / f"book_{id}.txt"
    if not book_path.exists():
        raise HTTPException(status_code=404, detail="Book not found")

    book_metadata = load_books_metadata().get(str(id))
    if (
        book_metadata is None
        or not isinstance(book_metadata.get("title"), str)
        or not isinstance(book_metadata.get("author"), str)
    ):
        raise HTTPException(
            status_code=503,
            detail=f"Book metadata is unavailable for book {id}.",
        )

    date = (
        book_metadata.get("first_publish_year")
        or book_metadata.get("release_date")
        or book_metadata.get("gutenberg_release_date")
    )
    content = book_path.read_text(encoding="utf-8")
    return {
        "id": id,
        "name": book_metadata["title"],
        "date": date,
        "author": book_metadata["author"],
        "content": content,
    }


@router.get("/similarities")
def get_similarities():
    """Return the precomputed pairwise similarities for available books."""
    similarities = load_similarities()
    book_ids = sorted(
        int(book_path.stem.removeprefix("book_"))
        for book_path in BOOKS_PATH.glob("book_*.txt")
    )

    links = []
    for index, id1 in enumerate(book_ids):
        for id2 in book_ids[index + 1 :]:
            try:
                similar_percent = similarities[str(id1)][str(id2)]
            except KeyError as error:
                raise HTTPException(
                    status_code=503,
                    detail=(
                        "Precomputed similarities are missing for "
                        f"books {id1} and {id2}."
                    ),
                ) from error
            links.append({
                "source": id1,
                "target": id2,
                "similar_percent": similar_percent,
            })

    return {"links": links}


@router.get("/similarities/you")
def get_user_similarities(
    read_book_ids: list[int] = Query(default=[]),
):
    """Calculate book similarities from the learner's combined read-book vocabulary."""
    if not read_book_ids:
        return {"links": []}

    book_paths = {
        int(book_path.stem.removeprefix("book_")): book_path
        for book_path in BOOKS_PATH.glob("book_*.txt")
    }
    unique_read_book_ids = set(read_book_ids)
    missing_ids = sorted(unique_read_book_ids - book_paths.keys())
    if missing_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Read books not found: {missing_ids}",
        )

    media_by_id = {
        book_id: Media.from_text_file(book_path)
        for book_id, book_path in book_paths.items()
    }
    vocabulary = LearnerVocabulary()
    for book_id in unique_read_book_ids:
        vocabulary.account_for_media(media_by_id[book_id])

    return {
        "links": [
            {
                "source": "you",
                "target": book_id,
                "similar_percent": vocabulary.know_percentage(media),
            }
            for book_id, media in sorted(media_by_id.items())
        ]
    }


@router.get("/similarity/{id1}/{id2}")
def get_similarity(
    id1: int,
    id2: int,
):
    """
    Return the vocabulary similarity between two books by their IDs.
    If either book does not exist, return an error message.
    """
    book1_path = BOOKS_PATH / f"book_{id1}.txt"
    book2_path = BOOKS_PATH / f"book_{id2}.txt"
    
    if not book1_path.exists() or not book2_path.exists():
        raise HTTPException(status_code=404, detail="One or both books not found")

    try:
        similar_percent = load_similarities()[str(id1)][str(id2)]
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail="Similarity not found for one or both book IDs",
        ) from error

    return {
        "source": str(book1_path.relative_to(PROJECT_ROOT)),
        "target": str(book2_path.relative_to(PROJECT_ROOT)),
        "similar_percent": similar_percent,
    }

@router.get("/path/{target_id}")
def get_path(
    target_id: str,
    comprehension_threshold: float = Query(
        default=0.8,
        ge=0.0,
        le=1.0,
    ),
):
    """
    Return the ordered list of books to read to reach the target book.
    """
    target_path = BOOKS_PATH / f"book_{target_id}.txt"
    if not target_path.is_file():
        raise HTTPException(status_code=404, detail="Target book not found")

    initial_vocabulary = LearnerVocabulary()
    reading_history = {}
    if READING_HISTORY_PATH.is_file():
        reading_history = json.loads(
            READING_HISTORY_PATH.read_text(encoding="utf-8")
        ).get("books", {})

    media_by_id = {}
    read_media_ids = set()
    for book_path in BOOKS_PATH.glob("book_*.txt"):
        book_id = book_path.stem.removeprefix("book_")
        media_by_id[book_id] = Media.from_text_file(book_path)

        history = reading_history.get(book_path.name, {})
        if history.get("is_read") is True:
            initial_vocabulary.account_for_media(media_by_id[book_id])
            read_media_ids.add(book_id)

    if target_id in read_media_ids:
        return []

    target_media = media_by_id[target_id]
    graph_media = [
        media
        for book_id, media in media_by_id.items()
        if book_id not in read_media_ids
    ]
    graph = Graph(
        tuple(graph_media),
        initial_vocabulary=initial_vocabulary,
        comprehension_threshold=comprehension_threshold,
    )

    try:
        result = PathFinder(graph).find_path(target_media)
    except LookupError:
        return []
    except TimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail="Path search exceeded its time limit",
        ) from exc

    id_by_media = {
        id(media): book_id
        for book_id, media in media_by_id.items()
    }
    return [
        {
            "id": id_by_media[id(media)],
            "name": f"book_{id_by_media[id(media)]}",
            "cost": sum(media.word_group_occurrences.values()),
        }
        for media in result.media
    ]