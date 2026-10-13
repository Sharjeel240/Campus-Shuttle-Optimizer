"""MST, single-source, and all-pairs shortest path screens."""

from __future__ import annotations

import time
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st

from algorithms.all_pairs import floyd_warshall, reconstruct_all_pairs_path
from algorithms.graph import build_adjacency, validate_undirected
from algorithms.mst import kruskal_mst, prim_mst
from algorithms.shortest_paths import (
    NegativeCycleError,
    bellman_ford,
    dijkstra,
    reconstruct_path,
)
from dashboard.common import show_algorithm_note, show_network, stop_labels


def render_mst(dataset: dict[str, list[dict[str, Any]]]) -> None:
    st.title("Minimum Spanning Tree")
    st.caption("Compare manual Prim and Kruskal implementations on the current undirected campus roads.")
    show_algorithm_note(
        "Connect all reachable stops with the least total edge weight.",
        "Prim expands from each unvisited component using a min-heap. Kruskal sorts roads by weight and uses disjoint-set union to avoid cycles.",
        "Both greedy choices produce a minimum spanning forest for an undirected weighted graph; disconnected input produces one tree per component.",
        "Prim: O((V + E) log V) with a binary heap. Kruskal: O(E log E), dominated by sorting.",
        "The MST is a low-cost network backbone, not an optimal passenger-serving shuttle route.",
    )
    if st.button("Run Prim and Kruskal", type="primary"):
        try:
            validate_undirected(dataset["roads"])
            start = time.perf_counter()
            prim_result = prim_mst(dataset["stops"], dataset["roads"])
            prim_ms = (time.perf_counter() - start) * 1000
            start = time.perf_counter()
            kruskal_result = kruskal_mst(dataset["stops"], dataset["roads"])
            kruskal_ms = (time.perf_counter() - start) * 1000
            st.session_state["mst_output"] = (prim_result, prim_ms, kruskal_result, kruskal_ms)
        except ValueError as error:
            st.error(str(error))
    output = st.session_state.get("mst_output")
    if output:
        prim_result, prim_ms, kruskal_result, kruskal_ms = output
        metric_columns = st.columns(4)
        metric_columns[0].metric("Prim total weight", f"{prim_result['total_weight']:.1f} min")
        metric_columns[1].metric("Prim runtime", f"{prim_ms:.4f} ms")
        metric_columns[2].metric("Kruskal total weight", f"{kruskal_result['total_weight']:.1f} min")
        metric_columns[3].metric("Kruskal runtime", f"{kruskal_ms:.4f} ms")
        st.write(f"Prim components: **{prim_result['components']}** · Kruskal components: **{kruskal_result['components']}**")
        if abs(prim_result["total_weight"] - kruskal_result["total_weight"]) > 1e-8:
            st.error("The manual implementations disagree on total forest weight.")
        else:
            st.success("Correctness cross-check: both implementations returned the same total forest weight.")
        st.subheader("Prim forest")
        st.dataframe(pd.DataFrame(prim_result["edges"]), use_container_width=True, hide_index=True)
        show_network(
            dataset,
            [[edge["from_stop"], edge["to_stop"]] for edge in prim_result["edges"]],
            "Prim minimum spanning forest",
        )
    else:
        st.info("Run both algorithms to see their measured output and highlighted forest.")


