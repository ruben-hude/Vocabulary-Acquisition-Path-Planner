"""Models for learning media."""

from pathlib import Path
import re

from vocabulary_acquisition_path_planner.models.word_group import (
    WordGroupRegistry,
)


class Media:
    """Represent a piece of learning media."""

    _word_pattern = re.compile(r"[A-Za-z]+(?:['-][A-Za-z]+)*")

    def __init__(self, word_group_occurrences=None):
        """Create media from an optional word-group occurrence mapping."""
        self._word_group_occurrences = dict(word_group_occurrences or {})

    @classmethod
    def from_text_file(cls, file_path):
        """Create media by counting known word groups in a text file."""
        text = Path(file_path).read_text(encoding="utf-8")
        registry = WordGroupRegistry()
        occurrences = {}

        for word in cls._word_pattern.findall(text):
            group_id = registry.get_group_id(word)
            if group_id is not None:
                occurrences[group_id] = occurrences.get(group_id, 0) + 1

        return cls(occurrences)

    @property
    def word_group_occurrences(self):
        """Return the word-group occurrence counts."""
        return dict(self._word_group_occurrences)
