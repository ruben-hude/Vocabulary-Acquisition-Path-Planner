from pathlib import Path

import json

from fastapi import APIRouter, HTTPException, Query, Query
from fastapi.responses import RedirectResponse

from vocabulary_acquisition_path_planner.models.learner_vocabulary import (
    LearnerVocabulary,
)
from vocabulary_acquisition_path_planner.models.media import Media
from vocabulary_acquisition_path_planner.search.graph import Graph
from vocabulary_acquisition_path_planner.search.path_finder import PathFinder

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BOOKS_PATH = PROJECT_ROOT / "data" / "raw" / "gutenberg_books" # Path to the folder containing the books
READING_HISTORY_PATH = PROJECT_ROOT / "data" / "processed" / "reading_history.json"

router = APIRouter(prefix="/api", tags=["path"])


@router.get("/")
def get_index():
    return RedirectResponse(url="/render.html")


@router.get("/books")
def get_books():
    """
    Return a list of available books in the static folder.
    Each book is represented as a dictionary with its name and path.
    """
    books = []
    for file in BOOKS_PATH.glob("*.txt"):
        books.append({"name": file.stem, "path": str(file.relative_to(PROJECT_ROOT))})
    return {"books": books}

@router.get("/book/{id}")
def get_book(id: int):
    """
    Return the content of a specific book by its name.
    If the book does not exist, return an error message.
    """
    book_path = BOOKS_PATH / f"book_{id}.txt"
    if not book_path.exists():
        raise HTTPException(status_code=404, detail="Book not found")
    
    content = book_path.read_text(encoding="utf-8")
    # TODO: Return the name, description, content, and additional information (date, author, ...).
    return {"id": id, "name": book_path.stem, "content": content}


@router.get("/similarities")
def get_similarities():
    """Return every pairwise similarity for the available books."""
    media_by_id = {}
    for book_path in BOOKS_PATH.glob("book_*.txt"):
        id = int(book_path.stem.removeprefix("book_"))
        media_by_id[id] = Media.from_text_file(book_path)

    links = []
    ids = sorted(media_by_id)
    for index, id1 in enumerate(ids):
        book_vocab = LearnerVocabulary()
        book_vocab.account_for_media(media_by_id[id1])
        for id2 in ids[index + 1 :]:
            similar_percent = book_vocab.know_percentage(media_by_id[id2])
            links.append({
                "source": id1,
                "target": id2,
                "similar_percent": similar_percent,
            })

    return {"links": links}

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
    
    source = Media.from_text_file(book1_path)
    target = Media.from_text_file(book2_path)
    book_vocab = LearnerVocabulary()
    book_vocab.account_for_media(source)

    return {
        "source": str(book1_path.relative_to(PROJECT_ROOT)),
        "target": str(book2_path.relative_to(PROJECT_ROOT)),
        "similar_percent": book_vocab.know_percentage(target),
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