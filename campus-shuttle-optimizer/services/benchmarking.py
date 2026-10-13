"""Reproducible, measured experiment runners for the dashboard."""

from __future__ import annotations

import random
import time
from statistics import mean
from typing import Any

from algorithms.all_pairs import floyd_warshall
from algorithms.graph import build_adjacency
from algorithms.greedy_scheduling import activity_selection
from algorithms.knapsack import allocate_passengers
from algorithms.mst import kruskal_mst, prim_mst
from algorithms.shortest_paths import bellman_ford, dijkstra
from algorithms.vehicle_routing import clarke_wright_routes


def _random_graph(size: int, density: float, seed: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rng = random.Random(seed + size)
    stops = [
        {"stop_id": f"N{node:03}", "name": f"Node {node}", "x": node, "y": rng.random(), "is_depot": node == 0}
        for node in range(size)
    ]
    roads = []
    for node in range(size - 1):
        roads.append(
            {
                "road_id": f"E{len(roads):04}",
                "from_stop": f"N{node:03}",
                "to_stop": f"N{node + 1:03}",
                "travel_time": rng.randint(1, 20),
                "directed": False,
            }
        )
    for left in range(size):
        for right in range(left + 2, size):
            if rng.random() < density:
                roads.append(
                    {
                        "road_id": f"E{len(roads):04}",
                        "from_stop": f"N{left:03}",
                        "to_stop": f"N{right:03}",
                        "travel_time": rng.randint(1, 20),
                        "directed": False,
                    }
                )
    return stops, roads


def run_graph_benchmarks(
    graph_sizes: list[int],
    density: float = 0.12,
    trials: int = 3,
    seed: int = 2026,
) -> list[dict[str, Any]]:
    """Compare MST, SSSP, repeated Dijkstra, and Floyd-Warshall runtimes."""
    results: list[dict[str, Any]] = []
    for size in graph_sizes:
        stops, roads = _random_graph(size, density, seed)
        adjacency = build_adjacency(stops, roads)
        measurements: dict[str, list[float]] = {
            "Prim": [], "Kruskal": [], "Dijkstra": [], "Bellman-Ford": [],
            "Repeated Dijkstra": [], "Floyd-Warshall": [],
        }
        for _trial in range(max(1, trials)):
            for name, function in (
                ("Prim", lambda: prim_mst(stops, roads)),
                ("Kruskal", lambda: kruskal_mst(stops, roads)),
                ("Dijkstra", lambda: dijkstra(adjacency, "N000")),
                ("Bellman-Ford", lambda: bellman_ford(adjacency, "N000")),
                ("Repeated Dijkstra", lambda: [dijkstra(adjacency, node) for node in adjacency]),
                ("Floyd-Warshall", lambda: floyd_warshall(adjacency)),
            ):
                start = time.perf_counter()
                function()
                measurements[name].append((time.perf_counter() - start) * 1000)
        edge_count = len(roads)
        for algorithm, runtimes in measurements.items():
            results.append(
                {
                    "graph_size": size,
                    "edges": edge_count,
                    "density": density,
                    "algorithm": algorithm,
                    "runtime_ms": mean(runtimes),
                    "trials": max(1, trials),
                }
            )
    return results


def run_demand_benchmarks(
    requests: list[dict[str, Any]],
    fleet: list[dict[str, Any]],
    capacities: list[int],
) -> list[dict[str, Any]]:
    """Measure knapsack quality and runtime at varying seat capacities."""
    output = []
    for capacity in capacities:
        start = time.perf_counter()
        result = allocate_passengers(requests, capacity)
        runtime = (time.perf_counter() - start) * 1000
        output.append(
            {
                "capacity": capacity,
                "request_count": len(requests),
                "passengers_served": result["passengers_served"],
                "service_value": result["service_value"],
                "utilization_percent": result["utilization"],
                "runtime_ms": runtime,
            }
        )
    return output


def run_scheduling_benchmark(requests: list[dict[str, Any]]) -> dict[str, Any]:
    """Return an actual activity-selection result and its elapsed time."""
    start = time.perf_counter()
    result = activity_selection(requests)
    return {
        "runtime_ms": (time.perf_counter() - start) * 1000,
        "scheduled_count": len(result["scheduled"]),
        "rejected_count": len(result["rejected"]),
        "result": result,
    }


def run_routing_benchmark(dataset: dict[str, list[dict[str, Any]]], fleet_sizes: list[int]) -> list[dict[str, Any]]:
    """Measure heuristic route construction under different fleet sizes."""
    results = []
    for count in fleet_sizes:
        fleet = dataset["fleet"][:count]
        start = time.perf_counter()
        routes = clarke_wright_routes(
            dataset["stops"], dataset["roads"], dataset["requests"], fleet
        )
        elapsed = (time.perf_counter() - start) * 1000
        results.append(
            {
                "fleet_size": count,
                "requests_served": len(routes["served_request_ids"]),
                "total_route_time": routes["total_time"],
                "runtime_ms": elapsed,
            }
        )
    return results
