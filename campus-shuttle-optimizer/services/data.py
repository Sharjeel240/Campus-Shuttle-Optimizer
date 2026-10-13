"""Reproducible synthetic campus data and validated CSV import/export."""

from __future__ import annotations

import io
import math
import random
from datetime import datetime
from typing import Any

import pandas as pd

from algorithms.graph import build_adjacency
from algorithms.shortest_paths import dijkstra


def generate_synthetic_dataset(seed: int = 2026, request_count: int = 24) -> dict[str, list[dict[str, Any]]]:
    """Generate stable sample stops, roads, shuttle vehicles, and demand."""
    stops = [
        {"stop_id": "S01", "name": "North Gate", "x": 0, "y": 4, "is_depot": True},
        {"stop_id": "S02", "name": "Library", "x": 2, "y": 5, "is_depot": False},
        {"stop_id": "S03", "name": "Engineering Block", "x": 4, "y": 5, "is_depot": False},
        {"stop_id": "S04", "name": "Student Center", "x": 4, "y": 3, "is_depot": False},
        {"stop_id": "S05", "name": "Science Complex", "x": 6, "y": 5, "is_depot": False},
        {"stop_id": "S06", "name": "Sports Arena", "x": 7, "y": 2, "is_depot": False},
        {"stop_id": "S07", "name": "East Depot", "x": 9, "y": 4, "is_depot": True},
        {"stop_id": "S08", "name": "Residence Hall A", "x": 2, "y": 1, "is_depot": False},
        {"stop_id": "S09", "name": "Residence Hall B", "x": 4, "y": 0, "is_depot": False},
        {"stop_id": "S10", "name": "Health Center", "x": 6, "y": 0, "is_depot": False},
        {"stop_id": "S11", "name": "West Gate", "x": 0, "y": 0, "is_depot": False},
        {"stop_id": "S12", "name": "South Depot", "x": 9, "y": 0, "is_depot": True},
        {"stop_id": "S13", "name": "Auditorium", "x": 8, "y": 6, "is_depot": False},
        {"stop_id": "S14", "name": "Innovation Hub", "x": 6, "y": 3, "is_depot": False},
    ]
    road_pairs = [
        ("S01", "S02", 5), ("S02", "S03", 4), ("S03", "S04", 3),
        ("S03", "S05", 5), ("S05", "S13", 4), ("S13", "S07", 5),
        ("S04", "S14", 3), ("S14", "S06", 4), ("S06", "S12", 5),
        ("S08", "S09", 4), ("S09", "S10", 3), ("S10", "S12", 4),
        ("S11", "S08", 5), ("S11", "S01", 6), ("S08", "S04", 5),
        ("S04", "S05", 4), ("S05", "S14", 3), ("S14", "S07", 5),
        ("S09", "S04", 4), ("S10", "S06", 4), ("S02", "S08", 6),
        ("S06", "S07", 6), ("S07", "S12", 7), ("S01", "S03", 8),
        ("S08", "S14", 8), ("S11", "S09", 8), ("S13", "S14", 4),
    ]
    roads = [
        {
            "road_id": f"R{index:02d}",
            "from_stop": start,
            "to_stop": end,
            "travel_time": minutes,
            "directed": False,
        }
        for index, (start, end, minutes) in enumerate(road_pairs, start=1)
    ]
    fleet = [
        {"vehicle_id": "BUS-01", "depot_id": "S01", "capacity": 28, "shift_start": "07:00", "shift_end": "19:00"},
        {"vehicle_id": "BUS-02", "depot_id": "S01", "capacity": 20, "shift_start": "07:00", "shift_end": "19:00"},
        {"vehicle_id": "BUS-03", "depot_id": "S07", "capacity": 24, "shift_start": "07:30", "shift_end": "19:30"},
        {"vehicle_id": "BUS-04", "depot_id": "S07", "capacity": 18, "shift_start": "08:00", "shift_end": "20:00"},
        {"vehicle_id": "BUS-05", "depot_id": "S12", "capacity": 26, "shift_start": "07:00", "shift_end": "19:00"},
        {"vehicle_id": "BUS-06", "depot_id": "S12", "capacity": 20, "shift_start": "08:00", "shift_end": "20:00"},
    ]

    adjacency = build_adjacency(stops, roads)
    rng = random.Random(seed)
    stop_ids = [str(stop["stop_id"]) for stop in stops if not stop["is_depot"]]
    requests: list[dict[str, Any]] = []
    for index in range(1, request_count + 1):
        pickup = rng.choice(stop_ids)
        destinations = [stop for stop in stop_ids if stop != pickup]
        rng.shuffle(destinations)
        destination = next(
            (
                stop
                for stop in destinations
                if dijkstra(adjacency, pickup)[0].get(stop, float("inf")) < float("inf")
            ),
            destinations[0],
        )
        minutes = int(round(dijkstra(adjacency, pickup)[0][destination]))
        start_time = 420 + ((index - 1) * 23) % 540
        passengers = rng.randint(1, 9)
        priority = rng.randint(2, 10)
        requests.append(
            {
                "request_id": f"Q{index:03d}",
                "pickup_stop": pickup,
                "destination_stop": destination,
                "passengers": passengers,
                "priority": priority,
                "deadline": rng.randint(1, 8),
                "estimated_minutes": minutes,
                "start_time": start_time,
                "finish_time": start_time + minutes + 8,
            }
        )
    return {"stops": stops, "roads": roads, "requests": requests, "fleet": fleet}


