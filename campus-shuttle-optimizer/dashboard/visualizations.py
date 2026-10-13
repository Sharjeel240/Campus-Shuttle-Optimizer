"""Network, timetable, and experiment visualizations."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import plotly.graph_objects as go

from algorithms.graph import to_networkx


def network_figure(
    stops: list[dict[str, Any]],
    roads: list[dict[str, Any]],
    highlighted_paths: Iterable[list[str]] | None = None,
    title: str = "Campus road network",
) -> go.Figure:
    """Draw the campus graph, optionally emphasizing selected paths."""
    graph = to_networkx(stops, roads)
    positions = {
        stop_id: (attrs["x"], attrs["y"])
        for stop_id, attrs in graph.nodes(data=True)
    }
    highlighted_pairs: set[frozenset[str]] = set()
    for path in highlighted_paths or []:
        for start, end in zip(path, path[1:]):
            highlighted_pairs.add(frozenset((str(start), str(end))))

    edge_x: list[float | None] = []
    edge_y: list[float | None] = []
    edge_text: list[str] = []
    hot_x: list[float | None] = []
    hot_y: list[float | None] = []
    hot_text: list[str] = []
    weight_labels: list[dict[str, Any]] = []
    annotations = []
    for _start, _end, attrs in graph.edges(data=True):
        # Graph representation duplicates undirected edges to make routing
        # validation convenient; draw each physical road only once.
        if not attrs["directed"] and _start > _end:
            continue
        x0, y0 = positions[_start]
        x1, y1 = positions[_end]
        is_hot = frozenset((_start, _end)) in highlighted_pairs
        target_x, target_y, target_text = (
            (hot_x, hot_y, hot_text) if is_hot else (edge_x, edge_y, edge_text)
        )
        target_x.extend([x0, x1, None])
        target_y.extend([y0, y1, None])
        target_text.extend([f"{attrs['travel_time']:g} min", f"{attrs['travel_time']:g} min", ""])
        weight_labels.append(
            {
                "x": (x0 + x1) / 2,
                "y": (y0 + y1) / 2,
                "text": f"{attrs['travel_time']:g}",
                "color": "#b75925" if is_hot else "#576878",
            }
        )
        if attrs["directed"]:
            annotations.append(
                {
                    "x": x0 + (x1 - x0) * 0.62,
                    "y": y0 + (y1 - y0) * 0.62,
                    "ax": x0 + (x1 - x0) * 0.43,
                    "ay": y0 + (y1 - y0) * 0.43,
                    "xref": "x",
                    "yref": "y",
                    "axref": "x",
                    "ayref": "y",
                    "showarrow": True,
                    "arrowhead": 2,
                    "arrowsize": 1,
                    "arrowwidth": 1,
                    "arrowcolor": "#d4772c" if is_hot else "#8a9aab",
                }
            )

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line={"color": "#b4c1ce", "width": 2},
            text=edge_text,
            hoverinfo="text",
            name="Road",
        )
    )
    if hot_x:
        figure.add_trace(
            go.Scatter(
                x=hot_x,
                y=hot_y,
                mode="lines",
                line={"color": "#e46d35", "width": 5},
                text=hot_text,
                hoverinfo="text",
                name="Selected route / MST",
            )
        )
    if weight_labels:
        figure.add_trace(
            go.Scatter(
                x=[label["x"] for label in weight_labels],
                y=[label["y"] for label in weight_labels],
                mode="text",
                text=[label["text"] for label in weight_labels],
                textfont={"size": 10, "color": [label["color"] for label in weight_labels]},
                hoverinfo="skip",
                name="Road travel time (minutes)",
            )
        )

    for depot_state, label, color, symbol in (
        (False, "Shuttle stop", "#287e82", "circle"),
        (True, "Depot", "#e46d35", "diamond"),
    ):
        selected = [
            (node, attrs)
            for node, attrs in graph.nodes(data=True)
            if bool(attrs["is_depot"]) == depot_state
        ]
        if not selected:
            continue
        figure.add_trace(
            go.Scatter(
                x=[positions[node][0] for node, _attrs in selected],
                y=[positions[node][1] for node, _attrs in selected],
                mode="markers+text",
                text=[node for node, _attrs in selected],
                textposition="top center",
                customdata=[[attrs["name"], "Depot" if depot_state else "Stop"] for _node, attrs in selected],
                hovertemplate="%{customdata[0]}<br>%{customdata[1]} (%{text})<extra></extra>",
                marker={"size": 15, "color": color, "symbol": symbol, "line": {"width": 1, "color": "white"}},
                name=label,
            )
        )
    figure.update_layout(
        title=title,
        height=440,
        margin={"l": 10, "r": 10, "t": 50, "b": 10},
        xaxis={"visible": False, "scaleanchor": "y", "scaleratio": 1},
        yaxis={"visible": False},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
        annotations=annotations,
        hovermode="closest",
    )
    return figure


def make_runtime_matplotlib_chart(frame: pd.DataFrame, title: str) -> plt.Figure:
    """Build an algorithm runtime chart with Matplotlib."""
    figure, axis = plt.subplots(figsize=(8, 4.4))
    if not frame.empty:
        for algorithm, subset in frame.groupby("algorithm"):
            ordered = subset.sort_values("graph_size")
            axis.plot(
                ordered["graph_size"],
                ordered["runtime_ms"],
                marker="o",
                linewidth=1.8,
                label=algorithm,
            )
        axis.legend(frameon=False, ncol=2)
    axis.set_title(title)
    axis.set_xlabel("Number of stops (V)")
    axis.set_ylabel("Measured runtime (ms)")
    axis.grid(True, alpha=0.22)
    figure.tight_layout()
    return figure


def timetable_figure(trips: list[dict[str, Any]], title: str) -> go.Figure:
    """Render selected trips as a simple, readable timeline."""
    base = pd.Timestamp("2026-01-01 00:00:00")
    rows = []
    for index, trip in enumerate(trips):
        rows.append(
            {
                "Trip": str(trip.get("request_id", f"Trip {index + 1}")),
                "Start": base + pd.Timedelta(minutes=int(trip["start_time"])),
                "Finish": base + pd.Timedelta(minutes=int(trip["finish_time"])),
                "Priority": float(trip.get("priority", 0)),
            }
        )
    if not rows:
        return go.Figure().update_layout(title=title, height=250)
    import plotly.express as px

    return px.timeline(
        pd.DataFrame(rows),
        x_start="Start",
        x_end="Finish",
        y="Trip",
        color="Priority",
        color_continuous_scale="Teal",
        title=title,
    ).update_layout(height=max(270, 34 * len(rows)), xaxis_title="Synthetic trip time", yaxis_title="Trip")
