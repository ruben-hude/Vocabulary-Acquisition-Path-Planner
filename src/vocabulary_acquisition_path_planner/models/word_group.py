"""Registry for groups of related words."""

from pathlib import Path
import re

import pandas as pd


excel_path = (
    Path(__file__).resolve().parents[3] / "data" / "BNC_COCA_lists.xlsx"
)


class WordGroupRegistry:
    """Map words to stable identifiers for their word groups."""

    _instance = None
    _initialized = False
    _form_to_group_id = {}
    _group_id_to_words = {}
    _group_info = {}

    def __new__(cls):
        """Return the single registry instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Load the word-group data once."""
        cls = type(self)
        if cls._initialized:
            return

        self.initialize()
        cls._initialized = True

    def get_group_id(self, word):
        """Return the group identifier associated with a word.

        Return ``None`` when the word is not present in the registry.
        """
        normalized_word = self._normalize_word(word)
        return type(self)._form_to_group_id.get(normalized_word)

    def contains(self, word):
        """Return whether the registry contains a word."""
        return self.get_group_id(word) is not None

    def get_words(self, group_id):
        """Return all words associated with a group identifier."""
        return tuple(type(self)._group_id_to_words.get(group_id, ()))

    def get_group_ids(self):
        """Return all known group identifiers."""
        return tuple(type(self)._group_id_to_words)

    def initialize(self):
        """Load and index the word-group data from the Excel file."""
        cls = type(self)
        dataframe = pd.read_excel(excel_path)
        dataframe.columns = [str(column).strip() for column in dataframe.columns]

        required_columns = {"Headword", "Related forms", "List"}
        missing_columns = required_columns.difference(dataframe.columns)
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"Vocabulary file is missing columns: {missing}")

        form_to_group_id = {}
        group_id_to_words = {}
        group_info = {}

        for _, row in dataframe.iterrows():
            if pd.isna(row["Headword"]):
                continue

            group_id = self._normalize_word(row["Headword"])
            if not group_id:
                continue

            group_info[group_id] = {"List": str(row["List"]).strip()}
            group_words = group_id_to_words.setdefault(group_id, set())
            group_words.add(group_id)
            form_to_group_id[group_id] = group_id

            if pd.isna(row["Related forms"]):
                continue

            related_forms = re.findall(
                r"([\w'-]+)\s*\(\d+\)",
                str(row["Related forms"]),
            )
            for form in related_forms:
                normalized_form = self._normalize_word(form)
                if normalized_form:
                    form_to_group_id[normalized_form] = group_id
                    group_words.add(normalized_form)

        cls._form_to_group_id = form_to_group_id
        cls._group_id_to_words = {
            group_id: tuple(sorted(words))
            for group_id, words in group_id_to_words.items()
        }
        cls._group_info = group_info

    def is_initialized(self):
        """Return whether the registry has been initialized."""
        return type(self)._initialized

    @staticmethod
    def _normalize_word(word):
        """Return the normalized representation used by the indexes."""
        if not isinstance(word, str):
            return ""
        return word.strip().lower()
