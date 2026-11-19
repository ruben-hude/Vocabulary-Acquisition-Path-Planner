from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from vocabulary_acquisition_path_planner.models.learner_vocabulary import (
    LearnerVocabulary,
)
from vocabulary_acquisition_path_planner.models.media import Media

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BOOKS_PATH = PROJECT_ROOT / "data" / "raw" / "gutenberg_books" # Path to the folder containing the books

router = APIRouter()


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
    
    source = Media.from_text_file(book1_path)
    target = Media.from_text_file(book2_path)
    book_vocab = LearnerVocabulary()
    book_vocab.account_for_media(source)

    return {
        "source": str(book1_path.relative_to(PROJECT_ROOT)),
        "target": str(book2_path.relative_to(PROJECT_ROOT)),
        "similar_percent": book_vocab.know_percentage(target),
    }
