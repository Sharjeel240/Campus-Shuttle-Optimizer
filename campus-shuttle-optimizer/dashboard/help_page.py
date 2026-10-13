"""Algorithm explanations and evidence-linked policy recommendations."""

from __future__ import annotations

from typing import Any

import networkx as nx
import streamlit as st

from algorithms.graph import build_adjacency, to_networkx
from algorithms.knapsack import allocate_passengers
from algorithms.mst import kruskal_mst
from algorithms.vehicle_routing import clarke_wright_routes
from dashboard.common import display_table
from services.recommendations import derive_recommendations
from services.simulation import compare_scenarios


ALGORITHM_GUIDE = [
    {
        "algorithm": "Prim",
        "problem and I/O": "Undirected weighted graph → minimum spanning forest.",
        "main logic / correctness sketch": "Expand the current forest using the lightest crossing edge. The cut property makes each selected edge safe.",
        "time / space": "O((V+E) log V) / O(V+E)",
        "limitations": "A connection backbone, not a shuttle tour.",
    },
    {
        "algorithm": "Kruskal",
        "problem and I/O": "Undirected weighted graph → minimum spanning forest.",
        "main logic / correctness sketch": "Process edges in ascending weight and keep those joining different disjoint sets. The cut property preserves an optimal forest.",
        "time / space": "O(E log E) / O(V+E)",
        "limitations": "A connection backbone, not a shuttle tour.",
    },
    {
        "algorithm": "Dijkstra",
        "problem and I/O": "Non-negative weighted graph plus source → distances and predecessor map.",
        "main logic / correctness sketch": "A min-heap settles the smallest tentative distance; non-negative edges mean that settled distance cannot later improve.",
        "time / space": "O((V+E) log V) / O(V+E)",
        "limitations": "Rejects negative weights.",
    },
    {
        "algorithm": "Bellman–Ford",
        "problem and I/O": "Weighted graph plus source → distances and predecessor map, or reachable negative-cycle error.",
        "main logic / correctness sketch": "A shortest simple path uses at most V−1 edges, so V−1 full edge-relaxation passes suffice.",
        "time / space": "O(VE) / O(V+E)",
        "limitations": "Slower than Dijkstra on non-negative graphs.",
    },
    {
        "algorithm": "Floyd–Warshall",
        "problem and I/O": "Weighted graph → all-pairs distance and next-hop matrices.",
        "main logic / correctness sketch": "The dynamic-programming recurrence considers each vertex as a possible intermediate in turn.",
        "time / space": "O(V³) / O(V²)",
        "limitations": "Cubic runtime and quadratic memory.",
    },
    {
        "algorithm": "0/1 Knapsack",
        "problem and I/O": "Passenger groups and seat capacity → whole groups with maximum score.",
        "main logic / correctness sketch": "For each request and capacity, choose the better of excluding it or taking it entirely.",
        "time / space": "O(nC) / O(nC)",
        "limitations": "Priority values are modeled scores, not observed satisfaction.",
    },
    {
        "algorithm": "Activity selection",
        "problem and I/O": "Trip intervals → maximum-cardinality compatible set for one shuttle.",
        "main logic / correctness sketch": "Choose the earliest finishing compatible interval, leaving the most remaining time.",
        "time / space": "O(n log n) / O(n)",
        "limitations": "One resource; ignores the complete multi-vehicle route problem.",
    },
    {
        "algorithm": "Job sequencing",
        "problem and I/O": "Unit-time jobs with integer deadlines and rewards → high-value feasible schedule.",
        "main logic / correctness sketch": "Sort by reward and place each job in the latest free slot on or before its deadline.",
        "time / space": "O(nD) / O(D)",
        "limitations": "Assumes jobs take one slot and share a common timeline.",
    },
    {
        "algorithm": "Clarke–Wright savings",
        "problem and I/O": "Requests, depots, and a fleet → capacity-safe heuristic routes.",
        "main logic / correctness sketch": "Merge route tails and heads when saved depot travel is high and reachability, fleet, and seat constraints remain satisfied.",
        "time / space": "O(V³ + R³) in this straightforward implementation / O(V² + R²)",
        "limitations": "Heuristic; does not guarantee a global optimum. Conservative summed demand can reject feasible sequential groups.",
    },
]


