"""Prim and Kruskal minimum spanning forest implementations."""

from __future__ import annotations

import heapq
from typing import Any, Iterable

from algorithms.graph import Adjacency, validate_undirected


def _undirected_edges(roads: Iterable[dict[str, Any]]) -> list[tuple[str, str, float]]:
    road_list = list(roads)
    validate_undirected(road_list)
    return [
        (str(road["from_stop"]), str(road["to_stop"]), float(road["travel_time"]))
        for road in road_list
    ]


def prim_mst(
    stops: Iterable[dict[str, Any]],
    roads: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Return a minimum spanning forest using a binary heap."""
    stop_ids = sorted(str(stop["stop_id"]) for stop in stops)
    edges = _undirected_edges(roads)
    adjacency: Adjacency = {stop_id: [] for stop_id in stop_ids}
    for start, end, weight in edges:
        adjacency[start].append((end, weight))
        adjacency[end].append((start, weight))

    visited: set[str] = set()
    selected: list[dict[str, Any]] = []
    component_count = 0
    for seed in stop_ids:
        if seed in visited:
            continue
        component_count += 1
        visited.add(seed)
        candidates: list[tuple[float, str, str]] = []
        for neighbor, weight in adjacency[seed]:
            heapq.heappush(candidates, (weight, seed, neighbor))
        while candidates:
            weight, start, end = heapq.heappop(candidates)
            if end in visited:
                continue
            visited.add(end)
            selected.append({"from_stop": start, "to_stop": end, "travel_time": weight})
            for neighbor, next_weight in adjacency[end]:
                if neighbor not in visited:
                    heapq.heappush(candidates, (next_weight, end, neighbor))
    return {
        "edges": selected,
        "total_weight": sum(edge["travel_time"] for edge in selected),
        "components": component_count,
    }


class DisjointSet:
    """Disjoint-set union with path compression and union by rank."""

    def __init__(self, items: Iterable[str]) -> None:
        self.parent = {item: item for item in items}
        self.rank = {item: 0 for item in items}

    def find(self, item: str) -> str:
        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])
        return self.parent[item]

    def union(self, left: str, right: str) -> bool:
        root_left = self.find(left)
        root_right = self.find(right)
        if root_left == root_right:
            return False
        if self.rank[root_left] < self.rank[root_right]:
            root_left, root_right = root_right, root_left
        self.parent[root_right] = root_left
        if self.rank[root_left] == self.rank[root_right]:
            self.rank[root_left] += 1
        return True


def kruskal_mst(
    stops: Iterable[dict[str, Any]],
    roads: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Return a minimum spanning forest using sorting and a disjoint-set union."""
    stop_ids = sorted(str(stop["stop_id"]) for stop in stops)
    edges = _undirected_edges(roads)
    disjoint_set = DisjointSet(stop_ids)
    selected: list[dict[str, Any]] = []
    for start, end, weight in sorted(edges, key=lambda edge: edge[2]):
        if disjoint_set.union(start, end):
            selected.append({"from_stop": start, "to_stop": end, "travel_time": weight})
    roots = {disjoint_set.find(stop_id) for stop_id in stop_ids}
    return {
        "edges": selected,
        "total_weight": sum(edge["travel_time"] for edge in selected),
        "components": len(roots),
    }
