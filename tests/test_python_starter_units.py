"""Unit test của khung PYTHON trong starter (ids, inputs, Session). Nếu nhóm thay bằng ngôn ngữ khác, XÓA file này
(và viết unit test tương đương bằng ngôn ngữ của nhóm); test hộp đen test_smoke_p1.py vẫn dùng nguyên."""

import unittest

from chonoi.errors import BadInput
from chonoi.ids import IdAllocator, id_key, sort_by_id
from chonoi.contract import load_contract
from chonoi.inputs import InputPlayer, InputState, LiveInputs, load_frames
from chonoi.runner import Session
from chonoi.scenario import load_scenario

from helpers import Workdir, frames, write_json


class Units(unittest.TestCase):
    def test_id_sorting(self):
        self.assertEqual([e["id"] for e in sort_by_id([{"id": "F10"}, {"id": "F2"}, {"id": "B1"}])], ["B1", "F2", "F10"])
        self.assertLess(id_key("F2"), id_key("F10"))

    def test_id_allocator_continues_after_max(self):
        a = IdAllocator()
        a.reserve("F3")
        a.reserve("F10")
        self.assertEqual(a.new("F"), "F11")
        self.assertEqual(a.new("F"), "F12")
        self.assertEqual(a.new("S"), "S1")

    def test_input_edges_and_inherit(self):
        with Workdir() as w:
            p = write_json(w.path("i.json"), frames({"tick": 1, "interact": True}, {"tick": 2, "move": [1, 1]}, {"tick": 3, "interact": False}, {"tick": 4, "interact": True}))
            pl = InputPlayer(load_frames(p))
            self.assertFalse(pl.advance(0).pressed("interact"))
            self.assertTrue(pl.advance(1).pressed("interact"))
            s2 = pl.advance(2)
            self.assertFalse(s2.pressed("interact"), "giữ true không lặp lại")
            self.assertAlmostEqual(s2.move[0] ** 2 + s2.move[1] ** 2, 1.0)
            pl.advance(3)
            self.assertTrue(pl.advance(4).pressed("interact"))
            self.assertEqual(pl.advance(5).move, s2.move, "move giữ giá trị cũ khi vắng frame")

    def test_bad_frames_raise(self):
        with Workdir() as w:
            with self.assertRaises(BadInput):
                load_frames(write_json(w.path("i.json"), frames({"tick": 0, "move": [2, 0]})))

    def test_catch_is_a_v10_button_and_attack_is_not(self):
        with Workdir() as w:
            load_frames(write_json(w.path("i.json"), frames({"tick": 0, "catch": True})))
            with self.assertRaises(BadInput):
                load_frames(write_json(w.path("j.json"), frames({"tick": 0, "attack": True})))

    def test_live_inputs_keep_fast_tap_edge(self):
        li = LiveInputs()
        li.set(interact=True)
        li.set(interact=False)  # bấm và nhả giữa hai tick: vẫn phải thấy một cạnh lên
        self.assertTrue(li.advance().pressed("interact"))
        self.assertFalse(li.advance().pressed("interact"))
        li.set(move=[1, 1], catch=True)
        st = li.advance()
        self.assertTrue(st.pressed("catch"))
        self.assertAlmostEqual(st.move[0] ** 2 + st.move[1] ** 2, 1.0)

    def test_session_steps_gather_and_dock(self):
        tuning = load_contract()["tuning"]
        s = Session("gather", tuning, {"hold": ["ca_loc"]}, 1)
        self.assertEqual(s.snapshot()["tick"], 0)
        li = LiveInputs()
        self.assertEqual(s.step(li.advance()), [])
        li.set(interact=True)
        rows = s.step(li.advance())
        self.assertEqual([r["name"] for r in rows], ["gather_end"])
        self.assertTrue(s.done)
        self.assertEqual(s.snapshot()["tick"], 2)
        self.assertEqual(s.end_row()["reason"], "docked")


