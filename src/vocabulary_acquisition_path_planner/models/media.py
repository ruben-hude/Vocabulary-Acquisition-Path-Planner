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
        return cls._from_text(text)

    @classmethod
    def from_subtitle(cls, subtitle_source, media_type="movie"):
        """Create media from subtitles for a movie or series.

        Movies expect a single subtitle file path.
        Series may be a directory containing ``*.srt`` files or an iterable of
        subtitle file paths.
        """
        if media_type == "movie":
            text = cls._subtitle_text_from_file(subtitle_source)
            return cls._from_text(text)

        if media_type == "series":
            subtitle_paths = cls._resolve_series_subtitle_paths(subtitle_source)
            merged_occurrences = {}
            for subtitle_path in subtitle_paths:
                subtitle_media = cls.from_subtitle(subtitle_path, media_type="movie")
                for group_id, count in subtitle_media.word_group_occurrences.items():
                    merged_occurrences[group_id] = (
                        merged_occurrences.get(group_id, 0) + count
                    )
            return cls(merged_occurrences)

        raise ValueError("media_type must be 'movie' or 'series'")

    @classmethod
    def _from_text(cls, text):
        """Create media by counting known word groups in text."""
        registry = WordGroupRegistry()
        occurrences = {}

        for word in cls._word_pattern.findall(text):
            group_id = registry.get_group_id(word)
            if group_id is not None:
                occurrences[group_id] = occurrences.get(group_id, 0) + 1

        return cls(occurrences)

    @staticmethod
    def _subtitle_text_from_file(file_path):
        """Return subtitle dialogue text without numbering and timestamps."""
        subtitle_text = Path(file_path).read_text(encoding="utf-8")
        subtitle_lines = []
        for line in subtitle_text.splitlines():
            stripped_line = line.strip()
            if not stripped_line or stripped_line.isdigit():
                continue
            if "-->" in stripped_line:
                continue
            subtitle_lines.append(stripped_line)
        return "\n".join(subtitle_lines)

    @staticmethod
    def _resolve_series_subtitle_paths(subtitle_source):
        """Return ordered subtitle paths for a series source."""
        if isinstance(subtitle_source, (str, Path)):
            source_path = Path(subtitle_source)
            if source_path.is_dir():
                return sorted(source_path.glob("*.srt"))
            return [source_path]
        return subtitle_source

    @property
    def word_group_occurrences(self):
        """Return the word-group occurrence counts."""
        return dict(self._word_group_occurrences)
