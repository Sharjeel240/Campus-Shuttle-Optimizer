# Campus Shuttle Optimizer

A Streamlit DAA simulator for campus shuttle networks, passenger allocation, vehicle routing, greedy scheduling, and reproducible traffic-disruption experiments.

## Run & Operate

- `cd campus-shuttle-optimizer && streamlit run app.py` — run the dashboard locally (Windows setup: see its README)
- `cd campus-shuttle-optimizer && python -m pytest` — run the algorithm and data-validation tests
- `Campus Shuttle Optimizer` workflow — run the Streamlit preview on port 5000
- `pnpm --filter @workspace/api-server run dev` — run the workspace API server (port 8080)
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- The shuttle simulator has no required environment variables or database.

## Stack

- Python 3.10+, Streamlit, NetworkX, Pandas, NumPy, Plotly, Matplotlib, pytest
- The wider workspace also contains a pnpm monorepo and shared Express API scaffold.

## Where things live

- `campus-shuttle-optimizer/algorithms/` — manual DAA algorithm implementations
- `campus-shuttle-optimizer/services/` — generated data, CSV validation, simulation, benchmarks, recommendations
- `campus-shuttle-optimizer/dashboard/` — Streamlit pages and visualizations
- `campus-shuttle-optimizer/tests/` — pytest coverage
- `campus-shuttle-optimizer/docs/` — complexity, system design, and review demo script
- `campus-shuttle-optimizer/README.md` — Windows setup, usage, and CSV fields

## Architecture decisions

- Sample records use a fixed seed and Streamlit session state; reset restores the sample scenario.
- NetworkX supports graph representation and connectivity inspection; required DAA algorithms remain manually implemented.
- Traffic disruption runs on copied road records and reports simulated outcomes only.
- The Clarke–Wright output is a feasible heuristic, not a globally optimal result.

## Product

The dashboard supports editable campus maps, graph analysis, passenger capacity allocation, greedy scheduling, fleet routes, seeded disruption comparison, measured experiments, and metric-derived recommendations.

## User preferences

The requested dashboard stack is Python and Streamlit, with readable manual DAA algorithm implementations and Windows setup instructions.

## Gotchas

- MST pages require every road to be undirected; Dijkstra requires non-negative travel times.
- Greedy activity selection and job sequencing are separate simplified models, not full-fleet scheduling.
- Route seat checks conservatively sum the passenger groups on each route.
- Runtime charts show measurements for the current environment and inputs, not fixed benchmark claims.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
