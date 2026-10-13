"""Capacity-safe Clarke-Wright savings heuristic for multiple shuttle vehicles."""

from __future__ import annotations

from typing import Any

from algorithms.all_pairs import floyd_warshall, reconstruct_all_pairs_path
from algorithms.graph import Adjacency, build_adjacency


def clarke_wright_routes(
    stops: list[dict[str, Any]],
    roads: list[dict[str, Any]],
    requests: list[dict[str, Any]],
    fleet: list[dict[str, Any]],
) -> dict[str, Any]:
    """Construct depot-return routes by repeatedly taking feasible savings merges.

    Passenger groups are treated conservatively as consuming their full seat
    count for the route. This can reject merges that sequential trip turnover
    could make feasible, but never overbooks a proposed route.
    """
    if not fleet:
        return {"routes": [], "unserved": requests[:], "served_request_ids": [], "total_time": 0.0}
    if any(int(vehicle["capacity"]) <= 0 for vehicle in fleet):
        raise ValueError("Every vehicle must have positive capacity.")

    adjacency = build_adjacency(stops, roads)
    nodes, distances, next_hop = floyd_warshall(adjacency)
    node_index = {node: index for index, node in enumerate(nodes)}
    depots = sorted({
        str(vehicle["depot_id"])
        for vehicle in fleet
        if str(vehicle["depot_id"]) in node_index
    })
    by_depot = {
        depot: [vehicle for vehicle in fleet if str(vehicle["depot_id"]) == depot]
        for depot in depots
    }
    max_capacity = {
        depot: max(int(vehicle["capacity"]) for vehicle in vehicles)
        for depot, vehicles in by_depot.items()
    }

    def distance(start: str, end: str) -> float:
        if start not in node_index or end not in node_index:
            return float("inf")
        return distances[node_index[start]][node_index[end]]

    priorities = {str(request["request_id"]): float(request["priority"]) for request in requests}
    demand = {str(request["request_id"]): int(request["passengers"]) for request in requests}
    request_by_id = {str(request["request_id"]): request for request in requests}
    routes_by_depot: dict[str, list[dict[str, Any]]] = {depot: [] for depot in depots}
    unserved_ids: set[str] = set()

    for request in requests:
        request_id = str(request["request_id"])
        pickup = str(request["pickup_stop"])
        destination = str(request["destination_stop"])
        candidates = [
            (distance(depot, pickup) + distance(pickup, destination) + distance(destination, depot), depot)
            for depot in depots
            if distance(depot, pickup) < float("inf")
            and distance(pickup, destination) < float("inf")
            and distance(destination, depot) < float("inf")
            and int(request["passengers"]) <= max_capacity[depot]
        ]
        if not candidates:
            unserved_ids.add(request_id)
            continue
        _cost, chosen_depot = min(candidates)
        routes_by_depot[chosen_depot].append(
            {
                "depot_id": chosen_depot,
                "request_ids": [request_id],
                "passengers": demand[request_id],
                "priority": priorities[request_id],
            }
        )

    merged_routes: list[dict[str, Any]] = []
    for depot, routes in routes_by_depot.items():
        # Keep choosing the best saving while there is room to merge routes
        # or the available vehicle count requires fewer routes.
        while len(routes) > 1:
            must_reduce_count = len(routes) > len(by_depot[depot])
            best: tuple[float, int, int] | None = None
            for left_index, left in enumerate(routes):
                left_last = request_by_id[left["request_ids"][-1]]
                for right_index, right in enumerate(routes):
                    if left_index == right_index:
                        continue
                    if left["passengers"] + right["passengers"] > max_capacity[depot]:
                        continue
                    right_first = request_by_id[right["request_ids"][0]]
                    left_end = str(left_last["destination_stop"])
                    right_start = str(right_first["pickup_stop"])
                    if distance(left_end, right_start) == float("inf"):
                        continue
                    saving = (
                        distance(left_end, depot)
                        + distance(depot, right_start)
                        - distance(left_end, right_start)
                    )
                    if not must_reduce_count and saving <= 0:
                        continue
                    if best is None or saving > best[0]:
                        best = (saving, left_index, right_index)
            if best is None:
                break
            _saving, left_index, right_index = best
            left = routes[left_index]
            right = routes[right_index]
            merged = {
                "depot_id": depot,
                "request_ids": left["request_ids"] + right["request_ids"],
                "passengers": left["passengers"] + right["passengers"],
                "priority": left["priority"] + right["priority"],
            }
            routes = [
                route
                for index, route in enumerate(routes)
                if index not in (left_index, right_index)
            ]
            routes.append(merged)
        merged_routes.extend(routes)

    assigned: list[dict[str, Any]] = []
    vehicles_by_depot = {
        depot: sorted(vehicles, key=lambda vehicle: int(vehicle["capacity"]))
        for depot, vehicles in by_depot.items()
    }
    for depot in depots:
        candidates = [
            route for route in merged_routes if route["depot_id"] == depot
        ]
        candidates.sort(key=lambda route: (route["priority"], route["passengers"]), reverse=True)
        available = vehicles_by_depot[depot][:]
        for route in candidates:
            suitable = [
                vehicle
                for vehicle in available
                if int(vehicle["capacity"]) >= route["passengers"]
            ]
            if not suitable:
                unserved_ids.update(route["request_ids"])
                continue
            vehicle = suitable[0]
            available.remove(vehicle)
            assigned.append({**route, "vehicle_id": str(vehicle["vehicle_id"]), "capacity": int(vehicle["capacity"])})

    output_routes: list[dict[str, Any]] = []
    served_ids: set[str] = set()
    for route in assigned:
        depot = route["depot_id"]
        sequence = [depot]
        total_time = 0.0
        current = depot
        valid = True
        for request_id in route["request_ids"]:
            request = request_by_id[request_id]
            for target in (str(request["pickup_stop"]), str(request["destination_stop"])):
                segment = reconstruct_all_pairs_path(nodes, next_hop, current, target)
                if not segment:
                    valid = False
                    break
                if len(segment) > 1:
                    sequence.extend(segment[1:])
                total_time += distance(current, target)
                current = target
            if not valid:
                break
        if valid:
            return_segment = reconstruct_all_pairs_path(nodes, next_hop, current, depot)
            if not return_segment:
                valid = False
            else:
                if len(return_segment) > 1:
                    sequence.extend(return_segment[1:])
                total_time += distance(current, depot)
        if not valid:
            unserved_ids.update(route["request_ids"])
            continue
        served_ids.update(route["request_ids"])
        output_routes.append(
            {
                **route,
                "stop_sequence": sequence,
                "total_time": total_time,
                "utilization": route["passengers"] / route["capacity"] * 100,
                "requests": [request_by_id[request_id] for request_id in route["request_ids"]],
            }
        )

    unserved = [
        request for request in requests
        if str(request["request_id"]) in (unserved_ids | (set(request_by_id) - served_ids))
    ]
    # The set expression above also accounts for any request omitted after a
    # route assignment issue, while the list preserves original input order.
    return {
        "routes": output_routes,
        "unserved": unserved,
        "served_request_ids": sorted(served_ids),
        "total_time": sum(route["total_time"] for route in output_routes),
        "adjacency": adjacency,
    }
