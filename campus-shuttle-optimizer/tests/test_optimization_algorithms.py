from algorithms.greedy_scheduling import activity_selection, job_sequencing
from algorithms.knapsack import allocate_passengers


def test_knapsack_optimum_and_capacity_invariant():
    requests = [
        {"request_id": "A", "passengers": 3, "priority": 4},
        {"request_id": "B", "passengers": 4, "priority": 5},
        {"request_id": "C", "passengers": 2, "priority": 3},
    ]
    result = allocate_passengers(requests, 5)
    assert {request["request_id"] for request in result["selected"]} == {"A", "C"}
    assert result["service_value"] == 7
    assert result["passengers_served"] <= 5
    assert len(result["selected"]) + len(result["rejected"]) == len(requests)


def test_knapsack_validates_capacity_and_group_sizes():
    try:
        allocate_passengers([], -1)
    except ValueError as error:
        assert "Capacity" in str(error)
    else:
        raise AssertionError("Negative capacity should be rejected.")
    try:
        allocate_passengers([{"passengers": 0, "priority": 1}], 5)
    except ValueError as error:
        assert "passenger" in str(error)
    else:
        raise AssertionError("An empty request group should be rejected.")


def test_activity_selection_is_non_overlapping_and_finish_time_greedy():
    trips = [
        {"request_id": "long", "start_time": 1, "finish_time": 10},
        {"request_id": "first", "start_time": 1, "finish_time": 3},
        {"request_id": "second", "start_time": 3, "finish_time": 5},
        {"request_id": "third", "start_time": 5, "finish_time": 7},
    ]
    result = activity_selection(trips)
    assert [trip["request_id"] for trip in result["scheduled"]] == ["first", "second", "third"]
    assert all(
        left["finish_time"] <= right["start_time"]
        for left, right in zip(result["scheduled"], result["scheduled"][1:])
    )


def test_job_sequencing_respects_deadlines_and_maximizes_reward():
    jobs = [
        {"request_id": "A", "deadline": 2, "priority": 100},
        {"request_id": "B", "deadline": 1, "priority": 19},
        {"request_id": "C", "deadline": 2, "priority": 27},
        {"request_id": "D", "deadline": 1, "priority": 25},
    ]
    result = job_sequencing(jobs)
    assert result["total_reward"] == 127
    assert len(result["scheduled"]) == 2
    assert all(job["slot"] <= job["deadline"] for job in result["scheduled"])


def test_job_sequencing_rejects_zero_deadline():
    try:
        job_sequencing([{"request_id": "A", "deadline": 0, "priority": 1}])
    except ValueError as error:
        assert "deadline" in str(error)
    else:
        raise AssertionError("A zero deadline should be rejected.")
