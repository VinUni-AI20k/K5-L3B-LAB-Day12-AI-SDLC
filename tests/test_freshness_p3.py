"""QA Phase 3 (hungdt31): độ tươi & kho cá thể v1.2 chạy qua headless (hộp đen).

Bổ sung phần chưa có test: hao ở gather, ngưỡng 30 ở gather, id cá thể mới, kho đếm cũ → mã 2,
nối kho giữ nguyên id/fresh, hàng ươn không dùng được ở quán, pause không làm hao.
Số liệu đọc từ game.contract.json; kỳ vọng tính bằng Fraction để không lệch ở ngưỡng.
"""

import copy
import json
import unittest
from fractions import Fraction

from chonoi.contract import load_contract
from chonoi.inputs import BUTTONS_V11, InputPlayer, InputState
from chonoi.runner import Session

from helpers import Workdir, events, frames, items, read_jsonl, run_headless, snapshots, write_json

T = load_contract()["tuning"]
F = T["freshness"]
HZ = T["tick_hz"]
G_STEP = Fraction(str(F["gather_decay_per_s"])) / HZ   # 0.5/60 mỗi tick
Q_STEP = Fraction(str(F["quan_decay_per_s"])) / HZ     # 0.25/60 mỗi tick
SPOIL = F["spoiled_below"]                             # 30


def _gather(w, scenario, ticks, *fr, inventory_out=None, every=1):
    sc = write_json(w.path("sc.json"), {"gather": scenario})
    args = ["--mode", "gather", "--seed", "1", "--ticks", str(ticks), "--scenario", sc,
            "--snapshot-every", str(every), "--out", w.path("g.jsonl")]
    if fr:
        args += ["--inputs", write_json(w.path("in.json"), frames(*fr))]
    if inventory_out:
        args += ["--inventory-out", inventory_out]
    code, err = run_headless(*args)
    return code, err, read_jsonl(w.path("g.jsonl")) if code == 0 else []


class GatherFreshness(unittest.TestCase):
    def test_hold_decays_each_tick_and_spoils_strictly_below_threshold_once(self):
        # Cần đúng bao nhiêu tick để từ SPOIL+1 rơi về SPOIL (= 30.0, còn dùng được), tick sau thì ươn.
        n = int(Fraction(1) / G_STEP)  # 120
        with Workdir() as w:
            code, err, rows = _gather(w, {"hold": items("bong_sung", fresh=SPOIL + 1), "random_fish": False},
                                      n + 30)
            self.assertEqual(code, 0, err)
            by_tick = {s["tick"]: s for s in snapshots(rows)}
            self.assertEqual(by_tick[0]["hold"][0]["fresh"], SPOIL + 1)
            self.assertAlmostEqual(by_tick[1]["hold"][0]["fresh"], float(SPOIL + 1 - G_STEP), places=9)
            self.assertEqual(by_tick[n]["hold"][0]["fresh"], SPOIL)  # đúng 30: chưa ươn
            spoiled = events(rows, "spoiled")
            self.assertEqual([(e["tick"], e["data"]) for e in spoiled],
                             [(n + 1, {"item_id": "I1", "kind": "bong_sung", "location": "hold"})])

    def test_harvest_new_item_gets_next_id_full_freshness_and_decays_from_next_step(self):
        n1 = next(n for n in T["gather"]["nodes"] if n["id"] == "N1")
        with Workdir() as w:
            code, err, rows = _gather(w, {"hold": items("ca_loc", "ca_linh"), "random_fish": False,
                                          "player": {"pos": n1["pos"]}},
                                      3, {"tick": 0, "interact": True})
            self.assertEqual(code, 0, err)
            by_tick = {s["tick"]: s for s in snapshots(rows)}
            new = by_tick[1]["hold"][-1]
            # id cá thể tiếp nối sau id lớn nhất trong scenario, độ tươi khởi điểm theo contract
            self.assertEqual((new["id"], new["kind"], new["fresh"]), ("I3", n1["kind"], F["initial"]))
            self.assertAlmostEqual(by_tick[2]["hold"][-1]["fresh"], float(F["initial"] - G_STEP), places=9)
            # hàng cũ vẫn hao ở bước nhặt
            self.assertAlmostEqual(by_tick[1]["hold"][0]["fresh"], float(100 - G_STEP), places=9)

    def test_inventory_roundtrip_keeps_ids_and_freshness_into_quan(self):
        with Workdir() as w:
            inv = w.path("kho.json")
            code, err, _ = _gather(w, {"hold": items("ca_loc", "bong_sung", fresh=80)}, 2,
                                   {"tick": 1, "interact": True}, inventory_out=inv)
            self.assertEqual(code, 0, err)
            with open(inv, encoding="utf-8") as f:
                saved = json.load(f)
            self.assertEqual(set(saved), {"items"})
            self.assertEqual([(x["id"], x["kind"]) for x in saved["items"]], [("I1", "ca_loc"), ("I2", "bong_sung")])
            for x in saved["items"]:
                self.assertAlmostEqual(x["fresh"], float(80 - 2 * G_STEP), places=9)
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", inv,
                                     "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)
            self.assertEqual(snapshots(read_jsonl(w.path("q.jsonl")))[0]["stock"], saved["items"])


