# Algorithm complexity and assumptions

| Algorithm | Problem | Time | Space | Correctness assumptions / limitations |
|---|---|---:|---:|---|
| Prim | Minimum spanning forest | `O((V+E) log V)` | `O(V+E)` | Undirected weighted graph; binary heap. |
| Kruskal | Minimum spanning forest | `O(E log E)` | `O(V+E)` | Undirected weighted graph; DSU with path compression and rank. |
| Dijkstra | Single-source shortest paths | `O((V+E) log V)` | `O(V+E)` | All edge weights must be non-negative. |
| Bellman–Ford | Single-source shortest paths | `O(VE)` | `O(V+E)` | Detects negative cycles reachable from the selected source. |
| Floyd–Warshall | All-pairs shortest paths | `O(V^3)` | `O(V^2)` | Uses a distance and next-hop matrix; reports negative cycles. |
| 0/1 Knapsack | Whole-group passenger allocation | `O(nC)` | `O(nC)` | Integer seat capacity; synthetic non-negative priority score. |
| Activity selection | Maximum compatible interval count | `O(n log n)` | `O(n)` | One shuttle; intervals have fixed start and finish. |
| Job sequencing | Unit-time jobs with deadlines | `O(nD)` | `O(D)` | Common integer slots; each job takes one slot. |
| Clarke–Wright savings | Multi-vehicle route heuristic | `O(V^3 + R^3)` in this implementation | `O(V^2 + R^2)` | Uses all-pairs distances, fleet/depot assignment, whole-group capacity checks, and a greedy savings merge; no global optimality guarantee. |

Here `V` is the number of stops, `E` the number of road connections, `n` the
number of passenger requests, `C` seat capacity, `D` the largest job deadline,
and `R` the number of requests used in routing.

The minimum spanning tree is a low-weight infrastructure backbone. It is not a
passenger-serving route: it does not encode pickup/dropoff demand, vehicle
capacity, shift time, or depot return.
