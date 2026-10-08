"""Fake backend 100% compatible with the Tkinter/CustomTkinter GUI."""

from pathlib import Path


class WordGroupRegistry:
    """Mock for the word group registry."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._mock_groups = {"play", "work", "read", "book", "story", "time"}
        return cls._instance

    def contains(self, word: str) -> bool:
        """Check if a word is in the registry."""
        return word.lower().strip() in self._mock_groups

    def get_group_id(self, word: str) -> str | None:
        """Return group ID or None if unknown."""
        normalized = word.lower().strip()
        return normalized if self.contains(normalized) else None


class Media:
    """Mock for a text or learning media item."""

    def __init__(self, occurrences: dict[str, int] | None = None):
        self._occurrences = occurrences or {"play": 10, "read": 5, "story": 2}

    @classmethod
    def from_text_file(cls, file_path: Path | str) -> "Media":
        """Simulate loading and parsing a text file."""
        path = Path(file_path)
        # Generate dummy occurrence counts based on file name length
        base_count = len(path.stem) * 5
        return cls({
            "play": base_count,
            "read": base_count // 2 + 1,
            "story": base_count // 3 + 1,
            "work": base_count // 4,
        })

    @property
    def word_group_occurrences(self) -> dict[str, int]:
        """Return word group occurrence count mapping."""
        return dict(self._occurrences)


class LearnerVocabulary:
    """Mock for tracking learner vocabulary state."""

    def __init__(self, exposure_threshold: int = 10):
        self.exposure_threshold = exposure_threshold
        self._known_words: set[str] = set()
        self._word_exposures: dict[str, int] = {}

    def account_for_media(self, media: Media) -> None:
        """Simulate media processing and word exposure accumulation."""
        for word, count in media.word_group_occurrences.items():
            current = self._word_exposures.get(word, 0) + count
            if current >= self.exposure_threshold:
                self._known_words.add(word)
                self._word_exposures.pop(word, None)
            else:
                self._word_exposures[word] = current

    def know_percentage(self, media: Media) -> float:
        """Calculate mock comprehension percentage for given media."""
        if not media.word_group_occurrences:
            return 0.0
        known_in_media = sum(
            count for word, count in media.word_group_occurrences.items()
            if word in self._known_words
        )
        total = sum(media.word_group_occurrences.values())
        return known_in_media / total if total > 0 else 0.0

    @property
    def known_words(self) -> set[str]:
        return set(self._known_words)

    @property
    def word_exposures(self) -> dict[str, int]:
        return dict(self._word_exposures)


class Graph:
    """Mock for implicit media graph."""

    def __init__(
        self,
        media_list: list[Media],
        initial_vocabulary: LearnerVocabulary | None = None,
        comprehension_threshold: float = 0.8,
    ):
        self.media = tuple(media_list)
        self.initial_vocabulary = initial_vocabulary or LearnerVocabulary()
        self.comprehension_threshold = comprehension_threshold


class PathResult:
    """Represents a path returned by PathFinder."""

    def __init__(self, media_list: list[Media], cost: int):
        self.media = tuple(media_list)
        self.cost = cost


class PathFinder:
    """Mock for Dijkstra search algorithm."""

    def __init__(self, graph: Graph):
        self.graph = graph

    def find_path(self, target_media: Media, time_limit_seconds: float | None = None) -> PathResult:
        """Simulate path search."""
        # Return dummy sequence using available graph media
        path = [m for m in self.graph.media if m is not target_media][:2]
        if target_media not in path:
            path.append(target_media)

        total_cost = sum(sum(m.word_group_occurrences.values()) for m in path)
        return PathResult(path, cost=total_cost)