class V12SchemaRejectsOldFormats(unittest.TestCase):
    def test_counted_inventory_and_string_hold_and_counted_stock_exit_2(self):
        with Workdir() as w:
            inv = write_json(w.path("inv.json"), {"items": {"ca_loc": 1}})
            self.assertEqual(run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", inv,
                                          "--out", w.path("q.jsonl"))[0], 2)
            for mode, block in (("gather", {"gather": {"hold": ["ca_loc"]}}),
                                ("quan", {"quan": {"stock": {"ca_loc": 1}}}),
                                ("gather", {"gather": {"hold": items("ca_loc") + items("ca_linh")}})):  # id trùng I1
                sc = write_json(w.path("sc.json"), block)
                self.assertEqual(run_headless("--mode", mode, "--seed", "1", "--ticks", "0", "--scenario", sc,
                                              "--out", w.path("o.jsonl"))[0], 2, block)


class QuanFreshness(unittest.TestCase):
    def test_spoiled_stock_is_kept_but_never_served(self):
        # Chỉ có 1 cá lóc đã ươn: khách đến thì không có món (no_dish), cá ươn vẫn nằm trong kho.
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"quan": {"stock": items("ca_loc", fresh=SPOIL - 1)}})
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks",
                                     str(T["quan"]["first_customer_tick"] + 1), "--scenario", sc,
                                     "--snapshot-every", "1", "--out", w.path("q2.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("q2.jsonl"))
            self.assertEqual([e["name"] for e in events(rows) if e["name"] in ("customer_arrived", "no_dish")],
                             ["no_dish"])
            self.assertEqual([x["id"] for x in snapshots(rows)[-1]["stock"]], ["I1"])

    def test_quan_decays_slower_than_gather(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"quan": {"stock": items("ca_loc", fresh=90), "random_customers": False}})
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", str(HZ), "--scenario", sc,
                                     "--snapshot-every", str(HZ), "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)
            last = snapshots(read_jsonl(w.path("q.jsonl")))[-1]
            self.assertAlmostEqual(last["stock"][0]["fresh"], float(90 - HZ * Q_STEP), places=9)  # 89.75


class DayItemIdsAcrossDays(unittest.TestCase):
    def test_gather_allocates_new_item_ids_on_day2_without_reusing_day1_ids(self):
        # Chạy gather THẬT trong day (không chỉ _prepare_gather_scenario): mỗi Ngày hái 1 nút ở bước đầu.
        # Giỏ mẫu rỗng (như chơi thật): trước bản sửa, Ngày 2 cấp lại "I1" vì gather dùng IdAllocator mới.
        n1 = next(n for n in T["gather"]["nodes"] if n["id"] == "N1")
        sc = {"gather": {"random_fish": False,
                         "player": {"pos": n1["pos"]}, "time_left_ticks": 3},
              "quan": {"time_left_ticks": 1, "random_customers": False}}
        sess = Session("day", copy.deepcopy(T), sc, 1, days=2)
        sess.initial_events()
        ends, prev = [], None
        for _ in range(50):
            if sess.done:
                break
            sn = sess.snapshot()
            want = "interact" if sn["phase"] == "gather" and sn["phase_tick"] == 0 else (
                "shop_done" if sn["phase"] == "shop" else None)
            edge = {want} if want and want != prev else set()
            prev = want
            held = {b: (b == want) for b in BUTTONS_V11}
            for e in sess.step(InputState((0.0, 0.0), held, edge)):
                if e["name"] == "gather_end":
                    ends.append([x["id"] for x in e["data"]["inventory"]["items"]])
        self.assertEqual(len(ends), 2)
        self.assertEqual(ends, [["I1"], ["I2"]])  # id họ I nối tiếp xuyên Ngày, không dùng lại


class PauseFreezesFreshness(unittest.TestCase):
    def test_pause_in_day_gather_does_not_decay_hold_and_resume_decays_same_step(self):
        sess = Session("day", copy.deepcopy(T),
                       {"gather": {"hold": items("ca_loc", fresh=50), "random_fish": False}}, 1, days=1)
        sess.initial_events()
        # Bước 0: cạnh pause -> vào pause. Bước 1: nhả nút (không có cạnh). Bước 40: cạnh -> resumed + chạy gameplay.
        ip = InputPlayer([{"tick": 0, "pause": True}, {"tick": 1, "pause": False}, {"tick": 40, "pause": True}],
                         buttons=BUTTONS_V11)
        for k in range(40):
            sess.step(ip.advance(k))
        snap = sess.snapshot()
        self.assertEqual(snap["state"], "paused")
        self.assertEqual(snap["hold"][0]["fresh"], 50)  # 40 bước pause: không hao
        evs = sess.step(ip.advance(40))
        self.assertIn("resumed", [e["name"] for e in evs])
        self.assertAlmostEqual(sess.snapshot()["hold"][0]["fresh"], float(50 - G_STEP), places=9)


if __name__ == "__main__":
    unittest.main()
