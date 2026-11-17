"""Reproduce the paper's results: python experiments.py (standard library)."""
import csv
import json
import math
import platform
import statistics
import time
from pathlib import Path
from dataclasses import asdict
from aco import *


def main():
    out=Path(__file__).parent/'results'; out.mkdir(exist_ok=True)
    cases=[('Demo',demo_graph(),'A','H')]+[(f'Random-{n}',random_graph(n,0.18,42),'0',str(n-1)) for n in (15,30,50)]
    rows=[]; summary=[]
    for name,g,s,t in cases:
        exact_path,exact=dijkstra(g,s,t)
        times=[]
        for _ in range(100):
            start=time.perf_counter(); dijkstra(g,s,t); times.append((time.perf_counter()-start)*1000)
        for seed in range(20):
            c=Colony(g,s,t,Parameters(seed=seed))
            start=time.perf_counter(); path,cost=c.run(); ms=(time.perf_counter()-start)*1000
            hit=next((r['iteration'] for r in c.history if r['best_cost']==exact),None)
            rows.append(dict(case=name,seed=seed,nodes=len(g),edges=sum(map(len,g.values()))//2,
                exact_cost=exact,aco_cost=cost if math.isfinite(cost) else None,
                gap_pct=100*(cost-exact)/exact if math.isfinite(cost) else None,
                optimal=cost==exact,runtime_ms=ms,first_optimal_iteration=hit,path='->'.join(path)))
            if seed==0:
                with (out/(name+'_history.csv')).open('w',newline='') as f:
                    w=csv.DictWriter(f,fieldnames=c.history[0]); w.writeheader(); w.writerows(c.history)
        selected=[r for r in rows if r['case']==name]
        gaps=[r['gap_pct'] for r in selected if r['gap_pct'] is not None]
        item=dict(case=name,nodes=len(g),edges=sum(map(len,g.values()))//2,exact_cost=exact,
            found=sum(r['aco_cost'] is not None for r in selected),optimal=sum(r['optimal'] for r in selected),
            mean_gap=statistics.mean(gaps) if gaps else None,max_gap=max(gaps) if gaps else None,
            mean_ms=statistics.mean(r['runtime_ms'] for r in selected),sd_ms=statistics.stdev(r['runtime_ms'] for r in selected),
            dijkstra_ms=statistics.mean(times),exact_path=exact_path)
        summary.append(item); print(item,flush=True)
    with (out/'runs.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    (out/'summary.json').write_text(json.dumps({'parameters':asdict(Parameters()),'seeds':list(range(20)),
        'graph_seed':42,'density':0.18,'python':platform.python_version(),'platform':platform.platform(),
        'processor':platform.processor(),'summary':summary},indent=2))


if __name__=='__main__': main()
