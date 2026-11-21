"""v1.1 (TICKET-02 mục 4.2) — pause ở gather/quan và các trường input mới (pause, shop_done, buy) — TV3.

Luật: xét cạnh pause trước. Bước vào pause chỉ tăng tick ngoài, phát paused, state "paused". Khi còn pause, bỏ qua
cạnh hành động và buy; sim_tick, phase_tick, lịch và timer đứng yên. Cạnh pause kế tiếp phát resumed và chạy
gameplay ngay trong bước đó.
"""

import copy
import os
import subprocess
import sys
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.inputs import InputPlayer, LiveInputs, load_frames
from chonoi.runner import Session

from helpers import ROOT, Workdir, events, frames, headless_cmd, read_jsonl, snapshots, write_json

TUNING = load_contract()["tuning"]
Q = TUNING["quan"]


def player_for(*fr):
    return InputPlayer(list(fr))


def run(*args):
    cmd = headless_cmd()
    if cmd and cmd[0] in ("python3", "python"):
        cmd = [sys.executable, *cmd[1:]]
    p = subprocess.run([*cmd, *args], cwd=ROOT, capture_output=True, text=True)
    return p.returncode, p.stderr


class InputFields(unittest.TestCase):
    def test_pause_shop_done_buy_accepted(self):
        with Workdir() as w:
            fr = load_frames(write_json(w.path("i.json"), frames(
                {"tick": 0, "pause": True}, {"tick": 1, "pause": False, "shop_done": True},
                {"tick": 2, "buy": "oxygen"})))
            self.assertEqual(len(fr), 3)

    def test_bad_types_and_unknown_rejected(self):
        bad = [{"tick": 0, "pause": 1}, {"tick": 0, "shop_done": "yes"}, {"tick": 0, "buy": ""},
               {"tick": 0, "buy": 5}, {"tick": 0, "attack": True}, {"tick": 0, "photo": True}]
        with Workdir() as w:
            for fr in bad:
                with self.subTest(fr=fr), self.assertRaises(BadInput):
                    load_frames(write_json(w.path("i.json"), frames(fr)))

    def test_buy_only_on_declared_frame_and_edges(self):
        pl = player_for({"tick": 1, "buy": "hp", "pause": True}, {"tick": 3, "pause": True})
        self.assertIsNone(pl.advance(0).buy)
        s1 = pl.advance(1)
        self.assertEqual((s1.buy, s1.pressed("pause")), ("hp", True))
        s2 = pl.advance(2)
        self.assertEqual((s2.buy, s2.pressed("pause")), (None, False), "buy không kế thừa, giữ pause không tạo cạnh")
        self.assertFalse(pl.advance(3).pressed("pause"), "vẫn true từ trước -> không có cạnh mới")

    def test_live_inputs_buy_consumed_once(self):
        li = LiveInputs()
        li.set(buy="oxygen", pause=True)
        st = li.advance()
        self.assertEqual((st.buy, st.pressed("pause")), ("oxygen", True))
        self.assertIsNone(li.advance().buy)


class PauseStandalone(unittest.TestCase):
    def test_gather_pause_freezes_everything(self):
        s = Session("gather", TUNING, {"player": {"pos": [20, 5]}}, 1)
        pl = player_for({"tick": 0, "move": [1, 0]}, {"tick": 5, "pause": True}, {"tick": 6, "pause": False},
                        {"tick": 8, "catch": True, "interact": True}, {"tick": 9, "catch": False, "interact": False},
                        {"tick": 10, "pause": True})
        for _ in range(5):
            s.step(pl.advance(s.tick))
        before = copy.deepcopy(s.snapshot())  # snapshot trả tham chiếu tới trạng thái sống của sim
        rows = s.step(pl.advance(s.tick))                       # bước 5: vào pause
        self.assertEqual([(r["name"], r["tick"]) for r in rows], [("paused", 6)])
        for _ in range(4):                                       # bước 6..9: đang pause, có cạnh catch/interact
            self.assertEqual(s.step(pl.advance(s.tick)), [])
        mid = copy.deepcopy(s.snapshot())
        self.assertEqual(mid["state"], "paused")
        self.assertEqual((mid["tick"], mid["sim_tick"], mid["phase_tick"]), (10, 5, 5))
        for k in ("time_left_ticks",):
            self.assertEqual(mid[k], before[k])
        self.assertEqual(mid["player"]["pos"], before["player"]["pos"], "không di chuyển khi pause")
        self.assertEqual(mid["player"]["oxygen_ticks"], before["player"]["oxygen_ticks"], "oxy đứng yên")
        rows = s.step(pl.advance(s.tick))                       # bước 10: resume + chạy gameplay
        self.assertEqual(rows[0]["name"], "resumed")
        after = copy.deepcopy(s.snapshot())
        self.assertEqual((after["state"], after["sim_tick"]), ("playing", 6))
        self.assertEqual(after["time_left_ticks"], before["time_left_ticks"] - 1)
        self.assertNotEqual(after["player"]["pos"], before["player"]["pos"], "gameplay chạy ngay bước resume")

    def test_quan_pause_freezes_cooking_and_patience(self):
        stove = {s["id"]: s["pos"] for s in Q["stoves"]}["B1"]
        c = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_tick": 0, "state": "waiting",
             "order_status": "assigned", "reserved": {}}
        b1 = {"id": "B1", "state": "cooking", "cook_ticks_left": 10,
              "dish": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}}
        s = Session("quan", TUNING, {"player": {"pos": list(stove)}, "random_customers": False,
                                     "customers": [c], "stoves": [b1]}, 1)
        pl = player_for({"tick": 0, "pause": True}, {"tick": 1, "pause": False}, {"tick": 50, "pause": True})
        s.step(pl.advance(s.tick))
        for _ in range(49):
            s.step(pl.advance(s.tick))
        snap = s.snapshot()
        self.assertEqual(snap["stoves"][0]["cook_ticks_left"], 10)
        self.assertEqual(snap["customers"][0]["patience_ticks_left"], c.get("patience_ticks_left", Q["patience_s"] * 60))
        self.assertEqual(snap["time_left_ticks"], Q["duration_s"] * 60)
        s.step(pl.advance(s.tick))
        self.assertEqual(s.snapshot()["stoves"][0]["cook_ticks_left"], 9, "resume chạy gameplay ngay")

    def test_headless_jsonl_pause_and_end_row(self):
        with Workdir() as w:
            inp = write_json(w.path("i.json"), frames({"tick": 2, "pause": True}))
            out = w.path("o.jsonl")
            code, err = run("--mode", "quan", "--seed", "1", "--inputs", inp, "--ticks", "10", "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            self.assertEqual([(r["name"], r["tick"], r["phase"]) for r in events(rows)], [("paused", 3, "quan")])
            last = snapshots(rows)[-1]
            self.assertEqual((last["tick"], last["sim_tick"], last["state"]), (10, 2, "paused"))
            self.assertEqual((rows[-1]["ticks"], rows[-1]["sim_tick"], rows[-1]["reason"]), (10, 2, "tick_limit"))

    def test_days_flag_rejected_outside_day(self):
        with Workdir() as w:
            out = w.path("o.jsonl")
            for args in (["--mode", "gather", "--days", "1"], ["--mode", "quan", "--days", "2"]):
                self.assertEqual(run(*args, "--seed", "1", "--ticks", "0", "--out", out)[0], 2, args)
            self.assertFalse(os.path.exists(out))


if __name__ == "__main__":
    unittest.main()
