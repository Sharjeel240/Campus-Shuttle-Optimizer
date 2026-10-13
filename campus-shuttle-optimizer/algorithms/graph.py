"""Weighted adjacency-list graph utilities for campus road networks."""

from __future__ import annotations

from collections import defaultdict
from math import isfinite
from typing import Any, Iterable

import networkx as nx

Road = dict[str, Any]
Adjacency = dict[str, list[tuple[str, float]]]


def build_adjacency(
    stops: Iterable[dict[str, Any]],
    roads: Iterable[Road],
    disabled_road_ids: set[str] | None = None,
    weight_multiplier: dict[str, float] | None = None,
    allow_negative: bool = False,
) -> Adjacency:
    """Build an adjacency list, respecting each road's direction flag."""
    stop_ids = {str(stop["stop_id"]) for stop in stops}
    disabled = disabled_road_ids or set()
    multipliers = weight_multiplier or {}
    adjacency: Adjacency = {stop_id: [] for stop_id in stop_ids}

    for road in roads:
        road_id = str(road["road_id"])
        if road_id in disabled:
            continue
        start = str(road["from_stop"])
        end = str(road["to_stop"])
        if start not in stop_ids or end not in stop_ids:
            raise ValueError(f"Road {road_id} references a missing stop.")
        weight = float(road["travel_time"]) * float(multipliers.get(road_id, 1.0))
        if not isfinite(weight):
            raise ValueError(f"Road {road_id} must have a finite travel time.")
        if not allow_negative and weight < 0:
            raise ValueError(f"Road {road_id} has a negative travel time.")
        adjacency[start].append((end, weight))
        if not bool(road.get("directed", False)):
            adjacency[end].append((start, weight))
    return adjacency


def adjacency_to_arcs(adjacency: Adjacency) -> list[tuple[str, str, float]]:
    """Return a flat list of directed arcs from an adjacency list."""
    return [
        (start, end, float(weight))
        for start, neighbors in adjacency.items()
        for end, weight in neighbors
    ]


def to_networkx(
    stops: Iterable[dict[str, Any]],
    roads: Iterable[Road],
) -> nx.MultiDiGraph:
    """Create a NetworkX representation for inspection and validation only."""
    graph = nx.MultiDiGraph()
    for stop in stops:
        graph.add_node(
            str(stop["stop_id"]),
            name=str(stop["name"]),
            x=float(stop["x"]),
            y=float(stop["y"]),
            is_depot=bool(stop["is_depot"]),
        )
    for road in roads:
        start = str(road["from_stop"])
        end = str(road["to_stop"])
        attrs = {
            "road_id": str(road["road_id"]),
            "travel_time": float(road["travel_time"]),
            "directed": bool(road.get("directed", False)),
        }
        graph.add_edge(start, end, **attrs)
        if not attrs["directed"]:
            graph.add_edge(end, start, **attrs)
    return graph


def connected_components(adjacency: Adjacency) -> list[set[str]]:
    """Find connected components using a manual traversal."""
    undirected: dict[str, set[str]] = defaultdict(set)
    for start, neighbors in adjacency.items():
        for end, _weight in neighbors:
            undirected[start].add(end)
            undirected[end].add(start)

    remaining = set(adjacency)
    components: list[set[str]] = []
    while remaining:
        seed = remaining.pop()
        component = {seed}
        stack = [seed]
        while stack:
            current = stack.pop()
            for neighbor in undirected[current]:
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        components.append(component)
    return components


def validate_undirected(roads: Iterable[Road]) -> None:
    """MST algorithms require an undirected graph."""
    if any(bool(road.get("directed", False)) for road in roads):
        raise ValueError("Minimum spanning trees require every road to be undirected.")