class GatherCore(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]
        self.g = self.tuning["gather"]

    def session(self, player=None, **scenario):
        return Session("gather", self.tuning, {"player": player or {}, **scenario}, 1)

    def step(self, session, move=(0, 0), edges=()):
        return session.step(InputState(move, {}, set(edges)))

    def test_surface_boundary_refills_and_clamps_oxygen(self):
        maximum = round(self.g["oxygen_max_s"] * self.tuning["tick_hz"])
        s = self.session({"pos": [20, self.g["surface_depth"]], "oxygen_ticks": maximum - 1})
        self.assertEqual(self.step(s), [])
        self.assertEqual(s.snapshot()["player"]["oxygen_ticks"], maximum)
        self.assertTrue(s.snapshot()["player"]["at_surface"])
        self.step(s)
        self.assertEqual(s.sim.oxygen_ticks, maximum)

    def test_dive_surface_use_end_position_and_emit_once(self):
        boundary = self.g["surface_depth"]
        s = self.session({"pos": [20, boundary], "oxygen_ticks": 10})
        rows = self.step(s, (0, 1))
        self.assertEqual([r["name"] for r in rows], ["dive"])
        self.assertEqual(s.sim.oxygen_ticks, 9)
        event_pos = list(rows[0]["data"]["pos"])
        self.assertEqual(self.step(s, (0, 1)), [])
        self.assertEqual(rows[0]["data"]["pos"], event_pos)
        for _ in range(self.g["ramp_max_ticks"] + 10):
            rows = self.step(s, (0, -1))
            if rows:
                break
        self.assertEqual([r["name"] for r in rows], ["surface"])
        self.assertLessEqual(s.sim.pos[1], boundary)
        oxygen = s.sim.oxygen_ticks
        self.assertEqual(self.step(s, (0, -1)), [])
        self.assertEqual(s.sim.oxygen_ticks, oxygen + self.g["oxygen_refill_per_tick"])

    def test_oxygen_empty_only_on_positive_to_zero(self):
        s = self.session({"pos": [20, 5], "oxygen_ticks": 1})
        self.assertEqual([r["name"] for r in self.step(s)], ["oxygen_empty"])
        self.assertEqual(s.sim.oxygen_ticks, 0)
        self.assertEqual(self.step(s), [])
        self.assertEqual(s.sim.oxygen_ticks, 0)

    def test_oxygen_refill_reads_tuning(self):
        self.g["oxygen_refill_per_tick"] = 9
        s = self.session({"oxygen_ticks": 0})
        self.step(s)
        self.assertEqual(s.sim.oxygen_ticks, 9)

    def test_choking_starts_on_tick_oxygen_reaches_zero(self):
        s = self.session({"pos": [20, 5], "oxygen_ticks": 1})
        self.step(s)
        self.assertEqual(s.sim.zero_oxy_ticks, 1)
        interval = self.g["choke_interval_ticks"]
        for _ in range(interval - 2):
            self.assertEqual(self.step(s), [])
        self.assertEqual(s.sim.hp, self.g["hp_max"])
        rows = self.step(s)
        self.assertEqual([(r["name"], r["data"]) for r in rows],
                         [("choke", {"hp": self.g["hp_max"] - 1})])
        self.assertEqual(s.sim.zero_oxy_ticks, 0)
        for _ in range(interval - 1):
            self.assertEqual(self.step(s), [])
        self.assertEqual([r["name"] for r in self.step(s)], ["choke"])

    def test_surface_resets_choking_before_damage(self):
        s = self.session({"pos": [20, self.g["surface_depth"] + 0.001],
                          "oxygen_ticks": 0, "zero_oxy_ticks": self.g["choke_interval_ticks"] - 1})
        self.assertEqual([r["name"] for r in self.step(s, (0, -1))], ["surface"])
        self.assertEqual(s.sim.zero_oxy_ticks, 0)
        self.assertEqual(s.sim.hp, self.g["hp_max"])
        self.assertEqual(s.sim.oxygen_ticks, self.g["oxygen_refill_per_tick"])

    def test_faint_clears_hold_before_end_and_precedes_docking_and_time(self):
        s = self.session({"pos": [2, 1], "oxygen_ticks": 0, "hp": 1,
                          "zero_oxy_ticks": self.g["choke_interval_ticks"] - 1},
                         hold=["ca_loc", "bong_sung"], time_left_ticks=1)
        rows = self.step(s, edges=("interact", "catch"))
        self.assertEqual([r["name"] for r in rows], ["choke", "faint", "gather_end"])
        self.assertEqual(rows[1]["data"], {"reason": "fainted"})
        self.assertEqual(rows[2]["data"], {"reason": "fainted", "inventory": {"items": {}}})
        snapshot = s.snapshot()
        self.assertEqual(snapshot["player"]["hp"], 0)
        self.assertEqual(snapshot["hold"], [])
        self.assertEqual(snapshot["hold_count"], 0)
        self.assertEqual(snapshot["state"], "finished")
        self.assertEqual(s.end_row()["reason"], "fainted")

    def test_choke_interval_reads_tuning(self):
        self.g["choke_interval_ticks"] = 2
        s = self.session({"pos": [20, 5], "oxygen_ticks": 0})
        self.assertEqual(self.step(s), [])
        self.assertEqual([r["name"] for r in self.step(s)], ["choke"])

    def test_faint_writes_empty_inventory_through_runner(self):
        from chonoi.inventory import read_inventory
        s = self.session({"pos": [20, 5], "oxygen_ticks": 0, "hp": 1,
                          "zero_oxy_ticks": self.g["choke_interval_ticks"] - 1}, hold=["ca_loc"])
        self.step(s)
        with Workdir() as w:
            path = write_json(w.path("inventory.json"), {"items": {"ca_loc": 3}})
            s.write_inventory_if_done(path)
            self.assertEqual(read_inventory(path), {})

    def test_hold_preserves_pickup_order_and_latest_item_is_last(self):
        original = ["ca_loc", "bong_sung"]
        s = self.session(hold=original)
        self.assertEqual(s.sim._store_in_hold("ca_linh", 3), 3)
        self.assertEqual(s.snapshot()["hold"], original + ["ca_linh"] * 3)
        self.assertEqual(original, ["ca_loc", "bong_sung"])
        self.assertEqual(s.sim.hold.pop(), "ca_linh")
        self.assertEqual(s.sim.inventory_items(), {"bong_sung": 1, "ca_linh": 2, "ca_loc": 1})

    def test_hold_capacity_reads_tuning_and_reports_actual_count(self):
        self.g["hold_capacity"] = 4
        s = self.session(hold=["bong_sung"] * 3)
        self.assertEqual(s.sim._store_in_hold("ca_linh", 3), 1)
        self.assertEqual(s.sim._store_in_hold("ca_loc", 1), 0)
        snapshot = s.snapshot()
        self.assertEqual(snapshot["hold"], ["bong_sung"] * 3 + ["ca_linh"])
        self.assertEqual(snapshot["hold_count"], 4)
        self.assertEqual(snapshot["hold_capacity"], 4)

    def test_snapshot_keeps_player_and_hold_values_after_next_step(self):
        s = self.session(hold=["ca_loc"])
        before = s.snapshot()
        self.step(s, (1, 0))
        s.sim._store_in_hold("bong_sung", 1)
        self.assertEqual(before["hold"], ["ca_loc"])
        self.assertEqual(before["hold_count"], 1)
        self.assertEqual(before["player"]["pos"], self.g["start_pos"])
        self.assertEqual(before["player"]["vel"], [0, 0])

    def test_scenario_accepts_full_hold_and_rejects_over_capacity(self):
        with Workdir() as w:
            hold = ["ca_loc"] * self.g["hold_capacity"]
            path = write_json(w.path("scenario.json"), {"gather": {"hold": hold}})
            self.assertEqual(load_scenario(path, "gather", self.tuning)["hold"], hold)
            write_json(path, {"gather": {"hold": hold + ["ca_loc"]}})
            with self.assertRaises(BadInput):
                load_scenario(path, "gather", self.tuning)


if __name__ == "__main__":
    unittest.main()
