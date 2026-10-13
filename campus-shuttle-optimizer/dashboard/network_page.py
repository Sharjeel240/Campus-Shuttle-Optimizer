"""Campus network editing and CSV data management."""

from __future__ import annotations

from typing import Any

import networkx as nx
import pandas as pd
import streamlit as st

from algorithms.graph import to_networkx
from dashboard.common import make_id, show_network
from services.data import csv_bytes, parse_csv_upload


def _unique_id(value: str, records: list[dict[str, Any]], field: str) -> bool:
    return bool(value.strip()) and all(str(record[field]) != value.strip() for record in records)


def _stop_manager(dataset: dict[str, list[dict[str, Any]]]) -> None:
    st.subheader("Stops and depots")
    add_tab, edit_tab, remove_tab = st.tabs(["Add a stop", "Edit a stop", "Remove a stop"])
    with add_tab:
        suggested = make_id("S", dataset["stops"], "stop_id")
        with st.form("add_stop_form", clear_on_submit=True):
            stop_id = st.text_input("Stop ID", value=suggested)
            name = st.text_input("Stop name")
            column_a, column_b = st.columns(2)
            x = column_a.number_input("Map x-coordinate", value=0.0, step=0.5)
            y = column_b.number_input("Map y-coordinate", value=0.0, step=0.5)
            is_depot = st.checkbox("This stop is a depot")
            submitted = st.form_submit_button("Add stop")
        if submitted:
            if not name.strip() or not _unique_id(stop_id, dataset["stops"], "stop_id"):
                st.error("Enter a name and an unused stop ID.")
            else:
                dataset["stops"].append(
                    {"stop_id": stop_id.strip(), "name": name.strip(), "x": x, "y": y, "is_depot": is_depot}
                )
                st.success(f"Added {name.strip()}.")
                st.rerun()
    with edit_tab:
        if not dataset["stops"]:
            st.info("There are no stops to edit.")
        else:
            stop_ids = [str(stop["stop_id"]) for stop in dataset["stops"]]
            selected_id = st.selectbox("Select stop", stop_ids, key="edit_stop_id")
            stop = next(item for item in dataset["stops"] if str(item["stop_id"]) == selected_id)
            with st.form(f"edit_stop_form_{selected_id}"):
                name = st.text_input("Stop name", value=str(stop["name"]))
                column_a, column_b = st.columns(2)
                x = column_a.number_input("Map x-coordinate", value=float(stop["x"]), step=0.5, key=f"edit_x_{selected_id}")
                y = column_b.number_input("Map y-coordinate", value=float(stop["y"]), step=0.5, key=f"edit_y_{selected_id}")
                is_depot = st.checkbox("This stop is a depot", value=bool(stop["is_depot"]), key=f"edit_depot_{selected_id}")
                submitted = st.form_submit_button("Save stop changes")
            if submitted:
                if not name.strip():
                    st.error("Stop name cannot be blank.")
                elif stop["is_depot"] and not is_depot and sum(bool(item["is_depot"]) for item in dataset["stops"]) == 1:
                    st.error("At least one depot must remain in the network.")
                else:
                    stop.update({"name": name.strip(), "x": x, "y": y, "is_depot": is_depot})
                    st.success("Stop updated.")
                    st.rerun()
    with remove_tab:
        if not dataset["stops"]:
            st.info("There are no stops to remove.")
        else:
            stop_ids = [str(stop["stop_id"]) for stop in dataset["stops"]]
            selected_id = st.selectbox("Stop to remove", stop_ids, key="remove_stop_id")
            stop = next(item for item in dataset["stops"] if str(item["stop_id"]) == selected_id)
            related_roads = [
                road for road in dataset["roads"]
                if selected_id in (str(road["from_stop"]), str(road["to_stop"]))
            ]
            related_requests = [
                request for request in dataset["requests"]
                if selected_id in (str(request["pickup_stop"]), str(request["destination_stop"]))
            ]
            st.warning(
                f"Removing this stop also removes {len(related_roads)} connected road(s) "
                f"and {len(related_requests)} request(s) that reference it."
            )
            confirm = st.checkbox("Confirm removal and dependent-row cleanup", key=f"confirm_stop_{selected_id}")
            if st.button("Remove selected stop", disabled=not confirm):
                if stop["is_depot"] and sum(bool(item["is_depot"]) for item in dataset["stops"]) == 1:
                    st.error("Keep at least one depot in the network.")
                else:
                    dataset["stops"] = [item for item in dataset["stops"] if str(item["stop_id"]) != selected_id]
                    dataset["roads"] = [item for item in dataset["roads"] if item not in related_roads]
                    dataset["requests"] = [item for item in dataset["requests"] if item not in related_requests]
                    dataset["fleet"] = [item for item in dataset["fleet"] if str(item["depot_id"]) != selected_id]
                    st.success("Stop and dependent rows removed.")
                    st.rerun()


