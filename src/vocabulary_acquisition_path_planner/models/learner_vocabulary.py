"""Models for a learner's vocabulary."""


class LearnerVocabulary:
    """Represent the vocabulary known by a learner."""

    def __init__(self, exposure_threshold=10):
        """Create an empty vocabulary with a configurable exposure threshold."""
        if exposure_threshold < 1:
            raise ValueError("exposure_threshold must be at least 1")

        self.exposure_threshold = exposure_threshold
        self._known_words = set()
        self._word_exposures = {}

    def account_for_media(self, media):
        """Account for each occurrence of every word group contained in media."""
        for word_group, occurrence_count in media.word_group_occurrences.items():
            if word_group in self._known_words:
                continue

            exposures = (
                self._word_exposures.get(word_group, 0) + occurrence_count
            )
            if exposures >= self.exposure_threshold:
                self._known_words.add(word_group)
                self._word_exposures.pop(word_group, None)
            else:
                self._word_exposures[word_group] = exposures

    def know_percentage(self, media):
        """Give the percentage of known vocabulary in a media."""
        nb_known_words = 0
        nb_total_words = 0

        for word_group, occurrence_count in (
            media.word_group_occurrences.items()
        ):
            nb_total_words += occurrence_count
            if word_group in self._known_words:
                nb_known_words += occurrence_count

        if nb_total_words == 0:
            return 0.0

        return nb_known_words / nb_total_words

    @property
    def known_words(self):
        """Return the word groups currently known by the learner."""
        return set(self._known_words)

    @property
    def word_exposures(self):
        """Return exposure counts for word groups not yet known."""
        return dict(self._word_exposures)
