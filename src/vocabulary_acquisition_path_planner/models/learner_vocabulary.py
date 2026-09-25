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
        """Account for one view of every word group contained in media."""
        for word_group in media.word_group_occurrences:
            if word_group in self._known_words:
                continue

            exposures = self._word_exposures.get(word_group, 0) + 1
            if exposures >= self.exposure_threshold:
                self._known_words.add(word_group)
                self._word_exposures.pop(word_group, None)
            else:
                self._word_exposures[word_group] = exposures

    @property
    def known_words(self):
        """Return the word groups currently known by the learner."""
        return set(self._known_words)

    @property
    def word_exposures(self):
        """Return exposure counts for word groups not yet known."""
        return dict(self._word_exposures)