def _road_manager(dataset: dict[str, list[dict[str, Any]]]) -> None:
    st.subheader("Road connections")
    add_tab, edit_tab, remove_tab = st.tabs(["Add a road", "Edit a road", "Remove a road"])
    stop_ids = [str(stop["stop_id"]) for stop in dataset["stops"]]
    if len(stop_ids) < 2:
        st.info("Add at least two stops before creating road connections.")
        return
    with add_tab:
        suggested = make_id("E", dataset["roads"], "road_id")
        with st.form("add_road_form", clear_on_submit=True):
            road_id = st.text_input("Road ID", value=suggested)
            column_a, column_b = st.columns(2)
            start = column_a.selectbox("From stop", stop_ids)
            end_options = [stop_id for stop_id in stop_ids if stop_id != start]
            end = column_b.selectbox("To stop", end_options)
            travel_time = st.number_input("Travel time (minutes)", min_value=0.1, value=5.0, step=0.5)
            directed = st.checkbox("One-way road")
            submitted = st.form_submit_button("Add connection")
        if submitted:
            if not _unique_id(road_id, dataset["roads"], "road_id"):
                st.error("Enter an unused road ID.")
            elif start == end:
                st.error("A road must connect two different stops.")
            else:
                dataset["roads"].append(
                    {
                        "road_id": road_id.strip(),
                        "from_stop": start,
                        "to_stop": end,
                        "travel_time": travel_time,
                        "directed": directed,
                    }
                )
                st.success("Road connection added.")
                st.rerun()
    with edit_tab:
        if dataset["roads"]:
            road_ids = [str(road["road_id"]) for road in dataset["roads"]]
            selected_id = st.selectbox("Select road", road_ids, key="edit_road_id")
            road = next(item for item in dataset["roads"] if str(item["road_id"]) == selected_id)
            with st.form(f"edit_road_form_{selected_id}"):
                start_index = stop_ids.index(str(road["from_stop"]))
                start = st.selectbox("From stop", stop_ids, index=start_index, key=f"edit_from_{selected_id}")
                end_options = [stop_id for stop_id in stop_ids if stop_id != start]
                end_current = str(road["to_stop"])
                end_index = end_options.index(end_current) if end_current in end_options else 0
                end = st.selectbox("To stop", end_options, index=end_index, key=f"edit_to_{selected_id}")
                travel_time = st.number_input(
                    "Travel time (minutes)",
                    min_value=0.1,
                    value=float(road["travel_time"]),
                    step=0.5,
                    key=f"edit_minutes_{selected_id}",
                )
                directed = st.checkbox(
                    "One-way road",
                    value=bool(road["directed"]),
                    key=f"edit_direction_{selected_id}",
                )
                submitted = st.form_submit_button("Save road changes")
            if submitted:
                if start == end:
                    st.error("A road must connect two different stops.")
                else:
                    road.update(
                        {"from_stop": start, "to_stop": end, "travel_time": travel_time, "directed": directed}
                    )
                    st.success("Road connection updated.")
                    st.rerun()
        else:
            st.info("There are no roads to edit.")
    with remove_tab:
        if dataset["roads"]:
            road_ids = [str(road["road_id"]) for road in dataset["roads"]]
            selected_id = st.selectbox("Road to remove", road_ids, key="remove_road_id")
            confirm = st.checkbox("Confirm removing this road", key=f"confirm_road_{selected_id}")
            if st.button("Remove selected road", disabled=not confirm):
                dataset["roads"] = [
                    road for road in dataset["roads"] if str(road["road_id"]) != selected_id
                ]
                st.success("Road connection removed.")
                st.rerun()
        else:
            st.info("There are no roads to remove.")


def _csv_management(dataset: dict[str, list[dict[str, Any]]]) -> None:
    st.subheader("CSV templates, import, and export")
    st.caption("CSV imports replace only the selected dataset table. IDs and stop references are validated before changes are applied.")
    kinds = ("stops", "roads", "requests", "fleet")
    columns = st.columns(4)
    for column, kind in zip(columns, kinds):
        column.download_button(
            f"Download {kind} template",
            data=csv_bytes(dataset[kind]),
            file_name=f"sample_{kind}.csv",
            mime="text/csv",
            key=f"download_template_{kind}",
        )
    kind = st.selectbox("Dataset table to replace", kinds)
    uploaded = st.file_uploader("Choose a CSV file", type=["csv"], key="network_csv_upload")
    if uploaded and st.button("Validate and import CSV", key="import_csv_button"):
        try:
            records = parse_csv_upload(uploaded, kind, dataset)
            dataset[kind] = records
            st.success(f"Imported {len(records)} {kind} row(s).")
            st.rerun()
        except (ValueError, KeyError) as error:
            st.error(str(error))
    with st.expander("Current CSV data"):
        data_type = st.selectbox("View table", kinds, key="csv_table_preview")
        st.dataframe(pd.DataFrame(dataset[data_type]), use_container_width=True, hide_index=True)


def render_network(dataset: dict[str, list[dict[str, Any]]]) -> None:
    st.title("Campus Network")
    st.caption("Stops are graph vertices; road connections carry travel time in minutes. Edit the scenario and all calculations use the updated data.")
    graph = to_networkx(dataset["stops"], dataset["roads"])
    columns = st.columns(4)
    columns[0].metric("Stops", graph.number_of_nodes())
    columns[1].metric("Physical roads", len(dataset["roads"]))
    columns[2].metric("Weakly connected groups", nx.number_weakly_connected_components(graph) if graph else 0)
    columns[3].metric("Depots", sum(bool(stop["is_depot"]) for stop in dataset["stops"]))
    show_network(dataset)
    st.caption("Directed arrows identify one-way roads. All sample roads are undirected; added or imported roads may be one-way.")
    with st.expander("Edit stops, depots, and road connections", expanded=True):
        _stop_manager(dataset)
        st.divider()
        _road_manager(dataset)
    with st.expander("Manage dataset CSV files"):
        _csv_management(dataset)
