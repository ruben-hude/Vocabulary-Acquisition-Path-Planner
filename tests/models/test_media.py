"""Tests for learning media."""

from vocabulary_acquisition_path_planner.models.media import Media


def test_media_counts_word_groups_from_text_file(tmp_path):
    text_file = tmp_path / "story.txt"
    text_file.write_text(
        "Play, player, and PLAYING. Unknown words are ignored.",
        encoding="utf-8",
    )

    media = Media.from_text_file(text_file)

    assert media.word_group_occurrences["play"] == 3


def test_media_does_not_expose_mutable_internal_state(tmp_path):
    text_file = tmp_path / "story.txt"
    text_file.write_text("play", encoding="utf-8")
    media = Media.from_text_file(text_file)

    occurrences = media.word_group_occurrences
    occurrences["play"] = 0

    assert media.word_group_occurrences["play"] == 1
