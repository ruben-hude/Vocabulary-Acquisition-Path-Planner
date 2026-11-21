import json
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BOOKS_PATH = PROJECT_ROOT / "data" / "raw" / "gutenberg_books" # Path to the folder containing the books
SIMILARITIES_PATH = PROJECT_ROOT / "data" / "raw" / "similarity_books.json"

router = APIRouter()


@lru_cache(maxsize=1)
def load_similarities() -> dict[str, dict[str, float]]:
    """Load the precomputed matrix once per server process."""
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


@router.get("/")
def get_index():
    return RedirectResponse(url="/render.html")


@router.get("/api/books")
def get_books():
    """
    Return a list of available books in the static folder.
    Each book is represented as a dictionary with its name and path.
    """
    books = []
    for file in BOOKS_PATH.glob("*.txt"):
        books.append({"name": file.stem, "path": str(file.relative_to(PROJECT_ROOT))})
    return {"books": books}

@router.get("/api/book/{id}")
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


@router.get("/api/similarities")
def get_similarities():
    """Return each precomputed pairwise similarity once."""
    similarities = load_similarities()
    links = []
    ids = sorted(int(book_id) for book_id in similarities)
    for index, id1 in enumerate(ids):
        for id2 in ids[index + 1 :]:
            links.append({
                "source": id1,
                "target": id2,
                "similar_percent": similarities[str(id1)][str(id2)],
            })

    return {"links": links}

@router.get("/api/similarity/{id1}/{id2}")
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
    
    similarities = load_similarities()
    try:
        similar_percent = similarities[str(id1)][str(id2)]
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