def render_shortest_path(dataset: dict[str, list[dict[str, Any]]]) -> None:
    st.title("Shortest Path Routing")
    st.caption("Find one source-to-destination route with a manually implemented single-source algorithm.")
    show_algorithm_note(
        "Find a minimum-travel-time path from one selected campus stop to another.",
        "Dijkstra uses a binary min-heap and relaxes non-negative edges. Bellman–Ford relaxes every directed adjacency arc up to V−1 times and checks for a reachable negative cycle.",
        "Dijkstra is correct for non-negative weights. Bellman–Ford handles negative edges and reports a negative cycle reachable from the chosen source.",
        "Dijkstra: O((V + E) log V). Bellman–Ford: O(VE).",
        "Normal road travel times are non-negative. A temporary one-way negative test edge is available here to demonstrate Bellman–Ford behavior; it is not saved to the campus dataset.",
    )
    labels = stop_labels(dataset)
    if len(labels) < 2:
        st.warning("Add at least two stops before running a route search.")
        return
    c1, c2, c3 = st.columns(3)
    source = c1.selectbox("Source stop", list(labels), format_func=labels.get, key="sp_source")
    destination = c2.selectbox(
        "Destination stop",
        list(labels),
        index=min(1, len(labels) - 1),
        format_func=labels.get,
        key="sp_destination",
    )
    algorithm = c3.selectbox("Algorithm", ["Dijkstra", "Bellman–Ford"])
    use_test_edge = st.checkbox("Add a temporary negative test edge (not saved)")
    test_edge: tuple[str, str, float] | None = None
    if use_test_edge:
        test_columns = st.columns(3)
        test_from = test_columns[0].selectbox("Test edge from", list(labels), key="negative_from")
        test_to = test_columns[1].selectbox("Test edge to", list(labels), index=1, key="negative_to")
        test_weight = test_columns[2].number_input("Test edge weight (minutes)", value=-2.0, step=1.0)
        test_edge = (test_from, test_to, float(test_weight))
    if st.button("Find shortest path", type="primary"):
        try:
            adjacency = build_adjacency(dataset["stops"], dataset["roads"], allow_negative=True)
            if test_edge:
                if test_edge[0] == test_edge[1]:
                    raise ValueError("Choose two different stops for the temporary test edge.")
                adjacency[test_edge[0]].append((test_edge[1], test_edge[2]))
            start = time.perf_counter()
            if algorithm == "Dijkstra":
                distances, parents = dijkstra(adjacency, source)
            else:
                distances, parents = bellman_ford(adjacency, source)
            runtime = (time.perf_counter() - start) * 1000
            path = reconstruct_path(parents, source, destination)
            st.session_state["shortest_path_output"] = {
                "source": source,
                "destination": destination,
                "algorithm": algorithm,
                "distance": distances[destination],
                "path": path,
                "runtime": runtime,
                "test_edge": test_edge,
            }
        except (ValueError, NegativeCycleError) as error:
            st.session_state.pop("shortest_path_output", None)
            st.error(str(error))
    output = st.session_state.get("shortest_path_output")
    if output:
        st.subheader("Route result")
        if not output["path"]:
            st.warning("The selected destination is unreachable from this source.")
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Shortest travel time", f"{output['distance']:.2f} min")
            c2.metric("Execution time", f"{output['runtime']:.4f} ms")
            c3.metric("Stops in sequence", len(output["path"]))
            names = {str(stop["stop_id"]): str(stop["name"]) for stop in dataset["stops"]}
            st.write(" → ".join(f"{names.get(stop, stop)} ({stop})" for stop in output["path"]))
            show_network(dataset, [output["path"]], f"{output['algorithm']} selected route")
    else:
        st.info("Select endpoints and run a shortest-path algorithm.")


def render_all_pairs(dataset: dict[str, list[dict[str, Any]]]) -> None:
    st.title("All-Pairs Routing")
    st.caption("Compute shortest distances between every ordered pair of campus stops with Floyd–Warshall.")
    show_algorithm_note(
        "Find shortest travel times for all source-destination pairs.",
        "For each intermediate stop k, compare the current i→j distance against i→k→j and update the next-hop table.",
        "After each intermediate node is considered, the matrix contains shortest paths whose intermediate nodes come from the processed prefix. Unreachable pairs remain infinity.",
        "O(V³) time and O(V²) space.",
        "Most appropriate for a small or medium campus map when many route queries are needed. Large sparse graphs may be faster with repeated Dijkstra runs.",
    )
    if st.button("Compute all-pairs matrix", type="primary"):
        try:
            start = time.perf_counter()
            nodes, distances, next_hop = floyd_warshall(build_adjacency(dataset["stops"], dataset["roads"]))
            runtime = (time.perf_counter() - start) * 1000
            st.session_state["all_pairs_output"] = (nodes, distances, next_hop, runtime)
        except ValueError as error:
            st.error(str(error))
    output = st.session_state.get("all_pairs_output")
    if not output:
        st.info("Compute the matrix to display distances and query a path.")
        return
    nodes, distances, next_hop, runtime = output
    labels = stop_labels(dataset)
    st.metric("Floyd–Warshall runtime", f"{runtime:.4f} ms")
    matrix = pd.DataFrame(
        [
            [round(value, 2) if np.isfinite(value) else "∞" for value in row]
            for row in distances
        ],
        index=[labels.get(node, node) for node in nodes],
        columns=[labels.get(node, node) for node in nodes],
    )
    st.dataframe(matrix, use_container_width=True)

    c1, c2 = st.columns(2)
    source = c1.selectbox("Path source", nodes, format_func=labels.get, key="allpairs_source")
    destination = c2.selectbox(
        "Path destination", nodes, index=min(1, len(nodes) - 1), format_func=labels.get, key="allpairs_destination"
    )
    path = reconstruct_all_pairs_path(nodes, next_hop, source, destination)
    if path:
        total = distances[nodes.index(source)][nodes.index(destination)]
        st.success(f"{total:.2f} minutes · " + " → ".join(path))
        show_network(dataset, [path], "Floyd–Warshall selected route")
    else:
        st.warning("The selected destination is unreachable.")

    if st.button("Compare repeated Dijkstra with Floyd–Warshall"):
        adjacency = build_adjacency(dataset["stops"], dataset["roads"])
        start = time.perf_counter()
        for node in nodes:
            dijkstra(adjacency, node)
        dijkstra_ms = (time.perf_counter() - start) * 1000
        start = time.perf_counter()
        floyd_warshall(adjacency)
        floyd_ms = (time.perf_counter() - start) * 1000
        st.dataframe(
            pd.DataFrame(
                [
                    {"method": "Dijkstra from each stop", "runtime_ms": dijkstra_ms, "queries covered": len(nodes) ** 2},
                    {"method": "Floyd–Warshall", "runtime_ms": floyd_ms, "queries covered": len(nodes) ** 2},
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
