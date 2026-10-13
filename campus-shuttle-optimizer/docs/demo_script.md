# DAA Review 2 demo script

Estimated length: 5–7 minutes.

1. **Overview (30 seconds):** State that all map, travel-time, demand, and
   benchmark values are reproducible synthetic data.
2. **Campus Network (45 seconds):** Point out stops, depots, weighted roads,
   graph connectivity, CSV templates, and the stop/road editing forms.
3. **MST (45 seconds):** Run Prim and Kruskal. Explain the same minimum forest
   weight, their distinct data structures, and why the result is not a shuttle
   route.
4. **Shortest Path (45 seconds):** Pick two stops and run Dijkstra. Show the
   path, time, and highlighted route. Explain why negative weights are rejected.
5. **All-Pairs / Bellman–Ford (45 seconds):** Show a matrix query or use the
   temporary negative test edge to explain Bellman–Ford and reachable-cycle
   detection.
6. **Passenger Allocation (45 seconds):** Reduce capacity, show whole request
   groups chosen by 0/1 knapsack, and verify remaining seats.
7. **Scheduling (45 seconds):** Contrast earliest-finishing intervals with
   unit-job deadline sequencing and note their different assumptions.
8. **Multi-Vehicle Routes (60 seconds):** Construct routes, inspect each depot
   return, request assignment, and capacity check. State that savings is a
   heuristic.
9. **Delay Simulation (60 seconds):** Set a delay, close roads, choose a seed,
   and compare baseline with disrupted route and service metrics.
10. **Experiments and Recommendations (45 seconds):** Run measured charts,
    export CSV, then connect each recommendation to its displayed evidence.

For a repeatable demonstration, reset sample data first and record the selected
capacity, road closures, disruption percentage, and random seed.
