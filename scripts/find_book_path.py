"""Find a learning path between two Gutenberg books."""

import argparse
from pathlib import Path

from vocabulary_acquisition_path_planner.models.learner_vocabulary import (
    LearnerVocabulary,
)
from vocabulary_acquisition_path_planner.models.media import Media
from vocabulary_acquisition_path_planner.search.graph import Graph
from vocabulary_acquisition_path_planner.search.path_finder import PathFinder


def main():
    """Run a bounded path search from one book to another."""
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument(
        "--comprehension-threshold",
        type=float,
        default=0.8,
    )
    parser.add_argument("--time-limit-seconds", type=float, default=10)
    args = parser.parse_args()

    source = Media.from_text_file(args.source)
    target = Media.from_text_file(args.target)
    vocabulary = LearnerVocabulary()
    vocabulary.account_for_media(source)

    book_paths = sorted(args.source.parent.glob("*.txt"))
    book_paths = [
        path for path in book_paths if path not in {args.source, args.target}
    ]
    books = [(path, Media.from_text_file(path)) for path in book_paths]
    media = [book_media for _, book_media in books] + [target]

    graph = Graph(
        media,
        initial_vocabulary=vocabulary,
        comprehension_threshold=args.comprehension_threshold,
    )
    print(f"Source: {args.source}")
    print(f"Target: {args.target}")
    print(f"Initial known groups: {len(vocabulary.known_words)}")
    print(f"Target coverage: {vocabulary.know_percentage(target):.2%}")
    try:
        result = PathFinder(graph).find_path(
            target,
            time_limit_seconds=args.time_limit_seconds,
        )
    except LookupError:
        print(
            "No path exists with the available books and the configured "
            f"{args.comprehension_threshold:.0%} comprehension threshold."
        )
        return

    print(f"Path cost: {result.cost}")
    print("Recommended reading path after the source book:")
    for selected_media in result.media:
        if selected_media is target:
            print(f"  {args.target}")
            continue
        for path, book_media in books:
            if selected_media is book_media:
                print(f"  {path}")
                break


if __name__ == "__main__":
    main()
