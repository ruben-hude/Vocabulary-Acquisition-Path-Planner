"""Shortest-path search over the implicit media graph."""

from dataclasses import dataclass
import heapq
import itertools
import time

from vocabulary_acquisition_path_planner.search.graph import Graph, Vertex


@dataclass(frozen=True)
class PathResult:
    """A path found through the media graph."""

    media: tuple
    cost: int


class PathFinder:
    """Find minimum-cost paths with Dijkstra's algorithm."""

    def __init__(self, graph):
        """Create a path finder for an implicit graph."""
        self.graph = graph

    def find_path(self, target_media, time_limit_seconds=None):
        """Return the least-cost path to target media.

        Raise ``ValueError`` when the target is not part of the graph and
        ``LookupError`` when no path exists. Raise ``TimeoutError`` when the
        optional time limit expires before a path is found.
        """
        if target_media not in self.graph.media:
            raise ValueError("target_media must be part of the graph")
        if (
            time_limit_seconds is not None
            and time_limit_seconds < 0
        ):
            raise ValueError("time_limit_seconds must not be negative")

        deadline = None
        if time_limit_seconds is not None:
            deadline = time.monotonic() + time_limit_seconds

        initial_vertex = self.graph.initial_vertex()
        queue = [(0, next(self._counter), initial_vertex)]
        distances = {self._state_key(initial_vertex): 0}
        parents = {}

        while queue:
            self._raise_if_timed_out(deadline)
            cost, _, vertex = heapq.heappop(queue)
            state_key = self._state_key(vertex)
            if cost != distances.get(state_key):
                continue

            if vertex.media is target_media:
                return self._build_result(vertex, cost, parents)

            for edge in self.graph.successors(vertex):
                self._raise_if_timed_out(deadline)
                next_vertex = edge.target
                next_cost = cost + edge.cost
                next_key = self._state_key(next_vertex)
                if next_cost >= distances.get(next_key, float("inf")):
                    continue

                distances[next_key] = next_cost
                parents[next_key] = (state_key, vertex)
                heapq.heappush(
                    queue,
                    (next_cost, next(self._counter), next_vertex),
                )

        raise LookupError("no path to target_media exists")

    def _build_result(self, vertex, cost, parents):
        """Reconstruct a path from parent links."""
        path = []
        state_key = self._state_key(vertex)
        while vertex.media is not None:
            path.append(vertex.media)
            parent = parents.get(state_key)
            if parent is None:
                break
            state_key, vertex = parent

        path.reverse()
        return PathResult(tuple(path), cost)

    @staticmethod
    def _raise_if_timed_out(deadline):
        if deadline is not None and time.monotonic() >= deadline:
            raise TimeoutError("path search exceeded its time limit")

    _counter = itertools.count()

    @staticmethod
    def _state_key(vertex):
        """Return a hashable key for a media and vocabulary state."""
        vocabulary = vertex.vocabulary
        return (
            id(vertex.media),
            frozenset(vocabulary.known_words),
            frozenset(vocabulary.word_exposures.items()),
        )
