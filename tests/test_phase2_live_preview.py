"""Exercise the Day web adapter with the real Phase 1 engines."""
from pathlib import Path
from runpy import run_path
import unittest

ROOT = Path(__file__).resolve().parents[1]
Preview = run_path(str(ROOT / "docs/proof/phase-2/day_fixture.py"))["LiveScenesPreview"]


class LiveDayPreviewTest(unittest.TestCase):
    def setUp(self):
        self.now = 0
        scope = Preview.tick.__globals__
        real_clock = scope["monotonic"]
        self.addCleanup(scope.__setitem__, "monotonic", real_clock)
        scope["monotonic"] = lambda: self.now

    def step(self, ticks=1):
        self.now += (ticks + 0.1) / 60
        return self.preview.snapshot()

    def press(self, key):
        self.assertTrue(self.preview.keys({key: True}))
        self.assertTrue(self.preview.keys({key: False}))
        return self.step()

    def start(self, faint=False):
        self.preview = Preview(1, faint)
        for action in ("start", "continue"):
            self.assertTrue(self.preview.action(action, {}))
        return self.preview

    def at(self, pos):
        self.preview.game.session.sim.pos = list(pos)

    def test_real_catch_transfers_stock_and_real_service_is_paid(self):
        preview = self.start()
        state = preview.snapshot()
        fish = next(f for f in state["snapshot"]["fish"] if f["kind"] == "ca_loc")
        self.at(fish["pos"])
        state = self.press("catch")
        self.assertEqual(state["snapshot"]["hold"], ["ca_loc"])
        self.assertIn("fish_caught", [event["name"] for event in state["events"]])
        self.assertTrue(preview.action("pause", {}))
        tick = preview.snapshot()["snapshot"]["tick"]
        self.assertEqual(self.step(120)["snapshot"]["tick"], tick)
        self.assertTrue(preview.action("resume", {}))

        self.at(state["snapshot"]["meta"]["dock_pos"])
        state = self.press("interact")
        self.assertEqual(state["screen"], "evening_intro")
        self.assertEqual(state["inventory"], {"ca_loc": 1})
        self.assertEqual(state["cookable"], ["ca_loc_nuong_trui"])
        self.assertTrue(preview.action("continue", {}))
        state = self.step(preview.game.tuning["quan"]["first_customer_tick"] + 1)
        self.assertEqual(state["snapshot"]["stock"], {"ca_loc": 1})

        self.at(state["snapshot"]["stoves"][0]["pos"])
        state = self.press("interact")
        stove = state["snapshot"]["stoves"][0]
        self.assertEqual(stove["state"], "cooking")
        self.step(stove["cook_ticks_left"] + 1)
        self.assertEqual(self.press("interact")["snapshot"]["hand"]["dish_id"], "ca_loc_nuong_trui")
        self.at(state["snapshot"]["tables"][0]["pos"])
        state = self.press("interact")
        diner = state["snapshot"]["customers"][0]
        self.assertEqual(diner["state"], "eating")
        state = self.step(diner["eat_ticks_left"] + 1)
        self.assertIn("paid", [event["name"] for event in state["events"]])
        self.assertEqual(state["snapshot"]["money"], 72)

        state = self.step(state["snapshot"]["time_left_ticks"] + 1)
        self.assertEqual(state["screen"], "day_result")
        self.assertEqual((state["result"]["served"], state["result"]["tips"]), (1, 12))
        self.assertTrue(preview.action("continue", {}))
        self.assertTrue(preview.snapshot()["shop_unavailable"])
        self.assertFalse(preview.action("buy", {"upgrade_id": "oxygen_1"}))
        self.assertTrue(preview.action("shop_done", {}))
        self.assertEqual(preview.snapshot()["result"]["money"], 72)
        self.assertEqual(preview.snapshot()["screen"], "summary")

    def test_real_faint_does_not_create_sample_inventory(self):
        preview = self.start(faint=True)
        state = self.step(2)
        self.assertEqual((state["screen"], state["gather_reason"]), ("evening_intro", "fainted"))
        self.assertEqual(state["inventory"], {})
        self.assertTrue(preview.action("continue", {}))
        self.assertEqual(preview.snapshot()["snapshot"]["stock"], {})
