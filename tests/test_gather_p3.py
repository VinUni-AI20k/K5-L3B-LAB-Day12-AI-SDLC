"""Phase 3 — Độ tươi ở gather (TICKET-03 Test Contract v1.2 §1). Hộp đen qua headless_cmd + đơn vị GatherSim.
Chạy: PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
"""

import json
import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim
from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

TUNING = load_contract()["tuning"]


def H(*kinds, fresh=100):
    return [{"id": f"I{i}", "kind": k, "fresh": fresh} for i, k in enumerate(kinds, start=1)]


def run_gather(w, scenario, inputs=None, ticks=1, inv_out=False):
    sc = write_json(w.path("sc.json"), {"gather": scenario})
    args = ["--mode", "gather", "--seed", "1", "--scenario", sc, "--ticks", str(ticks),
            "--out", w.path("g.jsonl"), "--snapshot-every", "1"]
    if inputs is not None:
        args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
    if inv_out:
        args += ["--inventory-out", w.path("kho.json")]
    code, err = run_headless(*args)
    assert code == 0, err
    return read_jsonl(w.path("g.jsonl"))


class Inp:
    def __init__(self, edges=()):
        self.move = (0.0, 0.0)
        self._e = set(edges)

    def pressed(self, name):
        return name in self._e


def make(sc, ids=None):
    return GatherSim(TUNING, dict({"random_fish": False, "monsters": [], "nodes": []}, **sc), Streams(1),
                     ids or IdAllocator())


