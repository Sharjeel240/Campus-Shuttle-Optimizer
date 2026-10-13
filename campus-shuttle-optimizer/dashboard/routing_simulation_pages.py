"""Multi-vehicle route construction and disruption simulation screens."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from algorithms.vehicle_routing import clarke_wright_routes
from dashboard.common import display_table, show_algorithm_note, show_network
from services.simulation import compare_scenarios


def render_vehicle_routes(dataset: dict[str, list[dict[str, Any]]]) -> None:
    st.title("Multi-Vehicle Routes")
    st.caption("Build depot-return routes from whole passenger requests with the Clarke–Wright savings heuristic.")
    show_algorithm_note(
        "Join compatible depot-to-request routes to save travel time while assigning service to multiple vehicles.",
        "The implementation starts with depot→pickup→destination→depot routes, ranks savings from joining route tails and heads, and merges when roads remain reachable and conservative passenger-seat totals fit an available vehicle.",
        "Every merge preserves its request groups, depot, route continuity, and a capacity upper bound. After merges, routes are assigned only to listed fleet vehicles and each served request appears once.",
        "This implementation's all-pairs shortest-path preparation is O(V³); savings merges are O(R³) in the straightforward repeated-search implementation.",
        "Clarke–Wright is a heuristic and does not guarantee a globally optimal route set. Summing all group sizes is conservative if passengers can alight before later pickups.",
    )
    if st.button("Construct vehicle routes", type="primary"):
        try:
            result = clarke_wright_routes(
                dataset["stops"], dataset["roads"], dataset["requests"], dataset["fleet"]
            )
            st.session_state["vehicle_route_output"] = result
        except (ValueError, KeyError) as error:
            st.error(str(error))
    result = st.session_state.get("vehicle_route_output")
    if not result:
        st.info("Run the heuristic to see vehicle assignments, stop sequences, and capacity checks.")
        return
    served_count = len(result["served_request_ids"])
    passengers = sum(
        int(request["passengers"])
        for route in result["routes"]
        for request in route["requests"]
    )
    total_seats = sum(int(route["capacity"]) for route in result["routes"])
    columns = st.columns(4)
    columns[0].metric("Routes assigned", len(result["routes"]))
    columns[1].metric("Request groups served", served_count)
    columns[2].metric("Total route time", f"{result['total_time']:.1f} min")
    columns[3].metric("Assigned seat utilization", f"{passengers / total_seats * 100:.1f}%" if total_seats else "0.0%")
    if result["unserved"]:
        st.warning(f"{len(result['unserved'])} request(s) could not be assigned under current reachability and fleet constraints.")
        with st.expander("Unserved requests"):
            display_table(result["unserved"])
    else:
        st.success("Every request group was assigned exactly once.")
    for route in result["routes"]:
        label = f"{route['vehicle_id']} · {route['passengers']}/{route['capacity']} seats · {route['total_time']:.1f} min"
        with st.expander(label, expanded=True):
            st.write("Stop sequence: " + " → ".join(route["stop_sequence"]))
            st.write("Request groups: " + ", ".join(route["request_ids"]))
            st.metric("Route seat utilization", f"{route['utilization']:.1f}%")
            show_network(
                dataset,
                [route["stop_sequence"]],
                f"Route for {route['vehicle_id']}",
            )
            display_table(route["requests"], "No requests assigned.")
    served_ids = [request_id for route in result["routes"] for request_id in route["request_ids"]]
    if len(served_ids) != len(set(served_ids)):
        st.error("Validation failed: a request was assigned to multiple vehicles.")
    for route in result["routes"]:
        if route["passengers"] > route["capacity"]:
            st.error(f"Validation failed: {route['vehicle_id']} exceeds its capacity.")
    export_routes = [
        {
            "vehicle_id": route["vehicle_id"],
            "depot_id": route["depot_id"],
            "request_ids": ";".join(route["request_ids"]),
            "stop_sequence": ";".join(route["stop_sequence"]),
            "passengers": route["passengers"],
            "capacity": route["capacity"],
            "utilization_percent": route["utilization"],
            "total_travel_time_minutes": route["total_time"],
            "returns_to_depot": route["stop_sequence"][0] == route["stop_sequence"][-1],
        }
        for route in result["routes"]
    ]
    export_routes.extend(
        {
            "vehicle_id": "",
            "depot_id": "",
            "request_ids": str(request["request_id"]),
            "stop_sequence": "",
            "passengers": request["passengers"],
            "capacity": "",
            "utilization_percent": "",
            "total_travel_time_minutes": "",
            "returns_to_depot": False,
            "route_status": "unserved",
        }
        for request in result["unserved"]
    )
    st.download_button(
        "Export optimized routes CSV",
        data=pd.DataFrame(export_routes).to_csv(index=False).encode("utf-8"),
        file_name="optimized_shuttle_routes.csv",
        mime="text/csv",
    )


def render_delay_simulation(dataset: dict[str, list[dict[str, Any]]]) -> None:
    st.title("Delay Simulation")
    st.caption("Compare baseline and disrupted runs using synthetic demand, a configurable seed, random delay, and road closures.")
    show_algorithm_note(
        "Measure how uncertain road travel and closed connections affect route service and journey times.",
        "A seeded random generator applies a bounded percentage increase to active edges and closes the selected plus randomly sampled roads. Shortest routes and the fleet heuristic are recomputed on the resulting graph.",
        "Identical input data and seed reproduce the same simulated delays and closures. Metrics are calculated from the route plans returned by the current algorithms.",
        "Runtime depends on network size, route demand, and environment; reported values are measured per run.",
        "This is a synthetic scenario, not a traffic forecast or observation from a real campus.",
    )
    road_ids = [str(road["road_id"]) for road in dataset["roads"]]
    column_a, column_b = st.columns(2)
    increase = column_a.slider("Maximum random travel-time increase (%)", 0, 150, 35, 5)
    closure_percent = column_b.slider("Random road closure (%)", 0, 50, 5, 1)
    selected_closed = st.multiselect("Also disable selected road connections", road_ids)
    seed = st.number_input("Random seed", min_value=0, max_value=2_147_483_647, value=2026, step=1)
    if st.button("Simulate disrupted scenario", type="primary"):
        try:
            result = compare_scenarios(
                dataset,
                float(increase),
                set(selected_closed),
                float(closure_percent),
                int(seed),
            )
            st.session_state["scenario_comparison"] = result
        except (ValueError, KeyError) as error:
            st.error(str(error))
    comparison = st.session_state.get("scenario_comparison")
    if not comparison:
        st.info("Set the disruption and seed values, then run the comparison.")
        return
    baseline = comparison["baseline"]
    disrupted = comparison["disrupted"]
    st.caption(
        f"Seed {comparison['seed']} · {len(comparison['disabled_road_ids'])} closed road(s) · "
        f"{disrupted['disrupted_road_percent']:.1f}% of road connections affected."
    )
    labels = [
        ("Average journey time", "average_journey_minutes", "min"),
        ("Requests served", "request_service_percent", "%"),
        ("Passengers served", "passengers_served", ""),
        ("0/1 groups within largest vehicle capacity", "knapsack_passengers_served", " passengers"),
        ("Average delay", "average_delay_minutes", "min"),
        ("Vehicle seat utilization", "capacity_utilization_percent", "%"),
        ("Runtime", "runtime_ms", "ms"),
    ]
    rows = []
    for label, key, unit in labels:
        rows.append(
            {
                "Metric": label,
                "Baseline": f"{baseline[key]:.2f}{unit}",
                "Disrupted": f"{disrupted[key]:.2f}{unit}",
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.download_button(
        "Export scenario comparison CSV",
        data=pd.DataFrame(
            [
                {"scenario": "baseline", **baseline},
                {"scenario": "disrupted", **disrupted},
            ]
        ).drop(
            columns=[
                "unserved_requests",
                "routing",
                "journey_times",
                "knapsack_allocation",
            ],
            errors="ignore",
        ).to_csv(index=False).encode("utf-8"),
        file_name="delay_scenario_comparison.csv",
        mime="text/csv",
    )
    chart = pd.DataFrame(
        [
            {"Scenario": "Baseline", "Average journey time": baseline["average_journey_minutes"], "Requests served (%)": baseline["request_service_percent"]},
            {"Scenario": "Disrupted", "Average journey time": disrupted["average_journey_minutes"], "Requests served (%)": disrupted["request_service_percent"]},
        ]
    )
    chart_tab_a, chart_tab_b = st.tabs(["Journey time", "Requests served"])
    with chart_tab_a:
        st.bar_chart(chart.set_index("Scenario")["Average journey time"])
    with chart_tab_b:
        st.bar_chart(chart.set_index("Scenario")["Requests served (%)"])
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Baseline route plan")
        show_network(
            dataset,
            [route["stop_sequence"] for route in baseline["routing"]["routes"]],
            "Baseline vehicle routes",
        )
    with c2:
        st.subheader("Disrupted route plan")
        show_network(
            dataset,
            [route["stop_sequence"] for route in disrupted["routing"]["routes"]],
            "Disrupted vehicle routes",
        )
    if disrupted["unserved_requests"]:
        with st.expander("Unserved after disruption"):
            display_table(disrupted["unserved_requests"])
    if comparison["disabled_road_ids"]:
        st.write("Closed road IDs: " + ", ".join(comparison["disabled_road_ids"]))
    st.info("Every result above is simulated from the current synthetic dataset.")
    allocation_left, allocation_right = st.columns(2)
    for column, label, metrics in (
        (allocation_left, "Baseline 0/1 allocation", baseline),
        (allocation_right, "Disrupted 0/1 allocation", disrupted),
    ):
        with column:
            st.subheader(label)
            selected_ids = metrics["knapsack_request_ids"]
            st.write(
                f"Selected request groups: {', '.join(selected_ids) if selected_ids else 'none'}"
            )
            st.caption(
                f"Recomputed from route-feasible requests at a "
                f"{metrics['knapsack_capacity']}-seat single-vehicle limit."
            )
