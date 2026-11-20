from typing import Literal
from pydantic import BaseModel


class VocabularyPoint(BaseModel):
    month: str
    known_words: int


class Profile(BaseModel):
    name: str
    member_since: str
    level: str
    known_words: int
    history: list[VocabularyPoint]


class ReadBook(BaseModel):
    id: str
    title: str
    author: str
    level: str
    completed_at: str
    learned_words: int
    cover_url: str


class PathStep(BaseModel):
    book_id: str
    title: str
    author: str
    level: str
    new_words: int
    status: Literal["read", "in_progress", "upcoming", "target"]


class CurrentPath(BaseModel):
    target_id: str
    target_title: str
    path_type: str
    steps: list[PathStep]


class Preferences(BaseModel):
    genres: list[str]
    favorite_books: list[str]


class Node(BaseModel):
    id: str
    title: str
    author: str
    level: str
    pages: int
    known_percentage: float
    new_words: int
    is_target: bool = False


class Link(BaseModel):
    source: str
    target: str
    path_id: str


class PathSummary(BaseModel):
    id: str
    name: str
    books: list[str]
    duration_hours: int
    difficulty: str
    learned_words: int


class Graph(BaseModel):
    nodes: list[Node]
    links: list[Link]
    paths: list[PathSummary]