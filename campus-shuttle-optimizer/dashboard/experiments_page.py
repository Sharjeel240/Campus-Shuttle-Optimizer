"""Interactive measured benchmark and experiment screen."""

from __future__ import annotations

import time
from typing import Any

import pandas as pd
import streamlit as st

from algorithms.knapsack import allocate_passengers
from dashboard.visualizations import make_runtime_matplotlib_chart
from services.benchmarking import (
    run_demand_benchmarks,
    run_graph_benchmarks,
    run_routing_benchmark,
    run_scheduling_benchmark,
)
from services.simulation import create_disrupted_roads, evaluate_scenario


def _as_export_rows(family: str, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"experiment": family, **record} for record in records]


def run_experiment_suite(
    dataset: dict[str, list[dict[str, Any]]],
    graph_sizes: list[int],
    density: float,
    trials: int,
    seed: int,
) -> dict[str, Any]:
    graph_results = run_graph_benchmarks(graph_sizes, density, trials, seed)
    max_demand = max(1, sum(int(request["passengers"]) for request in dataset["requests"]))
    capacities = sorted(set([5, 10, 15, 20, 30, 40, max_demand]))
    demand_results = run_demand_benchmarks(dataset["requests"], dataset["fleet"], capacities)

    counts = sorted(set([min(5, len(dataset["requests"])), min(10, len(dataset["requests"])), len(dataset["requests"])]))
    knapsack_results = []
    for count in counts:
        for capacity in (10, 20, 40):
            start = time.perf_counter()
            solution = allocate_passengers(dataset["requests"][:count], capacity)
            elapsed = (time.perf_counter() - start) * 1000
            knapsack_results.append(
                {
                    "request_count": count,
                    "capacity": capacity,
                    "runtime_ms": elapsed,
                    "passengers_served": solution["passengers_served"],
                    "priority_score": solution["service_value"],
                }
            )

    schedule_result = run_scheduling_benchmark(dataset["requests"])
    fleet_sizes = list(range(1, max(1, len(dataset["fleet"])) + 1))
    route_results = run_routing_benchmark(dataset, fleet_sizes)

    disruption_results = []
    for percent in (0, 20, 40, 60, 80):
        changed_roads, disabled = create_disrupted_roads(
            dataset["roads"], percent, set(), 0, seed + percent
        )
        metrics = evaluate_scenario(
            dataset["stops"], changed_roads, dataset["requests"], dataset["fleet"], disabled
        )
        disruption_results.append(
            {
                "disruption_percent": percent,
                "average_journey_minutes": metrics["average_journey_minutes"],
                "request_service_percent": metrics["request_service_percent"],
                "passengers_served": metrics["passengers_served"],
                "unserved_requests": len(metrics["unserved_requests"]),
                "runtime_ms": metrics["runtime_ms"],
            }
        )

    export = (
        _as_export_rows("graph", graph_results)
        + _as_export_rows("capacity", demand_results)
        + _as_export_rows("knapsack request count and capacity", knapsack_results)
        + _as_export_rows(
            "greedy scheduling",
            [
                {
                    "algorithm": "Activity selection",
                    "runtime_ms": schedule_result["runtime_ms"],
                    "scheduled_count": schedule_result["scheduled_count"],
                    "rejected_count": schedule_result["rejected_count"],
                }
            ],
        )
        + _as_export_rows("multi-vehicle routing", route_results)
        + _as_export_rows("disruption", disruption_results)
    )
    return {
        "graph": graph_results,
        "capacity": demand_results,
        "knapsack": knapsack_results,
        "schedule": schedule_result,
        "routes": route_results,
        "disruption": disruption_results,
        "export": export,
        "seed": seed,
        "trials": trials,
    }


def render_experiments(dataset: dict[str, list[dict[str, Any]]]) -> None:
    st.title("Experiments and Benchmarks")
    st.caption("Run measured algorithms against generated inputs; no benchmark values are pre-filled or fabricated.")
    size_options = [8, 12, 16, 24, 32, 48, 64]
    selected_sizes = st.multiselect("Synthetic graph sizes (number of stops)", size_options, default=[8, 16, 24])
    left, right = st.columns(2)
    density = left.slider("Random graph edge probability", 0.0, 0.50, 0.12, 0.02)
    trials = right.slider("Repeated graph trials", 1, 7, 3)
    seed = st.number_input("Benchmark seed", min_value=0, max_value=2_147_483_647, value=2026, step=1)
    if st.button("Run experiment suite", type="primary", disabled=not selected_sizes):
        with st.spinner("Measuring the selected algorithms against generated inputs…"):
            st.session_state["benchmark_results"] = run_experiment_suite(
                dataset, selected_sizes, density, trials, int(seed)
            )
    result = st.session_state.get("benchmark_results")
    if not result:
        st.info("Choose graph sizes and run the suite to measure runtime, served demand, disruption impact, and fleet scaling.")
        return

    st.caption(
        f"Graph trials averaged: {result['trials']} · benchmark seed: {result['seed']} · "
        "runtimes depend on machine, interpreter, graph shape, and input size."
    )
    st.subheader("Graph algorithm runtime by graph size")
    graph_frame = pd.DataFrame(result["graph"])
    st.pyplot(
        make_runtime_matplotlib_chart(graph_frame, "Measured runtime by graph size"),
        clear_figure=True,
    )
    st.dataframe(graph_frame, use_container_width=True, hide_index=True)
    st.caption(
        "Repeated Dijkstra and Floyd–Warshall both compute all source-destination pairs. "
        "Bellman–Ford is timed on non-negative benchmark graphs for a like-for-like correctness comparison."
    )

    capacity_tab, delay_tab, demand_tab, scheduling_tab = st.tabs(
        ["Demand vs capacity", "Journey time vs disruption", "Knapsack & fleet", "Greedy scheduling"]
    )
    with capacity_tab:
        capacity_frame = pd.DataFrame(result["capacity"])
        st.line_chart(
            capacity_frame.set_index("capacity")["passengers_served"],
            y_label="Passenger seats served",
        )
        st.dataframe(capacity_frame, use_container_width=True, hide_index=True)
    with delay_tab:
        delay_frame = pd.DataFrame(result["disruption"])
        st.line_chart(
            delay_frame.set_index("disruption_percent")[
                ["average_journey_minutes", "request_service_percent"]
            ]
        )
        st.dataframe(delay_frame, use_container_width=True, hide_index=True)
        st.caption("The x-axis setting is a maximum random increase per road; each point uses a distinct repeatable seed.")
    with demand_tab:
        st.subheader("Knapsack runtime by request count and seat capacity")
        st.dataframe(pd.DataFrame(result["knapsack"]), use_container_width=True, hide_index=True)
        st.subheader("Clarke–Wright route output by fleet size")
        st.dataframe(pd.DataFrame(result["routes"]), use_container_width=True, hide_index=True)
    with scheduling_tab:
        schedule = result["schedule"]
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "algorithm": "Earliest-finish activity selection",
                        "runtime_ms": schedule["runtime_ms"],
                        "scheduled trips": schedule["scheduled_count"],
                        "rejected trips": schedule["rejected_count"],
                    }
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.caption("Greedy scheduling feasibility and outcome details are available on the Greedy Scheduling page.")

    export_bytes = pd.DataFrame(result["export"]).to_csv(index=False).encode("utf-8")
    st.download_button(
        "Export all experiment results as CSV",
        data=export_bytes,
        file_name="campus_shuttle_experiments.csv",
        mime="text/csv",
    )
