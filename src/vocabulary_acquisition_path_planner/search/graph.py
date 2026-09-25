"""Implicit graph for planning a sequence of learning media."""

from copy import deepcopy
from dataclasses import dataclass

from vocabulary_acquisition_path_planner.models.learner_vocabulary import (
    LearnerVocabulary,
)
from vocabulary_acquisition_path_planner.models.media import Media


@dataclass
class Vertex:
    """A position in the media graph."""

    media: Media | None
    vocabulary: LearnerVocabulary


@dataclass
class Edge:
    """A transition to the next media in the graph."""

    target: Vertex
    cost: int


class Graph:
    """Represent the media graph without materializing all its vertices."""

    def __init__(
        self,
        media,
        initial_vocabulary=None,
        comprehension_threshold=0.0,
    ):
        """Create a graph over media and an initial vocabulary state."""
        if not 0 <= comprehension_threshold <= 1:
            raise ValueError("comprehension_threshold must be between 0 and 1")

        self.media = tuple(media)
        self.initial_vocabulary = (
            deepcopy(initial_vocabulary)
            if initial_vocabulary is not None
            else LearnerVocabulary()
        )
        self.comprehension_threshold = comprehension_threshold

    def initial_vertex(self):
        """Return the graph's starting vertex before any media is consumed."""
        return Vertex(None, deepcopy(self.initial_vocabulary))

    def successors(self, vertex):
        """Generate edges for media understandable from the given vertex."""
        for candidate in self.media:
            if candidate is vertex.media:
                continue
            if (
                vertex.vocabulary.know_percentage(candidate)
                < self.comprehension_threshold
            ):
                continue

            vocabulary = deepcopy(vertex.vocabulary)
            vocabulary.account_for_media(candidate)
            yield Edge(
                target=Vertex(candidate, vocabulary),
                cost=sum(candidate.word_group_occurrences.values()),
            )