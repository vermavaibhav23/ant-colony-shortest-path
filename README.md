# BIC — Ant Colony Optimization Based Shortest Path Finding Algorithm

## Live demo and final journal

**[Open the working browser demo](https://vaibhav-aco-pathfinder.nishverma11.chatgpt.site)** — public, no installation or localhost required.

**[Read / download the final journal PDF](paper/BIC_Journal_Paper.pdf)** · [Overleaf LaTeX source](paper/main.tex)

The journal is the completed project paper from the original benchmark. Its reported experiments are preserved; the later teaching interface is a separate demonstration.

### Browser demo

1. Click **Start exploration** to watch ants travel through the 14-node, 23-road graph.
2. After all attempts finish, inspect each road's old score, 30% evaporation, successful-ant count, reward and new score.
3. Click **Update scores**, or **Next round** to apply the pending update automatically exactly once.
4. Use **Show best route** to highlight the best route found so far.

Every edge displays distance (D) and pheromone (P). Stuck ants are counted separately and receive no reward. The browser uses the same Ant System rule as Python: `new P = max(1e-12, 0.70 * old P) + sum(10 / successful ant route distance)`.

The browser defaults to **40 ants, 5 rounds, seed 1**, a reproducible teaching example with best distances **32, 32, 32, 30, 30**. It uses Mulberry32 random sampling; Python uses its own random generator, so matching seeds do not imply matching routes. Routes are sampled, never forced. Other settings can discover the optimum earlier, later, or miss it.

Browser source is in [`web/`](web/). To preview it locally, run `python -m http.server 8000`, then open `http://localhost:8000/web/`. The public link above works without running any command. Browser engine checks: `node --test web/test-engine.mjs` (Node.js required only for these checks).

## Run from GitHub

```powershell
git clone https://github.com/vermavaibhav23/ant-colony-shortest-path.git
cd ant-colony-shortest-path
python app.py
```

Requires Python 3.10+ with Tkinter. No third-party Python packages are required. The desktop app runs locally; the public browser version is linked above.

- `python app.py` — larger teaching map with distance/score labels and explicit score updates
- `python advanced_app.py` — original graph lab with custom graphs and CSV export
- `python -m unittest -v` — 18 correctness and animation tests
- `python experiments.py` — reproduce the original benchmark

## Run your existing Music folder in VS Code (Windows PowerShell)

```powershell
cd "$env:USERPROFILE\Music\BIC"
code .
python app.py
```

Python 3.10+ with Tkinter is required (included in standard python.org Windows installations). No pip installation is needed. If `python` is unavailable, use `py app.py`.

## Interactive score-update demo (default)

Run `python app.py`. The teaching map has **14 nodes and 23 undirected roads** arranged as a readable grid with cross-links. Every edge shows **D: distance** and **P: preference / pheromone score**. Scores are shown to two decimals on the map and four decimals in the update popup; the solver retains full floating-point precision.

The graph was chosen as a reproducible teaching example. With the default **40 ants, 5 rounds, seed 42, alpha=1, beta=1**, the real solver's best distances are **33, 32, 30, 30, 30**. Dijkstra independently confirms the optimum is 30 (S–A–D–G–J–T). There is no forced delay or injected optimum: other seeds or parameters can find the optimum earlier, later, or miss it.

### Round workflow

1. Click **START**. The opening pause displays the scores used for the new round. Ants then travel along their actual sampled paths; edge distances control their travel times. A small departure delay separates the markers.
2. Wait until all attempts end (food reached or stuck). Scores stay unchanged throughout exploration. A nonmodal **Update preference scores** popup opens with each road's old score, remaining score after 30% evaporation, earned reward, and proposed new score. The preview itself does not change any score.
3. Click **UPDATE SCORES** in the popup or main window. Each road updates exactly once: **new P = max(1e-12, old P × 0.70) + reward**. Each successful ant contributes **10 / its route distance** to every road it used. Failed attempts contribute nothing. Roads without rewards only evaporate.
4. The new edge scores remain displayed. **NEXT ROUND** starts with these same scores. If you did not click Update scores (including if you closed the popup), Next round applies the pending update automatically before sampling the next population. Double-clicking cannot apply the same round twice.
5. On the last round, **FINISH** applies any pending update and shows the best discovered route. **Show best route** can end earlier after a round, also applying its pending update. Dijkstra checks the answer only; it never guides the ants.

**PAUSE / RESUME** controls movement. **Auto-play rounds** automatically commits pending scores and moves on after a four-second review delay. **Settings** contains ants (1–80), rounds (1–100), random seed and playback speed. Playback speed only affects animation.

P is a pheromone preference score, not road distance or whole-path fitness. Smaller route distance means a better path; a larger P makes a road more attractive. Ant choice weights are P^alpha × (1 / D)^beta, normalized over allowed unvisited neighbours.

Run `python -m unittest -v` for **18 tests**, including seeded improvement, pending updates, evaporation/reward accounting, popup dismissal, duplicate-click protection, score carry-over, autoplay and final-round handling.

The paper and original benchmark results are retained as historical experiment artifacts; they do not describe this newer teaching map. The earlier explanation PDF also illustrates a previous six-node demo.

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
