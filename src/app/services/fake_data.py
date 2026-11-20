from app.models import (
    CurrentPath, Graph, Link, Node, PathStep, PathSummary, Preferences,
    Profile, ReadBook, VocabularyPoint,
)

_preferences = Preferences(genres=["Fantasy", "Classics"], favorite_books=["narnia"])


def get_profile() -> Profile:
    words = [2100, 2380, 2650, 2900, 3050, 3200]
    months = ["June", "July", "August", "September", "October", "November"]
    return Profile(
        name="User Name",
        member_since="June 2026",
        level="B2",
        known_words=3200,
        nb_read_books= 14,
        history=[VocabularyPoint(month=month, known_words=value)
                 for month, value in zip(months, words)],
    )


def get_read_books() -> list[ReadBook]:
    return [
        ReadBook(id="psychology-of-money", title="The Psychology of Money",
                 author="Morgan Housel", level="B2", completed_at="2026-10-28",
                 learned_words=210),
        ReadBook(id="dorian-gray", title="The Picture of Dorian Gray",
                 author="Oscar Wilde", level="B2", completed_at="2026-10-03",
                 learned_words=320),
    ]


def get_current_path() -> CurrentPath:
    return CurrentPath(
        target_id="pride-and-prejudice",
        target_title="Pride and Prejudice",
        path_type="progressive",
        steps=[
            PathStep(book_id="charlottes-web", title="Charlotte's Web", author="E. B. White",
                     level="A2", new_words=150, status="read"),
            PathStep(book_id="little-prince", title="The Little Prince",
                     author="A. de Saint-Exupéry", level="B1", new_words=210,
                     status="in_progress"),
            PathStep(book_id="animal-farm", title="Animal Farm", author="George Orwell",
                     level="B1", new_words=340, status="upcoming"),
            PathStep(book_id="pride-and-prejudice", title="Pride and Prejudice",
                     author="Jane Austen", level="C1", new_words=1250, status="target"),
        ],
    )


def get_graph(target_id: str) -> Graph | None:
    if target_id != "pride-and-prejudice":
        return None                      # cible inconnue
    return Graph(
        nodes=[
            Node(id="charlottes-web", title="Charlotte's Web", author="E. B. White", level="A2",
                 pages=184, known_percentage=92, new_words=150),
            Node(id="animal-farm", title="Animal Farm", author="George Orwell", level="B1",
                 pages=112, known_percentage=85, new_words=340),
            Node(id="pride-and-prejudice", title="Pride and Prejudice", author="Jane Austen",
                 level="C1", pages=432, known_percentage=72, new_words=1250, is_target=True),
        ],
        links=[
            Link(source="charlottes-web", target="animal-farm", path_id="progressive"),
            Link(source="animal-farm", target="pride-and-prejudice", path_id="progressive"),
        ],
        paths=[
            PathSummary(id="progressive", name="Progressive path",
                        books=["charlottes-web", "animal-farm"], duration_hours=12,
                        difficulty="Easy", learned_words=700),
        ],
    )


def get_preferences() -> Preferences:
    return _preferences


def save_preferences(new_preferences: Preferences) -> Preferences:
    global _preferences
    _preferences = new_preferences
    return _preferences