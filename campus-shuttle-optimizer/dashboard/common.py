"""Shared dashboard formatting and graph display functions."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from dashboard.visualizations import network_figure


def stop_labels(dataset: dict[str, list[dict[str, Any]]]) -> dict[str, str]:
    return {
        str(stop["stop_id"]): f"{stop['name']} ({stop['stop_id']})"
        for stop in dataset["stops"]
    }


def show_network(
    dataset: dict[str, list[dict[str, Any]]],
    highlighted_paths: list[list[str]] | None = None,
    title: str = "Campus road network",
) -> None:
    st.plotly_chart(
        network_figure(dataset["stops"], dataset["roads"], highlighted_paths, title),
        use_container_width=True,
        key=f"network_{title}",
    )


def display_table(records: list[dict[str, Any]], empty_message: str = "No records to display.") -> None:
    if records:
        st.dataframe(pd.DataFrame(records), use_container_width=True, hide_index=True)
    else:
        st.info(empty_message)


def time_label(minutes: int | float) -> str:
    total = int(minutes)
    return f"{total // 60:02d}:{total % 60:02d}"


def make_id(prefix: str, existing: list[dict[str, Any]], field: str) -> str:
    values = {str(row[field]) for row in existing}
    index = 1
    while f"{prefix}{index:02d}" in values:
        index += 1
    return f"{prefix}{index:02d}"


def show_algorithm_note(problem: str, logic: str, correctness: str, complexity: str, limitation: str) -> None:
    with st.expander("How this algorithm works"):
        st.markdown(f"**Problem:** {problem}")
        st.markdown(f"**Main logic:** {logic}")
        st.markdown(f"**Correctness:** {correctness}")
        st.markdown(f"**Complexity:** {complexity}")
        st.markdown(f"**Limitation:** {limitation}")
