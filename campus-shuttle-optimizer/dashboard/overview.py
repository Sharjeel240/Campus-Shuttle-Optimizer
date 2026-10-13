"""Home page and project overview."""

from __future__ import annotations

from typing import Any

import streamlit as st

from dashboard.common import show_network


def render_overview(dataset: dict[str, list[dict[str, Any]]]) -> None:
    st.title("Campus Shuttle Optimizer")
    st.caption(
        "A synthetic campus transit lab for route planning, capacity allocation, "
        "trip scheduling, and disruption analysis."
    )
    columns = st.columns(4)
    metrics = (
        (len(dataset["stops"]), "Stops"),
        (len(dataset["roads"]), "Road connections"),
        (len(dataset["fleet"]), "Shuttles"),
        (len(dataset["requests"]), "Passenger requests"),
    )
    for column, (value, label) in zip(columns, metrics):
        column.metric(label, value)

    show_network(dataset, title="Sample campus network")
    left, right = st.columns([1.4, 1])
    with left:
        st.subheader("What the simulator demonstrates")
        st.markdown(
            "- **Graphs:** campus roads, Prim and Kruskal spanning forests, "
            "Dijkstra, Bellman–Ford, and Floyd–Warshall.\n"
            "- **Optimization:** 0/1 knapsack for whole passenger groups and "
            "two greedy trip schedulers.\n"
            "- **Routing:** a capacity-checked Clarke–Wright savings heuristic "
            "for a fleet serving multiple depots.\n"
            "- **Robustness:** seeded road delays and closures, with baseline "
            "and disrupted outcomes compared on the same synthetic demand.\n"
            "- **Experiments:** measured runtimes and solution metrics from the "
            "code running in this session."
        )
        st.info(
            "All passenger, road, and performance values are generated sample data. "
            "They are not observations from a real university."
        )
    with right:
        st.subheader("Quick facts")
        passenger_demand = sum(int(request["passengers"]) for request in dataset["requests"])
        total_fleet_seats = sum(int(vehicle["capacity"]) for vehicle in dataset["fleet"])
        st.write(f"Modeled seat demand: **{passenger_demand:,}**")
        st.write(f"Fleet seat capacities listed: **{total_fleet_seats:,}**")
        st.write(f"Designated depots: **{sum(bool(stop['is_depot']) for stop in dataset['stops'])}**")
        st.write(f"Network direction: **{'mixed' if any(road['directed'] for road in dataset['roads']) else 'undirected'}**")
        st.caption("A sum of vehicle capacities is a planning summary, not a one-trip capacity.")

    with st.expander("How to present this in a review"):
        st.markdown(
            "Start with the network and explain that travel times are edge weights. "
            "Compare the two MST implementations, select a shortest-path algorithm, "
            "then demonstrate an all-or-nothing capacity decision. Finish with a "
            "multi-vehicle route run and a seeded disruption so the same inputs can "
            "be reproduced during the viva."
        )
