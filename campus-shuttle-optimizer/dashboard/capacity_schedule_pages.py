"""Passenger allocation and greedy scheduling screens."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from algorithms.greedy_scheduling import activity_selection, job_sequencing
from algorithms.knapsack import allocate_passengers
from dashboard.common import display_table, show_algorithm_note
from dashboard.visualizations import timetable_figure


def render_passenger_allocation(dataset: dict[str, list[dict[str, Any]]]) -> None:
    st.title("Passenger Allocation")
    st.caption("Allocate whole passenger-request groups to one configurable shuttle capacity.")
    show_algorithm_note(
        "Choose request groups with maximum total priority score without exceeding the seat limit.",
        "A two-dimensional 0/1 DP table compares leaving each request out with including it completely.",
        "For each request prefix and capacity, the recurrence checks both legal choices. Backtracking identifies one optimal subset.",
        "O(nC) time and O(nC) space for the displayed table, where n is requests and C is capacity.",
        "Priority is a configurable synthetic score, not a guaranteed measure of passenger satisfaction. Groups are never split.",
    )
    max_capacity = max(80, max((int(vehicle["capacity"]) for vehicle in dataset["fleet"]), default=30))
    default_capacity = min(max_capacity, max(1, max((int(vehicle["capacity"]) for vehicle in dataset["fleet"]), default=28)))
    capacity = st.slider(
        "Available seats for this allocation",
        min_value=1,
        max_value=max_capacity,
        value=default_capacity,
        step=1,
    )
    result = allocate_passengers(dataset["requests"], capacity)
    columns = st.columns(4)
    columns[0].metric("Passengers served", f"{result['passengers_served']:,}")
    columns[1].metric("Seats remaining", result["remaining_seats"])
    columns[2].metric("Total priority score", f"{result['service_value']:g}")
    columns[3].metric("Capacity utilization", f"{result['utilization']:.1f}%")
    st.subheader(f"Selected groups ({len(result['selected'])})")
    display_table(result["selected"], "No request group fits this capacity.")
    st.subheader(f"Rejected groups ({len(result['rejected'])})")
    display_table(result["rejected"])
    export_rows = [
        {**request, "allocation_status": "selected"}
        for request in result["selected"]
    ] + [
        {**request, "allocation_status": "rejected"}
        for request in result["rejected"]
    ]
    st.download_button(
        "Export passenger allocation CSV",
        data=pd.DataFrame(export_rows).to_csv(index=False).encode("utf-8"),
        file_name="passenger_allocation.csv",
        mime="text/csv",
    )
    selected_people = sum(int(request["passengers"]) for request in result["selected"])
    if selected_people > capacity:
        st.error("Capacity invariant failed: the selected groups exceed the configured capacity.")
    else:
        st.success("Capacity check passed: no passenger group was split and the seat limit is respected.")
    if dataset["requests"]:
        with st.expander("Dynamic-programming table (small worked example)"):
            small_requests = dataset["requests"][: min(8, len(dataset["requests"]))]
            small_capacity = min(capacity, 18)
            example = allocate_passengers(small_requests, small_capacity)
            row_names = ["Start"] + [request["request_id"] for request in small_requests]
            display_table(
                [
                    {
                        "request prefix": row_names[row],
                        **{f"{seats} seats": example["table"][row][seats] for seats in range(small_capacity + 1)},
                    }
                    for row in range(len(row_names))
                ]
            )
            st.caption(
                f"This example uses {len(small_requests)} requests and capacities 0–{small_capacity}; "
                "each cell stores the best attainable priority score."
            )


def _display_activity_schedule(requests: list[dict[str, Any]]) -> None:
    result = activity_selection(requests)
    c1, c2 = st.columns(2)
    c1.metric("Compatible trips selected", len(result["scheduled"]))
    c2.metric("Rejected due to overlap / invalid duration", len(result["rejected"]))
    st.subheader("Activity selection — earliest finish first")
    display_table(result["scheduled"], "No compatible trip intervals were found.")
    export_rows = [
        {**trip, "schedule_status": "scheduled"}
        for trip in result["scheduled"]
    ] + [
        {**trip, "schedule_status": "rejected"}
        for trip in result["rejected"]
    ]
    st.download_button(
        "Export activity schedule CSV",
        data=pd.DataFrame(export_rows).to_csv(index=False).encode("utf-8"),
        file_name="activity_schedule.csv",
        mime="text/csv",
        key="export_activity_schedule",
    )
    if result["scheduled"]:
        st.plotly_chart(
            timetable_figure(result["scheduled"], "Single-shuttle compatible trip intervals"),
            use_container_width=True,
            key="activity_timetable",
        )


def _display_job_schedule(requests: list[dict[str, Any]]) -> None:
    result = job_sequencing(requests)
    c1, c2, c3 = st.columns(3)
    c1.metric("Jobs placed", len(result["scheduled"]))
    c2.metric("Rejected jobs", len(result["rejected"]))
    c3.metric("Total service reward", f"{result['total_reward']:g}")
    st.subheader("Job sequencing — reward with deadline")
    display_table(result["scheduled"], "No jobs met a valid deadline.")
    export_rows = [
        {**trip, "schedule_status": "scheduled"}
        for trip in result["scheduled"]
    ] + [
        {**trip, "schedule_status": "rejected"}
        for trip in result["rejected"]
    ]
    st.download_button(
        "Export job schedule CSV",
        data=pd.DataFrame(export_rows).to_csv(index=False).encode("utf-8"),
        file_name="job_schedule.csv",
        mime="text/csv",
        key="export_job_schedule",
    )
    if result["rejected"]:
        with st.expander("Rejected jobs"):
            display_table(result["rejected"])


def render_scheduling(dataset: dict[str, list[dict[str, Any]]]) -> None:
    st.title("Greedy Scheduling")
    st.caption("These single-resource strategies illustrate distinct scheduling assumptions; they do not solve the full multi-vehicle problem.")
    show_algorithm_note(
        "Activity selection maximizes the number of non-overlapping intervals on one shuttle. Job sequencing maximizes reward for unit-time jobs with deadlines.",
        "Activity selection sorts by finish time and accepts the next interval whose start is at or after the last chosen finish. Job sequencing sorts by reward and assigns each job to the latest available slot no later than its deadline.",
        "Earliest-finish activity selection is optimal for maximum-cardinality interval scheduling when each activity uses the same single resource. The unit-job deadline strategy is optimal for maximizing rewards under its unit-duration assumptions.",
        "Activity selection: O(n log n) time. Job sequencing: O(nD) here, where D is the largest deadline.",
        "The two strategies model separate simplified problems. Neither accounts for all fleet, route, capacity, and travel constraints at once.",
    )
    activity_tab, jobs_tab = st.tabs(["Activity selection", "Job sequencing"])
    with activity_tab:
        _display_activity_schedule(dataset["requests"])
    with jobs_tab:
        _display_job_schedule(dataset["requests"])
        st.caption("Deadlines are synthetic numbered service slots; priorities are the synthetic reward values.")
