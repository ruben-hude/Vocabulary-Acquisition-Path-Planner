"""Tests for learner vocabulary."""

import pytest

from vocabulary_acquisition_path_planner.models.learner_vocabulary import (
    LearnerVocabulary,
)
from vocabulary_acquisition_path_planner.models.media import Media


def test_media_words_become_known_after_the_exposure_threshold():
    vocabulary = LearnerVocabulary(exposure_threshold=10)
    media = Media({"play": 4, "read": 1})

    vocabulary.account_for_media(media)
    assert vocabulary.known_words == set()
    assert vocabulary.word_exposures == {"play": 4, "read": 1}

    vocabulary.account_for_media(media)
    assert vocabulary.known_words == set()
    assert vocabulary.word_exposures == {"play": 8, "read": 2}

    vocabulary.account_for_media(media)
    assert vocabulary.known_words == {"play"}
    assert vocabulary.word_exposures == {"read": 3}


def test_repeated_occurrences_in_one_media_count_as_repeated_exposures():
    vocabulary = LearnerVocabulary(exposure_threshold=101)
    media = Media({"play": 100})

    vocabulary.account_for_media(media)

    assert vocabulary.known_words == set()
    assert vocabulary.word_exposures == {"play": 100}


def test_known_words_are_not_counted_again():
    vocabulary = LearnerVocabulary(exposure_threshold=1)
    media = Media({"play": 1})

    vocabulary.account_for_media(media)
    vocabulary.account_for_media(media)

    assert vocabulary.known_words == {"play"}
    assert vocabulary.word_exposures == {}


def test_know_percentage_is_weighted_by_word_occurrences():
    vocabulary = LearnerVocabulary(exposure_threshold=1)
    vocabulary.account_for_media(Media({"play": 1}))

    percentage = vocabulary.know_percentage(Media({"play": 3, "read": 1}))

    assert percentage == 0.75


def test_exposure_threshold_must_be_positive():
    with pytest.raises(ValueError, match="at least 1"):
        LearnerVocabulary(exposure_threshold=0)
