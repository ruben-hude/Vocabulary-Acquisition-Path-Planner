"""Tests for learner vocabulary."""

import pytest

from vocabulary_acquisition_path_planner.models.learner_vocabulary import (
    LearnerVocabulary,
)
from vocabulary_acquisition_path_planner.models.media import Media


def test_media_words_become_known_after_the_exposure_threshold():
    vocabulary = LearnerVocabulary(exposure_threshold=2)
    media = Media({"play": 4, "read": 1})

    vocabulary.account_for_media(media)
    assert vocabulary.known_words == set()
    assert vocabulary.word_exposures == {"play": 1, "read": 1}

    vocabulary.account_for_media(media)
    assert vocabulary.known_words == {"play", "read"}
    assert vocabulary.word_exposures == {}


def test_known_words_are_not_counted_again():
    vocabulary = LearnerVocabulary(exposure_threshold=1)
    media = Media({"play": 1})

    vocabulary.account_for_media(media)
    vocabulary.account_for_media(media)

    assert vocabulary.known_words == {"play"}
    assert vocabulary.word_exposures == {}


def test_exposure_threshold_must_be_positive():
    with pytest.raises(ValueError, match="at least 1"):
        LearnerVocabulary(exposure_threshold=0)
