# Campus Shuttle Optimizer

An interactive DAA project that models a synthetic university shuttle network
and demonstrates graph algorithms, greedy optimization, dynamic programming,
capacity-constrained multi-vehicle routing, and seeded disruption experiments.
It is an academic simulator: its values are not observations from a real campus.

## Features

- Weighted campus graph with 14 synthetic stops, 3 depots, connected roads,
  editable stop/road tables, and one-way-road support.
- Manual Prim and Kruskal minimum spanning forest algorithms.
- Manual heap-based Dijkstra, Bellman–Ford with reachable negative-cycle
  detection, and Floyd–Warshall with path reconstruction.
- 0/1 knapsack passenger-group allocation with capacity and DP-table display.
- Earliest-finish activity selection and reward-based unit-job sequencing.
- Capacity-checked multi-vehicle Clarke–Wright savings heuristic with depot
  return and duplicate-service checks.
- Seeded delay and closure simulations with baseline comparison.
- Measured algorithm benchmarks, charts, and experiment CSV export.
- Validated CSV imports and downloadable CSV templates.
- Evidence-linked policy recommendations, pytest tests, complexity notes, and a
  review demo script.

## Architecture

```text
campus-shuttle-optimizer/
├── app.py
├── requirements.txt
├── algorithms/
├── dashboard/
├── services/
├── data/                  # reproducible sample CSVs are created on first run
├── docs/
└── tests/
```

`algorithms/` contains the readable manual implementations. NetworkX is used
for graph representation/validation and not as a replacement for the DAA
algorithms. The dashboard keeps edits in the current Streamlit browser session;
use **Reset synthetic sample data** to restore the fixed-seed scenario.

## Windows installation

Install Python 3.10 or newer, then open PowerShell in this project folder:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks environment activation, run the executable directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The dashboard opens in a browser, normally at `http://localhost:8501`.

## Run tests

```powershell
python -m pytest
```

## Example use

1. Open **Campus Network** to inspect or edit stops and road connections.
2. Open **MST Algorithms** and compare Prim with Kruskal.
3. Select source and destination stops under **Shortest Path Routing**.
4. Set a seat limit under **Passenger Allocation**.
5. Construct fleet routes and compare a seeded disruption.
6. Run **Experiments and Benchmarks** and download the measured CSV.

The CSV upload form replaces only the chosen dataset table and validates
required columns, duplicate IDs, numeric values, and stop references before
applying the imported data.

## Algorithm summary

| Algorithm | Time complexity | Main assumption |
|---|---:|---|
| Prim | `O((V+E) log V)` | Undirected weighted graph |
| Kruskal | `O(E log E)` | Undirected weighted graph |
| Dijkstra | `O((V+E) log V)` | Non-negative road weights |
| Bellman–Ford | `O(VE)` | Detects reachable negative cycles |
| Floyd–Warshall | `O(V^3)` | All-pairs shortest paths |
| 0/1 Knapsack | `O(nC)` | Whole groups, integer capacity |
| Activity selection | `O(n log n)` | One shuttle, fixed trip intervals |
| Job sequencing | `O(nD)` | Unit-time jobs and integer deadlines |
| Clarke–Wright heuristic | `O(V^3 + R^3)` here | Greedy route merges; no global-optimum guarantee |

See `docs/algorithm_complexity.md` for space costs and further detail.

## Experiments and interpretation

Runtime values are measured with `time.perf_counter` on the current machine and
input. They vary by hardware, Python version, graph density, and run conditions.
The dashboard reports only measured results; it does not hardcode performance
claims. Demand values, priorities, and traffic changes are simulated.

## CSV fields

- `stops`: `stop_id,name,x,y,is_depot`
- `roads`: `road_id,from_stop,to_stop,travel_time,directed`
- `requests`: `request_id,pickup_stop,destination_stop,passengers,priority,deadline,estimated_minutes,start_time,finish_time`
- `fleet`: `vehicle_id,depot_id,capacity,shift_start,shift_end`

Download a current sample template from **Campus Network**.

## Known limitations and future work

- Data is synthetic and session-scoped; there is no database or real-time feed.
- Greedy scheduling pages solve two simplified scheduling problems separately.
- Clarke–Wright is a heuristic; passenger groups are conservatively summed for
  route capacity, and optimization is not guaranteed globally.
- The simulator omits dwell time, changing passenger loads within a route,
  driver breaks, time windows beyond the simplified scheduler, and actual
  traffic distributions.

Possible extensions include multi-trip vehicle schedules, pickup/dropoff load
tracking, richer time windows, and validation against user-supplied anonymized
datasets.

## Screenshots

Run the dashboard, open the desired page in a browser, and use the browser's
Save/Print or screenshot function. For a repeatable review capture, reset sample
data and use the fixed sample seed before taking the screenshot.

## Demo

Follow the timed walkthrough in `docs/demo_script.md`.
