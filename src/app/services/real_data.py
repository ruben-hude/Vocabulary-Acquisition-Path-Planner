from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from app.models import (
    CurrentPath,
    PathStep,
    Preferences,
    Profile,
    ReadBook,
    VocabularyPoint,
)
from vocabulary_acquisition_path_planner.models.learner_vocabulary import (
    LearnerVocabulary,
)
from vocabulary_acquisition_path_planner.models.media import Media
from vocabulary_acquisition_path_planner.models.processed.reading_history import (
    ReadingHistory,
)

# Chemins vers les dossiers de données (depuis src/app/services/real_data.py -> parents[3] = racine du projet)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
BOOKS_PATH = PROJECT_ROOT / "data" / "raw" / "gutenberg_books"
HISTORY_PATH = PROJECT_ROOT / "data" / "processed" / "reading_history.json"
PREFS_PATH = PROJECT_ROOT / "data" / "processed" / "user_preferences.json"

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def _estimate_cefr_level(known_words_count: int) -> str:
    """Estime le niveau CECRL selon le nombre de groupes de mots connus."""
    if known_words_count < 1000:
        return "A2"
    if known_words_count < 2500:
        return "B1"
    if known_words_count < 4000:
        return "B2"
    return "C1"


def _format_title(book_id: str) -> str:
    """Transforme 'book_1' ou 'pride-and-prejudice' en titre lisible."""
    return book_id.replace("_", " ").replace("-", " ").title()


def _resolve_book_path(book_id: str, raw_source_path: str | None) -> Path | None:
    """Retrouve le fichier .txt du livre sur le disque."""
    if raw_source_path:
        p = Path(raw_source_path)
        if not p.is_absolute():
            p = PROJECT_ROOT / p
        if p.exists():
            return p

    for candidate in (BOOKS_PATH / f"{book_id}.txt", BOOKS_PATH / f"book_{book_id}.txt"):
        if candidate.exists():
            return candidate
    return None


def _compute_learner_state():
    """Parcourt reading_history.json, calcule le vocabulaire acquis et l'historique."""
    history_store = ReadingHistory(HISTORY_PATH)
    vocab = LearnerVocabulary()

    read_entries: list[tuple[str, str, Path]] = []
    for book_id, info in history_store._books.items():
        if not info.get("is_read", False):
            continue
        last_date = history_store.last_read_at(book_id) or "2026-01-01"
        book_path = _resolve_book_path(book_id, str(info.get("source_path", "")))
        if book_path is not None:
            read_entries.append((last_date, book_id, book_path))

    # Tri chronologique des lectures pour calculer les mots nouvellement appris à chaque livre
    read_entries.sort(key=lambda item: item[0])

    read_books: list[ReadBook] = []
    words_by_month: dict[str, int] = defaultdict(int)
    first_month_str = "June 2026"

    for idx, (raw_date, book_id, book_path) in enumerate(read_entries):
        before_count = len(vocab.known_words)
        media = Media.from_text_file(book_path)
        vocab.account_for_media(media)
        after_count = len(vocab.known_words)
        learned = after_count - before_count

        # Parsing de la date ISO (ex: "2026-10-28T14:30:00+00:00" ou "2026-10-28")
        iso_day = raw_date[:10]
        try:
            dt = datetime.fromisoformat(iso_day)
            month_name = MONTH_NAMES[dt.month - 1]
            if idx == 0:
                first_month_str = f"{month_name} {dt.year}"
        except ValueError:
            month_name = "June"

        words_by_month[month_name] = after_count

        read_books.append(
            ReadBook(
                id=book_id,
                title=_format_title(book_id),
                author="Auteur inconnu",
                level=_estimate_cefr_level(after_count),
                completed_at=iso_day,
                learned_words=learned,
            )
        )

    # Liste des derniers livres lus (les plus récents en premier)
    read_books.reverse()

    total_known = len(vocab.known_words)
    level = _estimate_cefr_level(total_known)

    history_points = [
        VocabularyPoint(month=m, known_words=count)
        for m, count in words_by_month.items()
    ]
    if not history_points:
        history_points = [VocabularyPoint(month="June", known_words=total_known)]

    return vocab, read_books, total_known, level, first_month_str, history_points


def get_profile() -> Profile:
    _, read_books, total_known, level, member_since, history_points = _compute_learner_state()
    return Profile(
        name="Camille",
        member_since=member_since,
        level=level,
        known_words=total_known,
        nb_read_books=len(read_books),
        history=history_points,
    )


def get_read_books() -> list[ReadBook]:
    _, read_books, _, _, _, _ = _compute_learner_state()
    return read_books


def get_current_path() -> CurrentPath:
    """Construit un parcours progressif à partir des prochains livres disponibles non lus."""
    vocab, _, _, _, _, _ = _compute_learner_state()
    history_store = ReadingHistory(HISTORY_PATH)

    candidates: list[tuple[float, int, str]] = []
    if BOOKS_PATH.exists():
        for file in sorted(BOOKS_PATH.glob("*.txt")):
            book_id = file.stem
            if history_store.is_read(book_id):
                continue
            media = Media.from_text_file(file)
            known_pct = vocab.know_percentage(media)
            # Nombre de groupes de mots pas encore connus dans ce livre
            unseen = sum(
                1 for wg in media.word_group_occurrences if wg not in vocab.known_words
            )
            candidates.append((known_pct, unseen, book_id))

    # Tri du plus accessible (plus haut % connu) au plus difficile (futur livre cible)
    candidates.sort(key=lambda item: item[0], reverse=True)
    selected = candidates[:4]

    if not selected:
        return CurrentPath(
            target_id="none",
            target_title="Aucun livre disponible",
            path_type="progressive",
            steps=[],
        )

    steps: list[PathStep] = []
    for idx, (known_pct, unseen, book_id) in enumerate(selected):
        is_last = idx == len(selected) - 1
        status = "target" if is_last else ("in_progress" if idx == 0 else "upcoming")
        steps.append(
            PathStep(
                book_id=book_id,
                title=_format_title(book_id),
                author="Project Gutenberg",
                level="C1" if is_last else ("B2" if known_pct < 0.85 else "B1"),
                new_words=unseen,
                status=status,
            )
        )

    target_step = steps[-1]
    return CurrentPath(
        target_id=target_step.book_id,
        target_title=target_step.title,
        path_type="progressive",
        steps=steps,
    )


def get_preferences() -> Preferences:
    if PREFS_PATH.exists():
        data = json.loads(PREFS_PATH.read_text(encoding="utf-8"))
        return Preferences(**data)
    return Preferences(genres=["Classics", "Fantasy"], favorite_books=[])


def save_preferences(new_preferences: Preferences) -> Preferences:
    PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PREFS_PATH.write_text(
        json.dumps(new_preferences.model_dump(), indent=2) + "\n",
        encoding="utf-8",
    )
    return new_preferences