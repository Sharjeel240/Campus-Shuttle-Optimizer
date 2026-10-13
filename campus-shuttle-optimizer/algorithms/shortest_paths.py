"""Manual single-source shortest-path algorithms."""

from __future__ import annotations

import heapq
from math import inf

from algorithms.graph import Adjacency, adjacency_to_arcs


class NegativeCycleError(ValueError):
    """Raised when Bellman-Ford can reach a negative-weight cycle."""


def dijkstra(adjacency: Adjacency, source: str) -> tuple[dict[str, float], dict[str, str | None]]:
    """Dijkstra's algorithm with a binary min-heap; rejects negative weights."""
    if source not in adjacency:
        raise ValueError(f"Unknown source stop: {source}")
    if any(weight < 0 for neighbors in adjacency.values() for _node, weight in neighbors):
        raise ValueError("Dijkstra's algorithm cannot run with negative edge weights.")

    distances = {node: inf for node in adjacency}
    parents: dict[str, str | None] = {node: None for node in adjacency}
    distances[source] = 0.0
    queue: list[tuple[float, str]] = [(0.0, source)]
    while queue:
        current_distance, current = heapq.heappop(queue)
        if current_distance != distances[current]:
            continue
        for neighbor, weight in adjacency[current]:
            candidate = current_distance + weight
            if candidate < distances[neighbor]:
                distances[neighbor] = candidate
                parents[neighbor] = current
                heapq.heappush(queue, (candidate, neighbor))
    return distances, parents


def bellman_ford(
    adjacency: Adjacency,
    source: str,
) -> tuple[dict[str, float], dict[str, str | None]]:
    """Bellman-Ford with detection of negative cycles reachable from source."""
    if source not in adjacency:
        raise ValueError(f"Unknown source stop: {source}")
    arcs = adjacency_to_arcs(adjacency)
    distances = {node: inf for node in adjacency}
    parents: dict[str, str | None] = {node: None for node in adjacency}
    distances[source] = 0.0
    for _ in range(max(0, len(adjacency) - 1)):
        changed = False
        for start, end, weight in arcs:
            if distances[start] != inf and distances[start] + weight < distances[end]:
                distances[end] = distances[start] + weight
                parents[end] = start
                changed = True
        if not changed:
            break
    for start, end, weight in arcs:
        if distances[start] != inf and distances[start] + weight < distances[end]:
            raise NegativeCycleError("A negative-weight cycle is reachable from the selected source.")
    return distances, parents


def reconstruct_path(
    parents: dict[str, str | None],
    source: str,
    destination: str,
) -> list[str]:
    """Reconstruct a path, or return an empty list when it is unreachable."""
    if destination not in parents:
        return []
    path: list[str] = []
    current: str | None = destination
    seen: set[str] = set()
    while current is not None:
        if current in seen:
            return []
        seen.add(current)
        path.append(current)
        if current == source:
            path.reverse()
            return path
        current = parents[current]
    return []
