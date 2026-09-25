"""Find a Gutenberg pair with a non-direct learning path."""

from pathlib import Path

from vocabulary_acquisition_path_planner.models.learner_vocabulary import (
    LearnerVocabulary,
)
from vocabulary_acquisition_path_planner.models.media import Media
from vocabulary_acquisition_path_planner.search.graph import Graph
from vocabulary_acquisition_path_planner.search.path_finder import PathFinder


BOOK_DIRECTORY = Path("data/raw/gutenberg_books")
THRESHOLD = 0.8
TIME_LIMIT_SECONDS = 5


def find_non_obvious_path():
    """Return the first pair with a sub-threshold direct route and a path."""
    paths = sorted(BOOK_DIRECTORY.glob("*.txt"))
    books = {path: Media.from_text_file(path) for path in paths}

    for source_path in paths:
        source_media = books[source_path]
        vocabulary = LearnerVocabulary()
        vocabulary.account_for_media(source_media)

        for target_path in paths:
            if target_path == source_path:
                continue

            target_media = books[target_path]
            direct_coverage = vocabulary.know_percentage(target_media)
            if direct_coverage >= THRESHOLD:
                continue

            intermediates = [
                media
                for path, media in books.items()
                if path not in {source_path, target_path}
            ]
            graph = Graph(
                intermediates + [target_media],
                initial_vocabulary=vocabulary,
                comprehension_threshold=THRESHOLD,
            )

            try:
                result = PathFinder(graph).find_path(
                    target_media,
                    time_limit_seconds=TIME_LIMIT_SECONDS,
                )
            except (LookupError, TimeoutError):
                continue

            if len(result.media) > 1:
                media_to_path = {id(media): path for path, media in books.items()}
                result_paths = tuple(
                    media_to_path[id(media)] for media in result.media
                )
                return (
                    source_path,
                    target_path,
                    direct_coverage,
                    result,
                    result_paths,
                )

    return None


def main():
    """Print a reproducible non-obvious path, if one exists."""
    match = find_non_obvious_path()
    if match is None:
        print("No non-obvious path found.")
        return

    source_path, target_path, direct_coverage, result, result_paths = match
    print(f"Source: {source_path}")
    print(f"Target: {target_path}")
    print(f"Direct target coverage: {direct_coverage:.2%}")
    print(f"Path cost: {result.cost}")
    print("Recommended reading path after the source book:")
    for path in result_paths:
        print(f"  {path}")


if __name__ == "__main__":
    main()
