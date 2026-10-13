"""Campus Shuttle Optimizer — interactive Streamlit dashboard."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import streamlit as st

from dashboard.algorithm_pages import render_all_pairs, render_mst, render_shortest_path
from dashboard.capacity_schedule_pages import render_passenger_allocation, render_scheduling
from dashboard.experiments_page import render_experiments
from dashboard.help_page import render_complexity_help, render_recommendations
from dashboard.network_page import render_network
from dashboard.overview import render_overview
from dashboard.routing_simulation_pages import render_delay_simulation, render_vehicle_routes
from services.data import generate_synthetic_dataset, write_sample_templates


PAGE_NAMES = [
    "Home / Project Overview",
    "Campus Network",
    "MST Algorithms",
    "Shortest Path Routing",
    "All-Pairs Routing",
    "Passenger Allocation",
    "Greedy Scheduling",
    "Multi-Vehicle Routes",
    "Delay Simulation",
    "Experiments and Benchmarks",
    "Algorithm Complexity and Help",
    "Policy Recommendations",
]
OUTPUT_KEYS = (
    "mst_output",
    "shortest_path_output",
    "all_pairs_output",
    "vehicle_route_output",
    "scenario_comparison",
    "benchmark_results",
)


def _fingerprint(dataset: dict[str, list[dict[str, Any]]]) -> str:
    payload = json.dumps(dataset, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _reset_results() -> None:
    for key in OUTPUT_KEYS:
        st.session_state.pop(key, None)


st.set_page_config(
    page_title="Campus Shuttle Optimizer",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

if "campus_dataset" not in st.session_state:
    st.session_state["campus_dataset"] = generate_synthetic_dataset(seed=2026)
if "campus_page" not in st.session_state:
    st.session_state["campus_page"] = PAGE_NAMES[0]
dataset = st.session_state["campus_dataset"]
write_sample_templates(dataset, str(Path(__file__).parent / "data"))

current_fingerprint = _fingerprint(dataset)
previous_fingerprint = st.session_state.get("dataset_fingerprint")
if previous_fingerprint and current_fingerprint != previous_fingerprint:
    _reset_results()
st.session_state["dataset_fingerprint"] = current_fingerprint

with st.sidebar:
    st.title("Shuttle Optimizer")
    st.caption("DAA project demonstration")
    st.session_state["campus_page"] = st.radio(
        "Navigate",
        PAGE_NAMES,
        key="campus_navigation",
        label_visibility="collapsed",
    )
    st.divider()
    if st.button("Reset synthetic sample data", use_container_width=True):
        st.session_state["campus_dataset"] = generate_synthetic_dataset(seed=2026)
        _reset_results()
        st.rerun()
    st.caption("Seeded synthetic data · changes remain in this browser session.")
    st.caption("No real campus performance is claimed.")

page = st.session_state["campus_page"]
if page == "Home / Project Overview":
    render_overview(dataset)
elif page == "Campus Network":
    render_network(dataset)
elif page == "MST Algorithms":
    render_mst(dataset)
elif page == "Shortest Path Routing":
    render_shortest_path(dataset)
elif page == "All-Pairs Routing":
    render_all_pairs(dataset)
elif page == "Passenger Allocation":
    render_passenger_allocation(dataset)
elif page == "Greedy Scheduling":
    render_scheduling(dataset)
elif page == "Multi-Vehicle Routes":
    render_vehicle_routes(dataset)
elif page == "Delay Simulation":
    render_delay_simulation(dataset)
elif page == "Experiments and Benchmarks":
    render_experiments(dataset)
elif page == "Algorithm Complexity and Help":
    render_complexity_help()
elif page == "Policy Recommendations":
    render_recommendations(dataset)
