from algorithms.vehicle_routing import clarke_wright_routes
from services.data import generate_synthetic_dataset, parse_csv_upload
from services.simulation import compare_scenarios, create_disrupted_roads


def small_route_data():
    stops = [
        {"stop_id": "D", "name": "Depot", "x": 0, "y": 0, "is_depot": True},
        {"stop_id": "P1", "name": "Pickup 1", "x": 1, "y": 0, "is_depot": False},
        {"stop_id": "X1", "name": "Dropoff 1", "x": 2, "y": 0, "is_depot": False},
        {"stop_id": "P2", "name": "Pickup 2", "x": 1, "y": 1, "is_depot": False},
        {"stop_id": "X2", "name": "Dropoff 2", "x": 2, "y": 1, "is_depot": False},
    ]
    roads = [
        {"road_id": "a", "from_stop": "D", "to_stop": "P1", "travel_time": 2, "directed": False},
        {"road_id": "b", "from_stop": "P1", "to_stop": "X1", "travel_time": 2, "directed": False},
        {"road_id": "c", "from_stop": "X1", "to_stop": "P2", "travel_time": 1, "directed": False},
        {"road_id": "d", "from_stop": "P2", "to_stop": "X2", "travel_time": 2, "directed": False},
        {"road_id": "e", "from_stop": "X2", "to_stop": "D", "travel_time": 2, "directed": False},
        {"road_id": "f", "from_stop": "D", "to_stop": "P2", "travel_time": 3, "directed": False},
        {"road_id": "g", "from_stop": "X1", "to_stop": "D", "travel_time": 2, "directed": False},
    ]
    requests = [
        {"request_id": "Q1", "pickup_stop": "P1", "destination_stop": "X1", "passengers": 4, "priority": 8},
        {"request_id": "Q2", "pickup_stop": "P2", "destination_stop": "X2", "passengers": 3, "priority": 6},
    ]
    fleet = [{"vehicle_id": "BUS-1", "depot_id": "D", "capacity": 10}]
    return {"stops": stops, "roads": roads, "requests": requests, "fleet": fleet}


def test_vehicle_routes_respect_capacity_connectivity_and_depot_return():
    dataset = small_route_data()
    result = clarke_wright_routes(**dataset)
    assert len(result["routes"]) == 1
    route = result["routes"][0]
    assert route["passengers"] <= route["capacity"]
    assert route["stop_sequence"][0] == "D"
    assert route["stop_sequence"][-1] == "D"
    assert len(route["request_ids"]) == len(set(route["request_ids"]))
    assert len(result["served_request_ids"]) == 2


def test_route_capacity_and_fleet_constraints_produce_unserved_requests():
    dataset = small_route_data()
    dataset["fleet"][0]["capacity"] = 2
    result = clarke_wright_routes(**dataset)
    assert not result["routes"]
    assert {request["request_id"] for request in result["unserved"]} == {"Q1", "Q2"}


def test_seeded_delay_is_reproducible_and_closures_are_applied():
    dataset = generate_synthetic_dataset(seed=2026, request_count=6)
    first = create_disrupted_roads(dataset["roads"], 40, set(), 10, 77)
    second = create_disrupted_roads(dataset["roads"], 40, set(), 10, 77)
    assert first == second
    comparison = compare_scenarios(dataset, 40, set(), 10, 77)
    assert comparison["seed"] == 77
    assert comparison["disrupted"]["runtime_ms"] >= 0
    assert comparison["disrupted"]["disrupted_road_percent"] > 0
    assert comparison["baseline"]["knapsack_capacity"] == max(
        vehicle["capacity"] for vehicle in dataset["fleet"]
    )
    assert comparison["disrupted"]["knapsack_passengers_served"] <= comparison["disrupted"]["knapsack_capacity"]


def test_csv_import_validates_columns_and_references():
    dataset = generate_synthetic_dataset(request_count=2)
    import io

    valid = io.BytesIO(
        b"stop_id,name,x,y,is_depot\nS99,Test,1,2,true\n"
    )
    try:
        parse_csv_upload(valid, "stops", dataset)
    except ValueError as error:
        assert "missing stop" in str(error)
    else:
        raise AssertionError("The replacement graph must retain valid references.")

    invalid = io.BytesIO(b"road_id,from_stop\nE99,S01\n")
    try:
        parse_csv_upload(invalid, "roads", dataset)
    except ValueError as error:
        assert "Missing required columns" in str(error)
    else:
        raise AssertionError("Missing fields should be rejected.")


def test_empty_dataset_and_disconnected_route_are_handled():
    empty = {"stops": [], "roads": [], "requests": [], "fleet": []}
    result = clarke_wright_routes(**empty)
    assert result["routes"] == []
    assert result["unserved"] == []

    dataset = small_route_data()
    dataset["roads"] = []
    routes = clarke_wright_routes(**dataset)
    assert routes["routes"] == []
    assert len(routes["unserved"]) == 2
