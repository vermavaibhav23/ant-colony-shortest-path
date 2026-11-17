import tkinter as tk
import unittest
from app import App, EDGES, teaching_graph, ant_position, score_breakdown
from aco import Colony, Parameters, dijkstra


class TeachingTests(unittest.TestCase):
    def setUp(self):
        self.root=tk.Tk(); self.root.withdraw()
        self.app=App(self.root); self.app.popups_enabled=False

    def tearDown(self):
        self.app.reset();self.root.destroy()

    def start(self,rounds=5):
        self.app.rounds.set(str(rounds)); self.app.start(); self.app.pause()

    def arrive(self):
        self.app.advance_time(3)
        self.app.advance_time(1000)
        self.app.refresh()
        self.assertEqual(self.app.phase,'pending')

    def test_default_genuinely_improves_after_first_round(self):
        c=Colony(teaching_graph(),'S','T',Parameters(iterations=5,beta=1))
        c.run()
        self.assertEqual(len(teaching_graph()),14)
        self.assertEqual(len(EDGES),23)
        self.assertEqual(dijkstra(teaching_graph(),'S','T')[1],30)
        self.assertEqual([r['best_cost'] for r in c.history],[33,32,30,30,30])

    def test_travel_uses_distance(self):
        g=teaching_graph();short=['S','A','D','G','J','T'];long=['S','B','E','H','K','T']
        self.assertEqual(ant_position(g,short,6),('A','D',0.0,False))
        self.assertTrue(ant_position(g,short,30)[3])
        self.assertFalse(ant_position(g,long,30)[3])
        self.assertTrue(ant_position(g,long,33)[3])

    def test_scores_wait_for_click_and_update_once(self):
        self.start();before=self.app.colony.pheromone.copy();self.arrive()
        self.assertEqual(self.app.colony.iteration,0)
        self.assertEqual(self.app.display_tau,before)
        self.app.advance_time(1000)
        self.assertEqual(self.app.colony.pheromone,before)
        rows=self.app.score_rows.copy();self.app.update_scores()
        for edge,row in rows.items():
            self.assertAlmostEqual(row['remaining'],before[edge]*.7)
            self.assertAlmostEqual(self.app.display_tau[edge],row['remaining']+row['reward'])
        self.assertEqual(self.app.colony.iteration,1)
        scores=self.app.colony.pheromone.copy()
        self.app.update_scores();self.app.update_scores()
        self.assertEqual(self.app.colony.iteration,1)
        self.assertEqual(self.app.colony.pheromone,scores)
        self.assertEqual(len(self.app.canvas.find_withtag('score_label')),23)
        self.assertEqual(len(self.app.canvas.find_withtag('distance_label')),23)

    def test_next_round_auto_applies_and_carries_scores(self):
        self.start();self.arrive();self.app.close_popup()
        expected=Colony(teaching_graph(),'S','T',Parameters(iterations=5,beta=1));expected.step()
        self.app.next_round();self.app.pause()
        self.assertEqual(self.app.colony.iteration,1)
        self.assertEqual(self.app.before,expected.pheromone)
        self.assertEqual(self.app.display_tau,expected.pheromone)
        self.assertEqual(self.app.phase,'launch')
        self.app.next_round()  # A double-click cannot skip an active round.
        self.assertEqual(self.app.colony.iteration,1)
        self.arrive();self.app.update_scores();scores=self.app.display_tau.copy()
        self.app.next_round();self.app.pause()
        self.assertEqual(self.app.colony.iteration,2)
        self.assertEqual(self.app.before,scores)

    def test_manual_and_automatic_updates_match_solver(self):
        self.start(3)
        expected=Colony(teaching_graph(),'S','T',Parameters(iterations=3,beta=1));expected.run()
        for i in range(3):
            self.arrive()
            if i%2==0:self.app.update_scores()
            if not self.app.final:self.app.next_round()
            if self.app.running:self.app.pause()
        self.assertTrue(self.app.final)
        self.assertEqual(self.app.colony.history,expected.history)
        self.assertEqual(self.app.colony.pheromone,expected.pheromone)

    def test_no_reward_only_evaporates(self):
        rows=score_breakdown({('A','B'):1.0,('B','C'):2.0},[])
        self.assertEqual(rows[('A','B')]['new'],.7)
        self.assertEqual(rows[('B','C')]['new'],1.4)
        self.assertEqual(rows[('A','B')]['reward'],0)

    def test_last_next_button_commits_pending_round(self):
        self.start(1);self.arrive();self.app.next_round()
        self.assertTrue(self.app.final)
        self.assertEqual(self.app.colony.iteration,1)
        self.assertEqual(self.app.colony.cost,33)
        self.app.next_round();self.assertEqual(self.app.colony.iteration,1)

    def test_popup_close_does_not_apply_scores(self):
        self.start();self.app.popups_enabled=True;self.arrive()
        self.assertIsNotNone(self.app.score_popup)
        self.assertEqual(len(self.app.popup_tree.get_children()),23)
        self.app.close_popup();self.assertEqual(self.app.colony.iteration,0)
        self.app.update_scores();self.assertEqual(self.app.colony.iteration,1)
        self.app.reset();self.assertIsNone(self.app.score_popup)

    def test_autoplay_applies_pending_scores(self):
        self.start(2);self.app.auto.set(True);self.arrive();self.app.cancel()
        self.app.advance_time(5)
        self.assertEqual(self.app.colony.iteration,1)
        self.assertEqual(self.app.phase,'launch')
        self.arrive();self.app.advance_time(5)
        self.assertTrue(self.app.final)
        self.assertEqual(self.app.colony.iteration,2)

    def test_enable_autoplay_while_waiting(self):
        self.start(2);self.arrive()
        self.assertFalse(self.app.running)
        self.app.auto.set(True);self.app.auto_changed()
        self.assertTrue(self.app.running)
        self.assertIsNotNone(self.app.timer)
        self.app.auto.set(False);self.app.auto_changed()
        self.assertFalse(self.app.running)
        self.assertIsNone(self.app.timer)


if __name__=='__main__':unittest.main()
