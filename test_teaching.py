import tkinter as tk
import unittest
from app import App, teaching_graph, ant_position
from aco import Colony, Parameters, dijkstra


class TeachingTests(unittest.TestCase):
    def test_motion_uses_edge_weights(self):
        graph=teaching_graph()
        self.assertEqual(ant_position(graph,['S','A','C','T'],3),('A','C',0.0,False))
        self.assertTrue(ant_position(graph,['S','A','C','T'],10)[3])
        self.assertFalse(ant_position(graph,['S','B','D','T'],10)[3])
        self.assertTrue(ant_position(graph,['S','B','D','T'],15)[3])
        self.assertEqual(dijkstra(graph,'S','T')[1],10)

    def test_split_round_matches_batch(self):
        a=Colony(teaching_graph(),'S','T',Parameters(seed=7,beta=1))
        b=Colony(teaching_graph(),'S','T',Parameters(seed=7,beta=1))
        for _ in range(5):
            before=a.pheromone.copy()
            attempts,successful=a.construct_paths()
            self.assertEqual(len(attempts),40)
            self.assertEqual(a.pheromone,before)
            a.finish_round(successful); b.step()
            self.assertEqual(a.history,b.history)
            self.assertEqual(a.pheromone,b.pheromone)

    def test_round_animation_and_manual_gate(self):
        root=tk.Tk(); root.withdraw()
        try:
            app=App(root); app.rounds.set('2'); app.start(); app.pause()
            self.assertEqual(len(app.canvas.find_withtag('ant')),40)
            app.advance_time(1.1)
            self.assertEqual(app.phase,'travel')
            app.travel=12
            self.assertGreater(app.arrived_count(),0)
            self.assertLess(app.arrived_count(),40)
            app.advance_time(100); self.assertEqual(app.phase,'compare')
            app.advance_time(3); self.assertEqual(app.phase,'evaporate')
            app.advance_time(1)
            self.assertTrue(all(abs(t-.85)<1e-9 for t in app.display_tau.values()))
            self.assertEqual(app.colony.iteration,0)
            app.advance_time(1); self.assertEqual(app.phase,'deposit')
            self.assertEqual(app.colony.iteration,1)
            app.advance_time(3); self.assertEqual(app.phase,'review')
            self.assertFalse(app.running)
            app.advance_time(100); self.assertEqual(app.colony.iteration,1)
            app.next_round(); app.pause()
            for dt in [2,100,3,2,3]: app.advance_time(dt)
            self.assertTrue(app.final)
            expected=Colony(teaching_graph(),'S','T',Parameters(iterations=2,beta=1)); expected.run()
            self.assertEqual(app.colony.pheromone,expected.pheromone)
            self.assertEqual(app.colony.history,expected.history)
            self.assertEqual(app.colony.cost,10)
            app.reset(); self.assertIsNone(app.timer)
        finally: root.destroy()

    def test_show_best_only_uses_completed_rounds(self):
        root=tk.Tk(); root.withdraw()
        try:
            app=App(root); app.start(); app.pause(); app.show_final()
            self.assertFalse(app.final)
            for dt in [2,100,3,2,3]: app.advance_time(dt)
            self.assertEqual(app.phase,'review')
            app.show_final()
            self.assertTrue(app.final)
            self.assertEqual(app.colony.iteration,1)
            app.reset()
        finally: root.destroy()


if __name__=='__main__': unittest.main()