REQUIRED_COLUMNS = {
    "stops": {"stop_id", "name", "x", "y", "is_depot"},
    "roads": {"road_id", "from_stop", "to_stop", "travel_time", "directed"},
    "requests": {
        "request_id", "pickup_stop", "destination_stop", "passengers",
        "priority", "deadline", "estimated_minutes", "start_time", "finish_time",
    },
    "fleet": {"vehicle_id", "depot_id", "capacity", "shift_start", "shift_end"},
}
IDENTIFIER_COLUMNS = {
    "stops": "stop_id",
    "roads": "road_id",
    "requests": "request_id",
    "fleet": "vehicle_id",
}


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    raise ValueError(f"Expected true/false, received {value!r}.")


def parse_csv_upload(uploaded_file: Any, kind: str, current: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Validate an uploaded CSV and return its parsed replacement records."""
    if kind not in REQUIRED_COLUMNS:
        raise ValueError("Choose one of the supported dataset types.")
    try:
        frame = pd.read_csv(uploaded_file)
    except Exception as error:
        raise ValueError(f"Could not read this CSV: {error}") from error
    missing = REQUIRED_COLUMNS[kind] - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}.")
    if frame.empty:
        raise ValueError("The uploaded CSV has no data rows.")
    records = frame.to_dict(orient="records")
    id_column = IDENTIFIER_COLUMNS[kind]
    id_columns = {
        "stops": ("stop_id",),
        "roads": ("road_id", "from_stop", "to_stop"),
        "requests": ("request_id", "pickup_stop", "destination_stop"),
        "fleet": ("vehicle_id", "depot_id"),
    }[kind]
    for record in records:
        for column in id_columns:
            if pd.isna(record[column]):
                raise ValueError(f"{column} values cannot be blank.")
            record[column] = str(record[column]).strip()
    identifiers = [str(record[id_column]).strip() for record in records]
    if any(not identifier or identifier.lower() == "nan" for identifier in identifiers):
        raise ValueError(f"{id_column} values cannot be blank.")
    if len(identifiers) != len(set(identifiers)):
        raise ValueError(f"{id_column} values must be unique.")

    numeric = {
        "stops": ("x", "y"),
        "roads": ("travel_time",),
        "requests": ("passengers", "priority", "deadline", "estimated_minutes", "start_time", "finish_time"),
        "fleet": ("capacity",),
    }
    for record in records:
        for column in numeric[kind]:
            record[column] = float(record[column])
            if not math.isfinite(record[column]):
                raise ValueError(f"{column} must be a finite number.")
            integer_columns = {
                "requests": {"passengers", "deadline", "estimated_minutes", "start_time", "finish_time"},
                "fleet": {"capacity"},
            }.get(kind, set())
            if column in integer_columns and not record[column].is_integer():
                raise ValueError(f"{column} must be a whole number.")
            if column in integer_columns:
                record[column] = int(record[column])
        if kind == "stops":
            if pd.isna(record["name"]) or not str(record["name"]).strip():
                raise ValueError("Stop names cannot be blank.")
            record["is_depot"] = _parse_bool(record["is_depot"])
        if kind == "roads":
            record["directed"] = _parse_bool(record["directed"])
            if record["travel_time"] < 0:
                raise ValueError("Campus road travel times cannot be negative.")
            if record["from_stop"] == record["to_stop"]:
                raise ValueError("A road must connect two different stops.")
        if kind == "requests":
            record["priority"] = float(record["priority"])
            if record["passengers"] < 1 or record["priority"] < 0:
                raise ValueError("Requests require at least one passenger and a non-negative priority.")
            if record["deadline"] < 1 or record["estimated_minutes"] < 0:
                raise ValueError("Request deadlines must be positive and estimated time cannot be negative.")
            if record["finish_time"] <= record["start_time"]:
                raise ValueError("Request finish time must be later than its start time.")
            if record["pickup_stop"] == record["destination_stop"]:
                raise ValueError("Request pickup and destination must be different stops.")
        if kind == "fleet" and record["capacity"] < 1:
            raise ValueError("Vehicle capacity must be positive.")
        if kind == "fleet":
            for column in ("shift_start", "shift_end"):
                try:
                    datetime.strptime(str(record[column]), "%H:%M")
                except ValueError as error:
                    raise ValueError(f"{column} must use 24-hour HH:MM time.") from error
            if str(record["shift_start"]) >= str(record["shift_end"]):
                raise ValueError("Vehicle shift end must be later than its shift start.")

    candidate = {key: [dict(item) for item in values] for key, values in current.items()}
    candidate[kind] = records
    stop_ids = {str(stop["stop_id"]) for stop in candidate["stops"]}
    if kind == "stops" and not any(bool(stop["is_depot"]) for stop in records):
        raise ValueError("At least one stop must be marked as a depot.")
    if kind == "roads":
        for road in records:
            if road["from_stop"] not in stop_ids or road["to_stop"] not in stop_ids:
                raise ValueError(f"Road {road['road_id']} references an unknown stop.")
    if kind == "requests":
        for request in records:
            if request["pickup_stop"] not in stop_ids or request["destination_stop"] not in stop_ids:
                raise ValueError(f"Request {request['request_id']} references an unknown stop.")
    if kind == "fleet":
        for vehicle in records:
            if vehicle["depot_id"] not in stop_ids:
                raise ValueError(f"Vehicle {vehicle['vehicle_id']} references an unknown depot.")
    # Check all references after any data type is replaced.
    build_adjacency(candidate["stops"], candidate["roads"])
    return records


def csv_bytes(records: list[dict[str, Any]]) -> bytes:
    """Serialize records as UTF-8 CSV bytes."""
    return pd.DataFrame(records).to_csv(index=False).encode("utf-8")


def write_sample_templates(dataset: dict[str, list[dict[str, Any]]], directory: str) -> None:
    """Create downloadable, checked-in-friendly CSV templates if absent."""
    from pathlib import Path

    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    for kind, records in dataset.items():
        path = target / f"sample_{kind}.csv"
        if not path.exists():
            path.write_bytes(csv_bytes(records))


def csv_text(records: list[dict[str, Any]]) -> io.BytesIO:
    """Return a fresh in-memory CSV stream for a Streamlit download button."""
    return io.BytesIO(csv_bytes(records))
