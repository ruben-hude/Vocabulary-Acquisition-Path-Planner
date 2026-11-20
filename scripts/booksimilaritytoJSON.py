"""Build a JSON file containing each similarity score between a book and each another book"""

import json
from vocabulary_acquisition_path_planner.models.media import Media
from vocabulary_acquisition_path_planner.models.learner_vocabulary import LearnerVocabulary

from pathlib import Path

"importe le json de bouquin"
path=Path(__file__).resolve().parents[1] / "data" / "raw" / "book_similarity.json"
with open(path, "r", encoding="utf-8") as f:
    books = json.load(f)

"dictionnaire des livres dans gutenberg et dictionnaire de leurs id"
BOOK_DIRECTORY = Path("data/raw/gutenberg_books")
paths = sorted(BOOK_DIRECTORY.glob("*.txt"))
Books = {path: Media.from_text_file(path) for path in paths}
Ids = {media.id: media for media in Books.values()}


def build_book_similarity_json(books:json):
    """
    Build a JSON file containing each similarity score between a book and each other book.

    Args:
        books (dict): A dictionary where keys are book IDs and values are book details."""

    similarity_dict = {}
    books_id = list(books.keys())
    for book_id in books_id:
        similarity_dict[book_id] = {}
        for other_book_id in book_id:
            if book_id != other_book_id:
                similarity_dict[book_id][other_book_id] = similarity_id(book_id, other_book_id, books)

def similarity_id(book_id:str, other_book_id:str, books:json):
    """
    Get the similarity score between the book associated to book_id and the book associated to other_book_id.
    Args:
        book_id (str) : The ID of the first book.
        other_book_id (str) : The ID of the second book.
        books (dict) : A dictionary where keys are book IDs and values are book details."""
    book1 = books[book_id]
    book2 = books[other_book_id]
    common_word_group = common_word_groups(book1, book2)
    total_word_group = total_word_groups(book1, book2)
    if total_word_group == 0:
        return 0.0
    elif common_word_group == -1:
        return "Certains livres de la liste ne sont pas enregistrés en local, veuillez les ajouter pour calculer la similarité."
    return len(common_word_group) / total_word_group

def common_word_groups(book1:dict, book2:dict):
    """
    Get the common word groups bewteen two books.
    Args:
        book1 (dict) : The first book.
        book2 (dict) : The second book. """
    if book1["id"] in Ids and book2["id"] in Ids:
        vocabulary = LearnerVocabulary()
        vocabulary.account_for_media(book1)
        percent_known = vocabulary.know_percentage(book2)
        common_word_groups = int(percent_known * total_word_groups(book1, book2))
        return common_word_groups
    else: 
        return -1
    

def total_word_groups(book1:dict, book2:dict):
    """
    Get the total number of word groups between two books.
    Args:
        book1 (dict) : The first book.
        book2 (dict) : The second book. """
    return book1["word_count"] + book2["word_count"]
    


"notes: estce que dans books_metadata, word_count = nbe total de mot ou"
"word count = nbe de groupe de mots ?"