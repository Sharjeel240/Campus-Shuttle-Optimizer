"""Greedy activity-selection and job-sequencing algorithms."""

from __future__ import annotations

from typing import Any


def activity_selection(trips: list[dict[str, Any]]) -> dict[str, Any]:
    """Select a maximum-size compatible set by earliest finishing time."""
    ordered = sorted(
        enumerate(trips),
        key=lambda item: (int(item[1]["finish_time"]), int(item[1]["start_time"])),
    )
    chosen_indexes: list[int] = []
    last_finish: int | None = None
    for index, trip in ordered:
        start = int(trip["start_time"])
        finish = int(trip["finish_time"])
        if finish <= start:
            continue
        if last_finish is None or start >= last_finish:
            chosen_indexes.append(index)
            last_finish = finish
    selected_set = set(chosen_indexes)
    return {
        "scheduled": [trips[index] for index in chosen_indexes],
        "rejected": [trip for index, trip in enumerate(trips) if index not in selected_set],
        "selected_indexes": chosen_indexes,
    }


def job_sequencing(trips: list[dict[str, Any]]) -> dict[str, Any]:
    """Maximize total reward for unit-time jobs with integer deadlines."""
    indexed = list(enumerate(trips))
    for _index, trip in indexed:
        if int(trip["deadline"]) < 1:
            raise ValueError("Job deadlines must be at least one time slot.")
    indexed.sort(
        key=lambda item: float(item[1].get("priority", item[1].get("reward", 0))),
        reverse=True,
    )
    max_deadline = max((int(trip["deadline"]) for trip in trips), default=0)
    slots: list[int | None] = [None] * (max_deadline + 1)
    scheduled_indexes: set[int] = set()
    schedule: list[dict[str, Any]] = []
    for index, trip in indexed:
        for slot in range(min(int(trip["deadline"]), max_deadline), 0, -1):
            if slots[slot] is None:
                slots[slot] = index
                scheduled_indexes.add(index)
                schedule.append({**trip, "slot": slot})
                break
    schedule.sort(key=lambda trip: trip["slot"])
    return {
        "scheduled": schedule,
        "rejected": [trip for index, trip in enumerate(trips) if index not in scheduled_indexes],
        "total_reward": sum(
            float(trips[index].get("priority", trips[index].get("reward", 0)))
            for index in scheduled_indexes
        ),
        "slots": slots,
    }