class DoTuoiGather(unittest.TestCase):
    def test_ac_p3_01_threshold_fixture_spoils_at_tick_1(self):
        """Fixture chuẩn: fresh đúng 30, một bước không input → spoiled tick 1, location hold."""
        with Workdir() as w:
            rows = run_gather(w, {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30}],
                                  "random_fish": False, "monsters": []}, ticks=1)
            sp = events(rows, "spoiled")
            self.assertEqual(len(sp), 1)
            self.assertEqual(sp[0]["tick"], 1)
            self.assertEqual(sp[0]["phase"], "gather")
            self.assertEqual(sp[0]["data"], {"item_id": "I1", "kind": "ca_linh", "location": "hold"})
            # ươn vẫn chiếm ô
            self.assertEqual(snapshots(rows)[-1]["hold_count"], 1)

    def test_ac_p3_02_decay_half_per_second_exact_over_60_ticks(self):
        s = make({"hold": H("ca_loc")})
        for _ in range(60):
            s.step(Inp())
        self.assertEqual(s.snapshot()["hold"][0]["fresh"], 99.5)
        self.assertEqual(s.hold[0]["units"], 24000 - 120)

    def test_ac_p3_03_spoiled_exactly_once_and_in_id_order(self):
        s = make({"hold": [{"id": "I2", "kind": "ca_loc", "fresh": 30},
                           {"id": "I1", "kind": "ca_linh", "fresh": 30},
                           {"id": "I3", "kind": "ca_keo", "fresh": 29}]})  # I3 đã ươn sẵn: không phát
        evs = s.step(Inp())
        self.assertEqual([(n, d["item_id"]) for n, d in evs if n == "spoiled"], [("spoiled", "I1"), ("spoiled", "I2")])
        for _ in range(100):
            self.assertEqual([e for e in s.step(Inp()) if e[0] == "spoiled"], [])

    def test_ac_p3_04_decay_clamped_at_zero(self):
        s = make({"hold": H("ca_loc", fresh=0.001)})
        s.step(Inp())
        self.assertEqual(s.hold[0]["units"], 0)
        self.assertEqual(s.snapshot()["hold"][0]["fresh"], 0)

    def test_ac_p3_05_new_item_fresh_100_decays_from_next_step(self):
        s = make({"player": {"pos": [30, 10]}, "fish": [{"id": "F1", "kind": "ca_loc", "pos": [31, 10]}]})
        s.step(Inp(edges={"catch"}))
        self.assertEqual(s.snapshot()["hold"], [{"id": "I1", "kind": "ca_loc", "fresh": 100}])
        s.step(Inp())
        self.assertAlmostEqual(s.snapshot()["hold"][0]["fresh"], 100 - 1 / 120, places=12)

    def test_ac_p3_06_ids_in_pick_order_continue_after_scenario_and_shared_allocator(self):
        ids = IdAllocator()
        s = make({"player": {"pos": [30, 10]}, "hold": [{"id": "I7", "kind": "ca_loc", "fresh": 50}],
                  "fish": [{"id": "F1", "kind": "ca_linh", "pos": [31, 10]}]}, ids)
        s.step(Inp(edges={"catch"}))
        self.assertEqual([i["id"] for i in s.snapshot()["hold"]], ["I7", "I8", "I9", "I10"])
        # Ngày kế dùng chung IdAllocator: id tiếp tục tăng; reissue cấp id mới theo thứ tự mảng
        s2 = GatherSim(TUNING, {"random_fish": False, "monsters": [], "nodes": [], "hold": H("ca_keo", "keo_neo")},
                       Streams(1), ids, reissue_hold_ids=True)
        self.assertEqual([(i["id"], i["kind"]) for i in s2.snapshot()["hold"]], [("I11", "ca_keo"), ("I12", "keo_neo")])

    def test_ac_p3_07_lost_arrays_lifo_items(self):
        croc = {"id": "M1", "kind": "ca_sau", "pos": [61, 24], "waypoints": [[61, 24], [65, 24]]}
        s = make({"monsters": [croc], "player": {"pos": [60, 24]},
                  "hold": H("ca_loc", "bong_sung", "ca_linh", "keo_neo")})
        evs = s.step(Inp())
        hit = [d for n, d in evs if n == "monster_hit"][0]
        self.assertEqual([i["id"] for i in hit["lost"]], ["I4", "I3"])
        self.assertTrue(all(set(i) == {"id", "kind", "fresh"} for i in hit["lost"]))
        self.assertAlmostEqual(hit["lost"][0]["fresh"], 100 - 1 / 120, places=12)  # hao ở đầu bước trước hit

    def test_ac_p3_08_faint_writes_empty_items(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 10], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 1},
                                  "hold": H("ca_loc", "ca_linh"), "nodes": [], "random_fish": False,
                                  "monsters": []}, ticks=5, inv_out=True)
            faint = events(rows, "faint")[0]["data"]
            self.assertEqual([i["id"] for i in faint["lost"]], ["I2", "I1"])
            self.assertEqual(events(rows, "gather_end")[0]["data"]["inventory"], {"items": []})
            with open(w.path("kho.json"), encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": []})

    def test_ac_p3_09_scenario_hold_validation_code_2(self):
        bad = [
            ["ca_loc"],  # schema đếm/kind cũ
            [{"id": "I1", "kind": "ca_loc"}],
            [{"id": "I1", "kind": "ca_ho", "fresh": 50}],
            [{"id": "I1", "kind": "ca_loc", "fresh": 101}],
            [{"id": "I1", "kind": "ca_loc", "fresh": -1}],
            [{"id": "I1", "kind": "ca_loc", "fresh": 50}, {"id": "I1", "kind": "ca_linh", "fresh": 50}],
            [{"id": "", "kind": "ca_loc", "fresh": 50}],
            [{"id": "I1", "kind": "ca_loc", "fresh": True}],
        ]
        with Workdir() as w:
            for h in bad:
                sc = write_json(w.path("sc.json"), {"gather": {"hold": h, "random_fish": False}})
                code, _ = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1", "--scenario", sc,
                                       "--out", w.path("g.jsonl"))
                self.assertEqual(code, 2, h)

    def test_ac_p3_10_dock_handover_file_exact(self):
        """Smoke bàn giao: fresh 100, interact frame 0 cập bến → file giữ fresh sau một lần hao."""
        with Workdir() as w:
            rows = run_gather(w, {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 100}], "random_fish": False,
                                  "monsters": []}, [{"tick": 0, "interact": True}], ticks=1, inv_out=True)
            self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "docked")
            with open(w.path("kho.json"), encoding="utf-8") as f:
                saved = json.load(f)
            self.assertEqual(saved["items"][0]["id"], "I1")
            self.assertEqual(round(saved["items"][0]["fresh"] * 240), 24000 - 2)
            self.assertEqual(saved["items"][0]["fresh"] * 240, 23998)


if __name__ == "__main__":
    unittest.main()
