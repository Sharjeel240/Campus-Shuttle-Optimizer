"""Manual Floyd-Warshall all-pairs shortest paths."""

from __future__ import annotations

from math import inf

from algorithms.graph import Adjacency


def floyd_warshall(
    adjacency: Adjacency,
) -> tuple[list[str], list[list[float]], list[list[str | None]]]:
    """Return node order, shortest-distance matrix, and next-hop matrix."""
    nodes = sorted(adjacency)
    index = {node: position for position, node in enumerate(nodes)}
    size = len(nodes)
    distances = [[inf] * size for _ in range(size)]
    next_hop: list[list[str | None]] = [[None] * size for _ in range(size)]
    for position, node in enumerate(nodes):
        distances[position][position] = 0.0
        next_hop[position][position] = node
    for start, neighbors in adjacency.items():
        for end, weight in neighbors:
            i, j = index[start], index[end]
            if weight < distances[i][j]:
                distances[i][j] = weight
                next_hop[i][j] = end

    for middle in range(size):
        for start in range(size):
            if distances[start][middle] == inf:
                continue
            for end in range(size):
                candidate = distances[start][middle] + distances[middle][end]
                if candidate < distances[start][end]:
                    distances[start][end] = candidate
                    next_hop[start][end] = next_hop[start][middle]

    if any(distances[node][node] < 0 for node in range(size)):
        raise ValueError("Floyd-Warshall detected a negative-weight cycle.")
    return nodes, distances, next_hop


def reconstruct_all_pairs_path(
    nodes: list[str],
    next_hop: list[list[str | None]],
    source: str,
    destination: str,
) -> list[str]:
    """Reconstruct a path from Floyd-Warshall's next-hop matrix."""
    index = {node: position for position, node in enumerate(nodes)}
    if source not in index or destination not in index:
        return []
    current = next_hop[index[source]][index[destination]]
    if current is None:
        return []
    path = [source]
    for _ in range(len(nodes) + 1):
        if path[-1] == destination:
            return path
        current = next_hop[index[path[-1]]][index[destination]]
        if current is None:
            return []
        path.append(current)
    return []
