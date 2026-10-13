"""Seeded traffic disruption and scenario comparison services."""

from __future__ import annotations

import random
import time
from typing import Any

from algorithms.graph import build_adjacency
from algorithms.knapsack import allocate_passengers
from algorithms.shortest_paths import dijkstra
from algorithms.vehicle_routing import clarke_wright_routes


def create_disrupted_roads(
    roads: list[dict[str, Any]],
    max_increase_percent: float,
    disabled_road_ids: set[str],
    random_closure_percent: float,
    seed: int,
) -> tuple[list[dict[str, Any]], set[str]]:
    """Apply deterministic random delays and optional random closures."""
    if max_increase_percent < 0:
        raise ValueError("Travel-time increase cannot be negative.")
    if not 0 <= random_closure_percent <= 100:
        raise ValueError("Random closure percentage must be between 0 and 100.")
    rng = random.Random(seed)
    selected_closures = set(disabled_road_ids)
    remaining = [road for road in roads if str(road["road_id"]) not in selected_closures]
    closure_count = round(len(roads) * random_closure_percent / 100)
    if closure_count:
        selected_closures.update(
            str(road["road_id"])
            for road in rng.sample(remaining, min(closure_count, len(remaining)))
        )
    disrupted: list[dict[str, Any]] = []
    for road in roads:
        copied = dict(road)
        road_id = str(road["road_id"])
        if road_id not in selected_closures and max_increase_percent:
            multiplier = 1 + rng.uniform(0, max_increase_percent / 100)
            copied["travel_time"] = round(float(road["travel_time"]) * multiplier, 3)
        disrupted.append(copied)
    return disrupted, selected_closures


def evaluate_scenario(
    stops: list[dict[str, Any]],
    roads: list[dict[str, Any]],
    requests: list[dict[str, Any]],
    fleet: list[dict[str, Any]],
    disabled_road_ids: set[str] | None = None,
) -> dict[str, Any]:
    """Run the routing heuristic and calculate measured service metrics."""
    start = time.perf_counter()
    active_roads = [
        road
        for road in roads
        if str(road["road_id"]) not in (disabled_road_ids or set())
    ]
    routing = clarke_wright_routes(stops, active_roads, requests, fleet)
    adjacency = build_adjacency(stops, roads, disabled_road_ids)
    served = set(routing["served_request_ids"])
    served_requests = [request for request in requests if request["request_id"] in served]
    largest_vehicle_capacity = max(
        (int(vehicle["capacity"]) for vehicle in fleet),
        default=0,
    )
    allocation = allocate_passengers(served_requests, largest_vehicle_capacity)
    journey_times: list[float] = []
    for request in served_requests:
        distances, _parents = dijkstra(adjacency, str(request["pickup_stop"]))
        value = distances.get(str(request["destination_stop"]), float("inf"))
        if value < float("inf"):
            journey_times.append(value)
    elapsed_ms = (time.perf_counter() - start) * 1000
    passengers = sum(int(request["passengers"]) for request in served_requests)
    active_routes = routing["routes"]
    capacity = sum(int(route["capacity"]) for route in active_routes)
    return {
        "requests_total": len(requests),
        "requests_served": len(served_requests),
        "request_service_percent": len(served_requests) / len(requests) * 100 if requests else 0.0,
        "passengers_served": passengers,
        "knapsack_passengers_served": allocation["passengers_served"],
        "knapsack_request_ids": [
            str(request["request_id"]) for request in allocation["selected"]
        ],
        "knapsack_capacity": largest_vehicle_capacity,
        "average_journey_minutes": sum(journey_times) / len(journey_times) if journey_times else 0.0,
        "average_delay_minutes": 0.0,
        "capacity_utilization_percent": passengers / capacity * 100 if capacity else 0.0,
        "unserved_requests": routing["unserved"],
        "runtime_ms": elapsed_ms,
        "disrupted_road_percent": 0.0,
        "routing": routing,
        "knapsack_allocation": allocation,
        "journey_times": {
            str(request["request_id"]): time
            for request, time in zip(served_requests, journey_times)
        },
    }


def compare_scenarios(
    dataset: dict[str, list[dict[str, Any]]],
    max_increase_percent: float,
    disabled_road_ids: set[str],
    random_closure_percent: float,
    seed: int,
) -> dict[str, Any]:
    """Compare baseline and seeded disrupted route plans on the same demand."""
    baseline = evaluate_scenario(**dataset)
    altered_roads, all_disabled = create_disrupted_roads(
        dataset["roads"],
        max_increase_percent,
        disabled_road_ids,
        random_closure_percent,
        seed,
    )
    disrupted = evaluate_scenario(
        dataset["stops"],
        altered_roads,
        dataset["requests"],
        dataset["fleet"],
        all_disabled,
    )
    before = baseline["journey_times"]
    after = disrupted["journey_times"]
    common_ids = set(before) & set(after)
    disrupted["average_delay_minutes"] = (
        sum(max(0.0, after[request_id] - before[request_id]) for request_id in common_ids)
        / len(common_ids)
        if common_ids
        else 0.0
    )
    disrupted["disrupted_road_percent"] = (
        len(all_disabled | {
            str(road["road_id"])
            for original, road in zip(dataset["roads"], altered_roads)
            if float(road["travel_time"]) > float(original["travel_time"])
        })
        / len(dataset["roads"]) * 100
        if dataset["roads"]
        else 0.0
    )
    return {
        "baseline": baseline,
        "disrupted": disrupted,
        "disabled_road_ids": sorted(all_disabled),
        "seed": seed,
        "simulated": True,
    }
