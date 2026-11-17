import math
import unittest
from aco import *


class AlgorithmTests(unittest.TestCase):
    def test_demo_optimum_and_valid_path(self):
        g=demo_graph(); c=Colony(g,'A','H'); path,cost=c.run()
        self.assertEqual(dijkstra(g,'A','H')[1],10)
        self.assertEqual(cost,10)
        self.assertEqual(len(path),len(set(path)))
        self.assertEqual(sum(g[u][v] for u,v in zip(path,path[1:])),cost)
        costs=[r['best_cost'] for r in c.history]
        self.assertTrue(all(a>=b for a,b in zip(costs,costs[1:])))

    def test_disconnected(self):
        g=graph_from_edges([('A','B',1)],['C'])
        c=Colony(g,'A','C'); self.assertFalse(c.reachable)
        self.assertEqual(c.run(),([],math.inf))
        self.assertEqual(dijkstra(g,'A','C'),([],math.inf))

    def test_identical_endpoints(self):
        c=Colony(demo_graph(),'A','A')
        self.assertEqual(c.run(),(['A'],0))

    def test_reproducible(self):
        a=Colony(demo_graph(),'A','H'); b=Colony(demo_graph(),'A','H')
        self.assertEqual(a.run(),b.run()); self.assertEqual(a.history,b.history)

    def test_invalid_inputs(self):
        for weight in [0,-1,math.inf,math.nan]:
            with self.assertRaises(ValueError): graph_from_edges([('A','B',weight)])
        with self.assertRaises(ValueError): Colony(demo_graph(),'X','H')
        with self.assertRaises(ValueError): Colony(demo_graph(),'A','H',Parameters(evaporation=1))

    def test_evaporation_and_deposit(self):
        c=Colony(graph_from_edges([('A','B',2)]),'A','B',Parameters(ants=1,iterations=1))
        c.step(); self.assertAlmostEqual(c.pheromone[('A','B')],0.7+10/2)

    def test_single_edge_and_dead_end(self):
        g=graph_from_edges([('A','B',2),('A','X',1),('B','C',3)])
        path,cost=Colony(g,'A','C').run()
        self.assertEqual((path,cost),(['A','B','C'],5))

    def test_random_paths_not_better_than_exact(self):
        for seed in range(5):
            g=random_graph(12,0.2,seed); c=Colony(g,'0','11',Parameters(iterations=20,seed=seed)); path,cost=c.run()
            self.assertGreaterEqual(cost,dijkstra(g,'0','11')[1])
            if path: self.assertEqual(cost,sum(g[u][v] for u,v in zip(path,path[1:])))


if __name__=='__main__': unittest.main()
