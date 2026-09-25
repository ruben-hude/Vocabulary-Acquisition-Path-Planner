"""Tests for the implicit media graph."""

from vocabulary_acquisition_path_planner.models.learner_vocabulary import (
    LearnerVocabulary,
)
from vocabulary_acquisition_path_planner.models.media import Media
from vocabulary_acquisition_path_planner.search.graph import Graph, Vertex


def test_graph_generates_successors_with_updated_vocabulary():
    first = Media({"play": 1})
    second = Media({"play": 2, "read": 1})
    vocabulary = LearnerVocabulary(exposure_threshold=1)
    graph = Graph([first, second], vocabulary)

    edges = list(graph.successors(graph.initial_vertex()))

    assert [edge.target.media for edge in edges] == [first, second]
    assert edges[0].cost == 1
    assert edges[0].target.vocabulary.known_words == {"play"}
    assert edges[1].target.vocabulary.known_words == {"play", "read"}


def test_graph_filters_media_below_comprehension_threshold():
    first = Media({"play": 1})
    understandable = Media({"play": 3, "read": 1})
    difficult = Media({"play": 1, "read": 3})
    vocabulary = LearnerVocabulary(exposure_threshold=1)
    vocabulary.account_for_media(first)
    graph = Graph(
        [first, understandable, difficult],
        vocabulary,
        comprehension_threshold=0.5,
    )

    edges = list(graph.successors(graph.initial_vertex()))

    assert [edge.target.media for edge in edges] == [
        first,
        understandable,
    ]

    edges = list(graph.successors(Vertex(first, vocabulary)))
    assert [edge.target.media for edge in edges] == [understandable]


def test_graph_does_not_return_the_current_media_as_a_successor():
    media = Media({"play": 1})
    graph = Graph([media])
    vertex = Vertex(media, LearnerVocabulary())

    assert list(graph.successors(vertex)) == []
