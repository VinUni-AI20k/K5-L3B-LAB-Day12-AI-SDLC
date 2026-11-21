"""Unit test của khung PYTHON trong starter (ids, inputs, Session). Nếu nhóm thay bằng ngôn ngữ khác, XÓA file này
(và viết unit test tương đương bằng ngôn ngữ của nhóm); test hộp đen test_smoke_p1.py vẫn dùng nguyên."""

import unittest

from chonoi.errors import BadInput
from chonoi.ids import IdAllocator, id_key, sort_by_id
from chonoi.contract import load_contract
from chonoi.inputs import InputPlayer, InputState, LiveInputs, load_frames
from chonoi.runner import Session

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


if __name__ == "__main__":
    unittest.main()
