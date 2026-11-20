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


def test_media_counts_word_groups_from_movie_subtitles(tmp_path):
    subtitle_file = tmp_path / "movie.srt"
    subtitle_file.write_text(
        "1\n"
        "00:00:00,000 --> 00:00:02,000\n"
        "Play!\n\n"
        "2\n"
        "00:00:02,000 --> 00:00:04,000\n"
        "playing player\n",
        encoding="utf-8",
    )

    media = Media.from_subtitle(subtitle_file, media_type="movie")

    assert media.word_group_occurrences["play"] == 3


def test_media_counts_word_groups_from_series_subtitles(tmp_path):
    series_dir = tmp_path / "series"
    series_dir.mkdir()
    (series_dir / "episode_1.srt").write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nplay\n",
        encoding="utf-8",
    )
    (series_dir / "episode_2.srt").write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nplayer playing\n",
        encoding="utf-8",
    )

    media = Media.from_subtitle(series_dir, media_type="series")

    assert media.word_group_occurrences["play"] == 3
