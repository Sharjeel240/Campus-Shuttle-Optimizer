"""Metric-derived recommendations for simulated campus operations."""

from __future__ import annotations

from typing import Any


def derive_recommendations(
    dataset: dict[str, list[dict[str, Any]]],
    allocation: dict[str, Any],
    routing: dict[str, Any],
    scenario_comparison: dict[str, Any] | None,
    mst_result: dict[str, Any],
) -> list[dict[str, str]]:
    """Create recommendations only when supported by observed app metrics."""
    recommendations: list[dict[str, str]] = []
    fleet_capacity = sum(int(vehicle["capacity"]) for vehicle in dataset["fleet"])
    demand = sum(int(request["passengers"]) for request in dataset["requests"])
    if demand > fleet_capacity:
        recommendations.append(
            {
                "recommendation": "Review fleet capacity during the modeled period.",
                "evidence": (
                    f"Synthetic demand contains {demand} passenger seats, while the listed fleet "
                    f"provides {fleet_capacity} seats across its vehicles."
                ),
            }
        )
    if allocation["rejected"]:
        value = sum(float(request["priority"]) for request in allocation["rejected"])
        recommendations.append(
            {
                "recommendation": "Review the shuttle capacity allocation and rejected requests.",
                "evidence": (
                    f"The configured knapsack capacity leaves {len(allocation['rejected'])} "
                    f"whole request groups unselected; their combined priority score is {value:g}."
                ),
            }
        )
    if routing["unserved"]:
        recommendations.append(
            {
                "recommendation": "Investigate additional service for currently unserved requests.",
                "evidence": (
                    f"The multi-vehicle heuristic could not assign "
                    f"{len(routing['unserved'])} of {len(dataset['requests'])} request groups "
                    f"within the listed fleet, depot, reachability, and route-capacity constraints."
                ),
            }
        )
    if scenario_comparison:
        baseline = scenario_comparison["baseline"]
        disrupted = scenario_comparison["disrupted"]
        if disrupted["average_journey_minutes"] > baseline["average_journey_minutes"]:
            recommendations.append(
                {
                    "recommendation": "Inspect alternate road connections for the disrupted scenario.",
                    "evidence": (
                        f"Average simulated journey time changed from "
                        f"{baseline['average_journey_minutes']:.1f} to "
                        f"{disrupted['average_journey_minutes']:.1f} minutes after the selected "
                        f"delay/closure settings."
                    ),
                }
            )
        if disrupted["request_service_percent"] < baseline["request_service_percent"]:
            recommendations.append(
                {
                    "recommendation": "Review contingency service for the newly unserved requests.",
                    "evidence": (
                        f"The simulated request service rate fell from "
                        f"{baseline['request_service_percent']:.1f}% to "
                        f"{disrupted['request_service_percent']:.1f}%."
                    ),
                }
            )
    if mst_result["components"] > 1:
        recommendations.append(
            {
                "recommendation": "Review road-network connectivity between the modeled stop groups.",
                "evidence": (
                    f"The undirected campus graph currently has {mst_result['components']} "
                    f"connected components; no spanning backbone can connect all of them."
                ),
            }
        )
    if not recommendations:
        recommendations.append(
            {
                "recommendation": "Keep the current scenario as a comparison baseline.",
                "evidence": (
                    "The current allocation and route runs did not trigger the configured "
                    "capacity, unserved-demand, disruption, or connectivity indicators."
                ),
            }
        )
    return recommendations
