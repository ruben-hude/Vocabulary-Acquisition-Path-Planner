"""Tests for the word-group registry."""

from vocabulary_acquisition_path_planner.models.word_group import (
    WordGroupRegistry,
)


def test_registry_is_a_singleton():
    first_registry = WordGroupRegistry()
    second_registry = WordGroupRegistry()

    assert first_registry is second_registry


def test_registry_is_initialized():
    registry = WordGroupRegistry()

    assert registry.is_initialized()
    assert registry.get_group_ids()


def test_headword_maps_to_itself():
    registry = WordGroupRegistry()

    assert registry.get_group_id("able") == "able"


def test_word_lookup_is_normalized():
    registry = WordGroupRegistry()

    assert registry.get_group_id("  ABLE ") == "able"


def test_group_contains_its_headword():
    registry = WordGroupRegistry()

    assert "able" in registry.get_words("able")


def test_related_words_share_a_group():
    registry = WordGroupRegistry()

    assert registry.get_group_id("play") == registry.get_group_id("player")


def test_unknown_word_is_not_in_registry():
    registry = WordGroupRegistry()

    assert registry.get_group_id("word-that-does-not-exist") is None
    assert not registry.contains("word-that-does-not-exist")


def test_unknown_group_has_no_words():
    registry = WordGroupRegistry()

    assert registry.get_words("group-that-does-not-exist") == ()
