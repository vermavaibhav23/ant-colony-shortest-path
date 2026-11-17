"""Ant System for positive-weight, undirected shortest paths. Standard library only."""
import heapq
import math
import random
from dataclasses import dataclass


def graph_from_edges(edges, nodes=()):
    graph = {str(n): {} for n in nodes}
    for u, v, weight in edges:
        u, v, weight = str(u), str(v), float(weight)
        if u == v or not math.isfinite(weight) or weight <= 0:
            raise ValueError('Use distinct endpoints and finite positive edge weights.')
        graph.setdefault(u, {})[v] = weight
        graph.setdefault(v, {})[u] = weight
    return graph


def demo_graph():
    return graph_from_edges([('A','B',2),('A','C',5),('B','C',1),
        ('B','D',4),('C','D',1),('C','E',5),('D','E',2),
        ('D','F',6),('E','F',1),('E','G',5),('F','G',2),
        ('F','H',5),('G','H',1)])


def random_graph(n=20, density=0.18, seed=42):
    rng = random.Random(seed)
    edges = [(str(i-1), str(i), rng.randint(1,20)) for i in range(1,n)]
    edges += [(str(i),str(j),rng.randint(1,20)) for i in range(n)
              for j in range(i+2,n) if rng.random() < density]
    return graph_from_edges(edges, range(n))


def dijkstra(graph, source, target):
    if source not in graph or target not in graph:
        raise ValueError('Source and destination must exist.')
    distances, parent, queue = {source:0.0}, {}, [(0.0, source)]
    while queue:
        cost, u = heapq.heappop(queue)
        if cost != distances[u]:
            continue
        if u == target:
            path = [u]
            while u != source:
                u = parent[u]
                path.append(u)
            return path[::-1], cost
        for v,w in graph[u].items():
            if cost+w < distances.get(v, math.inf):
                distances[v], parent[v] = cost+w, u
                heapq.heappush(queue, (cost+w,v))
    return [], math.inf


@dataclass
class Parameters:
    ants: int = 40
    iterations: int = 100
    alpha: float = 1.0
    beta: float = 2.0
    evaporation: float = 0.3
    q: float = 10.0
    seed: int = 42

    def validate(self):
        if self.ants < 1 or self.iterations < 1:
            raise ValueError('Ants and iterations must be positive integers.')
        if not all(math.isfinite(x) for x in (self.alpha,self.beta,self.evaporation,self.q)):
            raise ValueError('Parameters must be finite.')
        if self.alpha < 0 or self.beta < 0 or not 0 < self.evaporation < 1 or self.q <= 0:
            raise ValueError('Require alpha,beta >= 0; 0 < evaporation < 1; Q > 0.')


class Colony:
    def __init__(self, graph, source, target, parameters=None):
        self.p = parameters or Parameters()
        self.p.validate()
        if source not in graph or target not in graph:
            raise ValueError('Source and destination must exist.')
        for u, neighbors in graph.items():
            for v,w in neighbors.items():
                if u == v or not math.isfinite(w) or w <= 0 or graph.get(v,{}).get(u) != w:
                    raise ValueError('Graph must be undirected with finite positive weights.')
        self.graph, self.source, self.target = graph, source, target
        self.rng = random.Random(self.p.seed)
        self.pheromone = {tuple(sorted((u,v))):1.0 for u in graph for v in graph[u]}
        self.path = [source] if source == target else []
        self.cost = 0.0 if source == target else math.inf
        self.history, self.iteration = [], 0
        reachable, stack = {source}, [source]
        while stack:
            for v in graph[stack.pop()]:
                if v not in reachable:
                    reachable.add(v)
                    stack.append(v)
        self.reachable = target in reachable

    def construct_paths(self):
        """Sample one population without changing trails or the incumbent."""
        attempts = []
        successful = []
        if self.reachable and self.source != self.target:
            for _ in range(self.p.ants):
                path, seen, cost = [self.source], {self.source}, 0.0
                while path[-1] != self.target:
                    u = path[-1]
                    choices = [v for v in self.graph[u] if v not in seen]
                    if not choices:
                        break
                    logs = [self.p.alpha*math.log(self.pheromone[tuple(sorted((u,v)))])
                            - self.p.beta*math.log(self.graph[u][v]) for v in choices]
                    maximum = max(logs)
                    weights = [math.exp(x-maximum) for x in logs]
                    v = self.rng.choices(choices, weights=weights)[0]
                    cost += self.graph[u][v]
                    path.append(v)
                    seen.add(v)
                attempts.append({'path':path[:], 'cost':cost, 'success':path[-1] == self.target})
                if path[-1] == self.target:
                    successful.append((path,cost))
        return attempts, successful

    def finish_round(self, successful):
        """Commit the sampled population using the same Ant System update."""
        for path,cost in successful:
            if cost < self.cost:
                self.path, self.cost = path[:], cost
        for edge in self.pheromone:
            self.pheromone[edge] = max(1e-12,(1-self.p.evaporation)*self.pheromone[edge])
        for path,cost in successful:
            for u,v in zip(path,path[1:]):
                self.pheromone[tuple(sorted((u,v)))] += self.p.q/cost
        self.iteration += 1
        row = {'iteration':self.iteration, 'best_cost':self.cost,
               'successful_ants':len(successful)}
        self.history.append(row)
        return row

    def step(self):
        _, successful = self.construct_paths()
        return self.finish_round(successful)

    def run(self):
        for _ in range(self.p.iterations):
            self.step()
        return self.path, self.cost
