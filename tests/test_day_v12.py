"""`--mode day` với kho cá thể v1.2 (TICKET-03): bàn giao cùng tick, id tăng xuyên Ngày, Shop không hao.

Tự bật khi game.contract.json là v1.2 (có tuning.freshness); trước đó skip để main vẫn xanh trong lúc chuyển.
"""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

with open("game.contract.json", encoding="utf-8") as _f:
    _C = json.load(_f)
TUNING = _C["tuning"]
V12 = "freshness" in TUNING
QUAN_T = int(TUNING["quan"]["duration_s"] * 60)
SHOP_OPEN = 1 + QUAN_T
HOLD = [{"id": "I1", "kind": "ca_loc", "fresh": 100}, {"id": "I2", "kind": "bong_sung", "fresh": 100},
        {"id": "I3", "kind": "bong_sung", "fresh": 100}]
G_DECAY = TUNING.get("freshness", {}).get("gather_decay_per_s", 0.5) / 60


def run_day(w, *frs, scenario=None, days=1, ticks=60000):
    args = ["--mode", "day", "--seed", "1", "--days", str(days), "--ticks", str(ticks), "--out", w.path("d.jsonl")]
    if scenario is not None:
        args += ["--scenario", write_json(w.path("sc.json"), scenario)]
    if frs:
        args += ["--inputs", write_json(w.path("in.json"), frames(*frs))]
    code, err = run_headless(*args)
    return code, err, (read_jsonl(w.path("d.jsonl")) if code == 0 else [])


def ids_kinds(items):
    return [(it["id"], it["kind"]) for it in items]


@unittest.skipUnless(V12, "manifest chưa bật contract v1.2")
class DayV12(unittest.TestCase):
    def _dock_two_days(self, w):
        sc = {"gather": {"hold": HOLD, "random_fish": False, "monsters": []}}
        return run_day(w, {"tick": 0, "interact": True}, {"tick": 1, "interact": False},
                       {"tick": SHOP_OPEN + 5, "shop_done": True}, {"tick": SHOP_OPEN + 6, "interact": True},
                       {"tick": SHOP_OPEN + 7, "interact": False}, scenario=sc, days=2)

    def test_handoff_same_tick_no_extra_decay(self):
        with Workdir() as w:
            code, err, rows = self._dock_two_days(w)
            self.assertEqual(code, 0, err)
            inv = [e for e in events(rows, "gather_end") if e["day"] == 1][0]["data"]["inventory"]["items"]
            self.assertEqual(ids_kinds(inv), [("I1", "ca_loc"), ("I2", "bong_sung"), ("I3", "bong_sung")])
            for it in inv:  # 1 bước gather: hao một lần
                self.assertAlmostEqual(it["fresh"], 100 - G_DECAY, delta=0.01)
            quan0 = [s for s in snapshots(rows) if s["day"] == 1 and s["phase"] == "quan" and s["phase_tick"] == 0][0]
            self.assertEqual(quan0["stock"], inv, "quán tick 0 nhận đúng id + độ tươi, không hao thêm")

    def test_ids_continue_across_days(self):
        with Workdir() as w:
            code, err, rows = self._dock_two_days(w)
            self.assertEqual(code, 0, err)
            g2 = [s for s in snapshots(rows) if s["day"] == 2 and s["phase"] == "gather"][0]
            self.assertEqual(ids_kinds(g2["hold"]), [("I4", "ca_loc"), ("I5", "bong_sung"), ("I6", "bong_sung")])
            self.assertTrue(all(it["fresh"] == 100 for it in g2["hold"]), "Ngày kế: kind/fresh như mẫu")

    def test_shop_stock_does_not_decay(self):
        with Workdir() as w:
            sc = {"gather": {"hold": HOLD, "random_fish": False, "monsters": []}, "quan": {"random_customers": False}}
            code, err, rows = run_day(w, {"tick": 0, "interact": True}, scenario=sc)
            self.assertEqual(code, 0, err)
            shop = [s for s in snapshots(rows) if s["phase"] == "shop"]
            self.assertGreater(len(shop), 2)
            self.assertTrue(all(isinstance(s["stock"], list) for s in shop))
            self.assertEqual(shop[0]["stock"], shop[-1]["stock"])

    def test_faint_hands_empty_list(self):
        with Workdir() as w:
            sc = {"gather": {"player": {"pos": [20, 5], "oxygen_ticks": 0, "hp": 1, "zero_oxy_ticks": 59},
                             "hold": HOLD, "random_fish": False, "monsters": []}}
            code, err, rows = run_day(w, scenario=sc, ticks=3)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "gather_end")[0]["data"]["inventory"], {"items": []})
            self.assertEqual([s for s in snapshots(rows) if s["phase"] == "quan"][0]["stock"], [])


if __name__ == "__main__":
    unittest.main()
