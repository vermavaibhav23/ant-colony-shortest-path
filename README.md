# BIC — Ant Colony Optimization Based Shortest Path Finding Algorithm

## Run from GitHub

```powershell
git clone https://github.com/vermavaibhav23/ant-colony-shortest-path.git
cd ant-colony-shortest-path
python app.py
```

Requires Python 3.10+ with Tkinter. No third-party Python packages are required. The desktop app runs locally; this repository is not a browser-hosted app.

- `python app.py` — simplified animated teaching demo
- `python advanced_app.py` — original graph lab with custom graphs and CSV export
- `python -m unittest -v` — 12 correctness and animation tests
- `python experiments.py` — reproduce the original benchmark

## Run your existing Music folder in VS Code (Windows PowerShell)

```powershell
cd "$env:USERPROFILE\Music\BIC"
code .
python app.py
```

Python 3.10+ with Tkinter is required (included in standard python.org Windows installations). No pip installation is needed. If `python` is unavailable, use `py app.py`.

## Simplified visual demo (default)

`python app.py` opens a large map with six nodes and eight roads, including cross-links. Edge labels are distances; the map is not drawn to scale. The upper direct route S–A–C–T has distance 10; the lower direct route S–B–D–T has distance 15. Cross-links allow other choices and possible dead ends.

- **START** begins one round. Actual sampled ant paths are animated with small ant-shaped markers.
- Ants leave in a short stream to remain visible. Travel time is proportional to cumulative edge distance, at the same distance rate for every ant. Launch delay only separates the markers; it does not affect the algorithm.
- Arrived ants are removed from the map and counted at FOOD. Ants reaching dead ends stop, are counted as stuck and receive no pheromone reward.
- One short explanation follows exploration, comparison, evaporation and reinforcement. The entire population is evaluated before trails are updated; early arrival does not trigger an early deposit.
- The demo pauses after each complete round. Click **NEXT ROUND** to see the effect of the updated trails. Enable **Auto-play rounds** for continuous playback.
- **PAUSE / RESUME** freezes or resumes the current animation. **Show best route** selects the cheapest solution from completed rounds and highlights it in green; it does not secretly compute additional rounds.
- **Settings** contains ants, round count, seed and speed. Default: 40 ants, 5 rounds, alpha=1, beta=1, evaporation=0.3, Q=10, seed=42. Changing speed affects playback only. Ants/rounds/seed changes take effect on restart.

The teaching graph and beta=1 setting are separate from the original benchmark. The paper, original algorithm defaults and recorded benchmark results remain unchanged. Run `python -m unittest -v` to check the solver, weighted travel timing, phase transitions and round accounting.

## Original advanced graph lab

Run `python advanced_app.py` for the original application described in the paper, including custom graphs, CSV export and the eight-node benchmark demo.

1. Click **Run / restart** for the eight-node demo; the exact optimum is 10.
2. Adjust ants, iterations, alpha, beta, evaporation or random seed and rerun.
3. Green edges show the best ACO path. Blue edge thickness shows relative pheromone. The chart shows best-so-far cost and the Dijkstra optimum.
4. Pause/resume, switch to a reproducible random graph, or load your own JSON graph.
5. Export the iteration history as CSV. Use Save graph to obtain an editable JSON example.

Custom graph schema:
```json
{"nodes": ["A", "B", "C"], "edges": [["A", "B", 2], ["B", "C", 3]], "source": "A", "target": "C"}
```

Graphs are undirected; weights must be finite and strictly positive. Node names are strings. Isolated nodes may be included in `nodes`. Duplicate edges use the last supplied weight. Source=target returns cost zero. Disconnected targets are reported explicitly.

## Tests and paper experiments

```powershell
python -m unittest -v
python experiments.py
```

`results/runs.csv` contains all 80 measured runs. `results/summary.json` includes configuration, machine metadata and aggregates. Four per-case CSV files contain seed-0 convergence histories. Timings depend on the machine. Experiments use four fixed graphs and 20 solver seeds per graph, not 20 different graphs. Regenerating experiments does not automatically rewrite the paper: its reported results are a snapshot of the delivered run.

## Algorithm

Ants make stochastic self-avoiding walks with transition weights tau^alpha × (1/edge_cost)^beta. An ant reaching a dead end fails for that iteration. After all ants finish, every edge evaporates by (1-rho), with a numerical floor of 1e-12. Every successful ant deposits Q/path_cost on each traversed undirected edge. No Dijkstra path or exact distance is used to guide ACO. Dijkstra is only an independent comparison. The best solution is retained across iterations; finite runs do not guarantee optimality.

## Paper / Overleaf

`paper/main.tex` is a complete IEEEtran source containing the original supplied text plus new sections and six vector diagrams. The figures are drawn inside LaTeX using TikZ/PGFPlots; no external image files are required. Set the compiler to pdfLaTeX in Overleaf and paste this entire file into the BIC main file, or upload it. `paper/original.tex` preserves the exact supplied source.

The original literature review and bibliography were preserved as requested. The newer references in that supplied text have not been independently verified; review their bibliographic details before submission. The added implementation/results section is limited to static positive-weight graphs; it does not claim superiority over Dijkstra or demonstrate dynamic routing, robotics or obstacle avoidance.

Files: `aco.py` algorithm; `app.py` animated teaching GUI; `advanced_app.py` original graph lab; `experiments.py` repeatable evaluation; `test_aco.py` and `test_teaching.py` correctness checks; `paper/` source; `results/` evidence. The paper and its results describe the original experiment, not the new teaching graph.
