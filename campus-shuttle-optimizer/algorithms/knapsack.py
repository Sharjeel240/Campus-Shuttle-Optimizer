"""0/1 passenger-group capacity allocation using dynamic programming."""

from __future__ import annotations

from typing import Any


def allocate_passengers(
    requests: list[dict[str, Any]],
    capacity: int,
) -> dict[str, Any]:
    """Maximize request priority without splitting passenger groups."""
    if capacity < 0:
        raise ValueError("Capacity cannot be negative.")
    if any(int(request["passengers"]) <= 0 for request in requests):
        raise ValueError("Every request must contain at least one passenger.")
    if any(float(request["priority"]) < 0 for request in requests):
        raise ValueError("Priority scores cannot be negative.")

    count = len(requests)
    table = [[0.0] * (capacity + 1) for _ in range(count + 1)]
    for row, request in enumerate(requests, start=1):
        weight = int(request["passengers"])
        value = float(request["priority"])
        for seats in range(capacity + 1):
            table[row][seats] = table[row - 1][seats]
            if weight <= seats:
                table[row][seats] = max(
                    table[row][seats],
                    table[row - 1][seats - weight] + value,
                )

    selected_indexes: list[int] = []
    remaining = capacity
    for row in range(count, 0, -1):
        if table[row][remaining] > table[row - 1][remaining]:
            selected_indexes.append(row - 1)
            remaining -= int(requests[row - 1]["passengers"])
    selected_indexes.reverse()
    selected_set = set(selected_indexes)
    selected = [requests[index] for index in selected_indexes]
    rejected = [request for index, request in enumerate(requests) if index not in selected_set]
    passengers = sum(int(request["passengers"]) for request in selected)
    value = sum(float(request["priority"]) for request in selected)
    return {
        "selected": selected,
        "rejected": rejected,
        "passengers_served": passengers,
        "remaining_seats": capacity - passengers,
        "service_value": value,
        "utilization": (passengers / capacity * 100) if capacity else 0.0,
        "table": table,
        "selected_indexes": selected_indexes,
    }