def render_complexity_help() -> None:
    st.title("Algorithm Complexity and Help")
    st.caption("Inputs, outputs, correctness assumptions, runtime and space bounds, and limitations.")
    st.dataframe(ALGORITHM_GUIDE, use_container_width=True, hide_index=True)
    st.subheader("Model assumptions")
    st.markdown(
        "- Normal campus travel-time edges are non-negative. A directed negative test edge is temporary and exists only on the shortest-path page.\n"
        "- The MST pages accept undirected road networks; directed road edits cause a clear validation message.\n"
        "- Passenger groups are indivisible in the knapsack and route-capacity checks.\n"
        "- The scheduling demos use one-shuttle intervals or unit-duration reward jobs, respectively.\n"
        "- The Clarke–Wright result is a feasible heuristic output under modeled constraints, not an optimality guarantee.\n"
        "- Random disruptions are reproducible from their seed. Every metric is a simulation result."
    )
    st.subheader("Correctness checks included")
    st.markdown(
        "Automated tests exercise spanning weights and validity, known shortest paths, negative-cycle detection, "
        "unreachable stops, optimal small knapsack instances, non-overlapping schedules, route capacity and depot "
        "return, CSV validation, and seeded simulation reproducibility."
    )
    st.subheader("Project report outline")
    st.markdown(
        "1. **Introduction and problem statement** — campus transport constraints and synthetic-data scope.\n"
        "2. **Methodology** — weighted graph, route demand model, and reproducible scenario generation.\n"
        "3. **Algorithm selection** — MST, shortest paths, knapsack, greedy scheduling, and savings heuristic.\n"
        "4. **System design** — modules, data flow, validation, and interactive dashboard workflows.\n"
        "5. **Complexity analysis** — correctness assumptions, time and space bounds, limitations.\n"
        "6. **Experiments** — measured runtime and service metrics; record hardware and settings.\n"
        "7. **Observations and policy recommendations** — cite metrics from the actual simulation run.\n"
        "8. **Conclusion and future work** — improve demand model, real operational constraints, or routing exactness."
    )


def render_recommendations(dataset: dict[str, list[dict[str, Any]]]) -> None:
    st.title("Policy Recommendations")
    st.caption("Recommendations are generated from the current synthetic data and algorithm outputs.")
    capacity = st.slider(
        "Capacity used for the allocation evidence",
        min_value=1,
        max_value=max(40, max((int(vehicle["capacity"]) for vehicle in dataset["fleet"]), default=40)),
        value=min(28, max(1, max((int(vehicle["capacity"]) for vehicle in dataset["fleet"]), default=28))),
        key="recommendation_capacity",
    )
    try:
        allocation = allocate_passengers(dataset["requests"], capacity)
        routing = clarke_wright_routes(
            dataset["stops"], dataset["roads"], dataset["requests"], dataset["fleet"]
        )
        graph = to_networkx(dataset["stops"], dataset["roads"])
        try:
            mst = kruskal_mst(dataset["stops"], dataset["roads"])
        except ValueError:
            mst = {"components": nx.number_weakly_connected_components(graph)}
        comparison = st.session_state.get("scenario_comparison")
        recommendations = derive_recommendations(
            dataset, allocation, routing, comparison, mst
        )
    except (ValueError, KeyError) as error:
        st.error(f"Could not derive recommendations from the current data: {error}")
        return

    for index, item in enumerate(recommendations, start=1):
        st.subheader(f"{index}. {item['recommendation']}")
        st.write(f"**Evidence:** {item['evidence']}")
    st.info(
        "These are decision-support prompts derived from generated data, not operational instructions "
        "or claims about real campus performance."
    )
    with st.expander("Current measured inputs"):
        st.write(f"Allocation: {allocation['passengers_served']} passengers served with {capacity} seats.")
        st.write(f"Routing: {len(routing['served_request_ids'])}/{len(dataset['requests'])} requests assigned.")
        st.write(f"Network components: {mst['components']}.")
        if comparison:
            st.write(
                f"Disruption comparison: journey time {comparison['baseline']['average_journey_minutes']:.1f} → "
                f"{comparison['disrupted']['average_journey_minutes']:.1f} minutes; "
                f"request service {comparison['baseline']['request_service_percent']:.1f}% → "
                f"{comparison['disrupted']['request_service_percent']:.1f}%."
            )
