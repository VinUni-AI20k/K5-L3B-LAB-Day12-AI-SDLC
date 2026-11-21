"""Unit test của khung PYTHON trong starter (ids, inputs, Session). Nếu nhóm thay bằng ngôn ngữ khác, XÓA file này
(và viết unit test tương đương bằng ngôn ngữ của nhóm); test hộp đen test_smoke_p1.py vẫn dùng nguyên."""

import copy
import unittest

from chonoi.errors import BadInput
from chonoi.headless import main as headless_main
from chonoi.ids import IdAllocator, id_key, sort_by_id
from chonoi.contract import load_contract
from chonoi.inputs import InputPlayer, LiveInputs, load_frames
from chonoi.runner import Session

from helpers import hold_items, kinds_of, counts_of, Workdir, frames, write_json


class Units(unittest.TestCase):
    def test_burn_extension_requires_matching_contract_setting(self):
        contract = load_contract()
        mismatches = []

        extension_disabled = copy.deepcopy(contract)
        extension_disabled["extensions"] = []
        mismatches.append(extension_disabled)

        setting_disabled = copy.deepcopy(contract)
        setting_disabled["tuning"]["quan"]["burn_s"] = None
        mismatches.append(setting_disabled)

        with Workdir() as w:
            for i, invalid in enumerate(mismatches):
                with self.subTest(case=i), self.assertRaises(BadInput):
                    load_contract(write_json(w.path(f"contract-{i}.json"), invalid))

    def test_headless_runs_declared_burn_extension(self):
        # Mở rộng có mã trong Test Contract được chấm qua headless_cmd -> không được tắt ở headless.
        # Món chín sẵn 1199 tick: tick 1 -> 1200 (vẫn bưng được), tick 2 -> 1201 > 1200 thì cháy.
        self.assertIn("burn", load_contract()["extensions"])
        sc = {"quan": {"random_customers": False, "player": {"pos": [12, 5]}, "stock": [],
                       "stoves": [{"id": "B1", "state": "ready", "ready_ticks": 1199,
                                   "dish": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}}],
                       "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                      "order_status": "assigned", "reserved": []}]}}
        with Workdir() as w:
            out = w.path("out.jsonl")
            result = headless_main(["--mode", "quan", "--seed", "1", "--ticks", "3", "--out", out,
                                    "--scenario", write_json(w.path("sc.json"), sc)])
            self.assertEqual(result, 0)
            import json
            with open(out, encoding="utf-8") as f:
                burnt = [r for r in map(json.loads, f) if r.get("name") == "dish_burnt"]
        self.assertEqual([(r["tick"], r["data"]) for r in burnt],
                         [(2, {"stove_id": "B1", "order_id": "C1", "dish_id": "ca_loc_nuong_trui",
                               "order_status": "unfulfillable"})])

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
        # v1.1 (TICKET-02 mục 4.2): attack/photo/pause/shop_done là nút hợp lệ; mở rộng chưa bật thì sim bỏ qua.
        # Nút lạ vẫn mã 2.
        with Workdir() as w:
            load_frames(write_json(w.path("i.json"), frames({"tick": 0, "catch": True})))
            load_frames(write_json(w.path("a.json"), frames({"tick": 0, "attack": True, "pause": True})))
            with self.assertRaises(BadInput):
                load_frames(write_json(w.path("j.json"), frames({"tick": 0, "jump": True})))
            with self.assertRaises(BadInput):
                load_frames(write_json(w.path("b.json"), frames({"tick": 0, "buy": ""})))

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
        s = Session("gather", tuning, {"hold": hold_items("ca_loc")}, 1)
        self.assertEqual(s.snapshot()["tick"], 0)
        li = LiveInputs()
        self.assertEqual(s.step(li.advance()), [])
        li.set(interact=True)
        rows = s.step(li.advance())
        self.assertEqual([r["name"] for r in rows], ["gather_end"])
        self.assertTrue(s.done)
        self.assertEqual(s.snapshot()["tick"], 2)
        self.assertEqual(s.end_row()["reason"], "docked")


if __name__ == "__main__":
    unittest.main()
