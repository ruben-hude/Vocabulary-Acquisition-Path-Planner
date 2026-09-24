# Vocabulary Acquisition Path Planner

An experimental project for finding an efficient reading path to help language
learners acquire vocabulary progressively.

## Overview

The project aims to recommend a sequence of media, such as short stories,
articles, or books, whose vocabulary becomes increasingly accessible as the
learner progresses.

The central idea is to model each step as a combination of:

- a piece of media;
- the learner's current vocabulary;
- the vocabulary required to understand the next piece of media.

The planner should then find a path from a learner's starting vocabulary to a
target level/media while taking the cost of each piece of media into account.

## Problem Model

### Word groups

Words should be grouped by their grammatical or morphological relationships.
For example, *play*, *player*, and *playing* should not necessarily be treated
as completely independent learning goals. We can even treat them as the same 
learning goal.

### Media representation

Each piece of media may be represented by:

- the words or word groups it contains and their number of occurences;
- its reading or exposure cost;
- potentially, additional information such as length or genre (not planned).

The cost model should reflect the learner's effort. For example, reading five
short stories may be preferable to reading three very long books, even if both
options expose the learner to a similar amount of vocabulary.

### Learner vocabulary

The learner's known vocabulary should be represented by a lightweight,
incrementally updatable structure. Because path-search algorithms may explore
and backtrack frequently, the implementation should eventually support
efficiently applying and undoing temporary vocabulary updates.

The vocabulary representation should also provide a way to compare a text with
the learner's current knowledge and estimate how understandable that text is.

## Path Search

The intended graph is implicit rather than explicitly materialized:

- a vertex represents a pair `(media, vocabulary state)`;
- an edge connects two vertices when the media items are different and the
  current vocabulary makes the next item sufficiently understandable;
- the edge cost represents the effort required to complete the next item.

An initial implementation could use Dijkstra's algorithm to establish a
baseline. A* or another informed search algorithm may be considered later if a
useful heuristic can be defined.

Because the graph and vocabulary state may become large, approximate or
recursive approaches may also be useful. The project should avoid assuming
that the problem always satisfies the conditions required for a straightforward
shortest-path solution.

## Open Questions

- How should comprehension be estimated from vocabulary coverage?
- How should related word forms be grouped?
- Should media cost depend on length, difficulty, or both?
- Should the planner optimize reading time, number of media items, vocabulary
  acquisition, or a weighted combination?
- Would a mixed-integer linear programming formulation be useful?
- Can a practical heuristic be found for A*?
- How should the user interface present and adjust a recommended path?

## Roadmap

1. Define the data model for word groups, media, and learner vocabulary.
2. Implement text comparison and vocabulary coverage metrics.
3. Build an implicit graph representation.
4. Implement a baseline path search, starting with Dijkstra's algorithm.
5. Add realistic media-cost and comprehension models.
6. Evaluate heuristic and approximate search methods.
7. Design a user interface for creating, inspecting, and adapting learning
   paths.
