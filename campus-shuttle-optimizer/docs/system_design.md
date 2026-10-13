# System design

## Data flow

1. A fixed-seed generator creates the default sample stops, road connections,
   fleet, and request groups when the Streamlit session starts.
2. Session state is the source of truth for interactive edits. A reset restores
   the reproducible sample; CSV imports replace one validated table at a time.
3. Algorithm modules receive ordinary Python records and adjacency lists.
   NetworkX is used for graph representation/validation and Matplotlib/Plotly
   for charts, not as substitutes for the required manual algorithms.
4. The dashboard runs each algorithm on demand and displays its actual result.
5. The disruption page creates a seeded scenario copy; it never overwrites
   baseline roads or demand.
6. Experiment runs record measured values from `time.perf_counter` and can be
   downloaded as CSV.

## Modules

- `algorithms/`: adjacency-list graph utilities, MST, shortest paths,
  all-pairs paths, knapsack, greedy scheduling, and route construction.
- `services/`: synthetic data and CSV validation, scenario simulation,
  benchmarking, and evidence-based recommendations.
- `dashboard/`: Streamlit screens and Plotly/Matplotlib visualizations.
- `tests/`: algorithm, constraint, data-validation, and reproducibility tests.
- `docs/`: algorithm complexity and report outline.

## Scope and limitations

This is an academic simulator with generated values. It does not use GPS,
real-time traffic, actual student records, or a real university network.
The scheduling demonstrations are intentionally distinct simplified problems.
The multi-vehicle route builder is a heuristic, not an exact vehicle-routing
solver; capacity checks conservatively sum passenger groups on a route.
