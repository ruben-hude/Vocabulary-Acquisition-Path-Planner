"""Tests for Dijkstra path finding."""

import pytest

from vocabulary_acquisition_path_planner.models.media import Media
from vocabulary_acquisition_path_planner.search.graph import Graph
from vocabulary_acquisition_path_planner.search.path_finder import PathFinder


def test_path_finder_returns_the_lowest_cost_path():
    first = Media({"play": 1})
    expensive = Media({"play": 1, "read": 10})
    target = Media({"play": 1})
    graph = Graph([first, expensive, target])

    result = PathFinder(graph).find_path(target)

    assert result.media == (target,)
    assert result.cost == 1


def test_path_finder_can_reach_target_after_an_intermediate_media():
    first = Media({"play": 1})
    target = Media({"play": 1, "read": 1})
    graph = Graph([first, target])

    result = PathFinder(graph).find_path(target)

    assert result.media == (target,)
    assert result.cost == 2


def test_path_finder_respects_time_limit():
    graph = Graph([Media({"play": 1})])
    finder = PathFinder(graph)

    with pytest.raises(TimeoutError, match="time limit"):
        finder.find_path(graph.media[0], time_limit_seconds=0)
