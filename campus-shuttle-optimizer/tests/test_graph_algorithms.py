from math import inf

import pytest

from algorithms.all_pairs import floyd_warshall, reconstruct_all_pairs_path
from algorithms.graph import build_adjacency
from algorithms.mst import kruskal_mst, prim_mst
from algorithms.shortest_paths import (
    NegativeCycleError,
    bellman_ford,
    dijkstra,
    reconstruct_path,
)


def sample_graph():
    stops = [{"stop_id": node, "name": node, "x": 0, "y": 0, "is_depot": node == "A"} for node in "ABCD"]
    roads = [
        {"road_id": "e1", "from_stop": "A", "to_stop": "B", "travel_time": 2, "directed": False},
        {"road_id": "e2", "from_stop": "B", "to_stop": "C", "travel_time": 3, "directed": False},
        {"road_id": "e3", "from_stop": "A", "to_stop": "C", "travel_time": 8, "directed": False},
    ]
    return stops, roads


def test_prim_and_kruskal_return_same_spanning_forest_weight():
    stops, roads = sample_graph()
    prim = prim_mst(stops, roads)
    kruskal = kruskal_mst(stops, roads)
    assert prim["total_weight"] == kruskal["total_weight"] == 5
    assert len(prim["edges"]) == len(kruskal["edges"]) == 2
    assert prim["components"] == kruskal["components"] == 2


def test_mst_rejects_directed_road():
    stops, roads = sample_graph()
    roads[0]["directed"] = True
    with pytest.raises(ValueError, match="undirected"):
        prim_mst(stops, roads)


def test_dijkstra_finds_shortest_path_and_rejects_negative_edges():
    stops, roads = sample_graph()
    adjacency = build_adjacency(stops, roads)
    distances, parents = dijkstra(adjacency, "A")
    assert distances["C"] == 5
    assert reconstruct_path(parents, "A", "C") == ["A", "B", "C"]
    adjacency["A"].append(("D", -1))
    with pytest.raises(ValueError, match="negative"):
        dijkstra(adjacency, "A")


def test_bellman_ford_handles_negative_edges_and_detects_reachable_cycle():
    adjacency = {
        "A": [("B", 4), ("C", 5)],
        "B": [("C", -6)],
        "C": [],
    }
    distances, parents = bellman_ford(adjacency, "A")
    assert distances["C"] == -2
    assert reconstruct_path(parents, "A", "C") == ["A", "B", "C"]
    adjacency["C"].append(("B", 1))
    with pytest.raises(NegativeCycleError):
        bellman_ford(adjacency, "A")


def test_floyd_warshall_reconstructs_path_and_keeps_unreachable_infinity():
    adjacency = {
        "A": [("B", 2)],
        "B": [("C", 3)],
        "C": [],
        "D": [],
    }
    nodes, distances, next_hop = floyd_warshall(adjacency)
    assert distances[nodes.index("A")][nodes.index("C")] == 5
    assert distances[nodes.index("A")][nodes.index("D")] == inf
    assert reconstruct_all_pairs_path(nodes, next_hop, "A", "C") == ["A", "B", "C"]
    assert reconstruct_all_pairs_path(nodes, next_hop, "A", "D") == []


def test_empty_and_disconnected_graph_are_supported():
    assert prim_mst([], []) == {"edges": [], "total_weight": 0, "components": 0}
    stops, roads = sample_graph()
    roads = roads[:1]
    forest = kruskal_mst(stops, roads)
    assert forest["components"] == 3
