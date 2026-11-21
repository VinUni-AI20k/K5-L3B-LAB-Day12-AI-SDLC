"""Luật quán Phase 1 (lát 3 + lát 4), hộp đen qua headless_cmd. Mỗi test ghi AC tương ứng trong
docs/verification/phase-1.md. Chạy: PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
"""

import json
import os
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

AT_STOVE = [2, 8]
AT_TABLE = [9, 2]
PAY60 = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}


def run_quan(w, scenario, inputs=None, ticks=10, every=1, inventory=None, seed=1):
    args = ["--mode", "quan", "--seed", str(seed), "--ticks", str(ticks), "--out", w.path("q.jsonl"),
            "--snapshot-every", str(every)]
    if scenario is not None:
        args += ["--scenario", write_json(w.path("sc.json"), {"quan": scenario})]
    if inputs is not None:
        args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
    if inventory is not None:
        args += ["--inventory", write_json(w.path("kho.json"), {"items": inventory})]
    code, err = run_headless(*args)
    assert code == 0, err
    return read_jsonl(w.path("q.jsonl"))


def code_of(w, scenario):
    out = w.path("bad.jsonl")
    code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "5", "--out", out,
                           "--scenario", write_json(w.path("bad.json"), {"quan": scenario}))
    return code, os.path.exists(out)


def snap_at(rows, tick):
    return next(s for s in snapshots(rows) if s["tick"] == tick)


def customer(**kw):
    c = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}
    c.update(kw)
    return c


class Lat3KhachGiuChoKienNhan(unittest.TestCase):
    def test_ac_p1_20_customer_arrives_at_first_tick_and_reserves(self):
        with Workdir() as w:
            rows = run_quan(w, {"stock": {"ca_loc": 1, "ca_linh": 2}}, ticks=121, every=200)
            arr = events(rows, "customer_arrived")
            self.assertEqual(len(arr), 1)
            self.assertEqual(arr[0]["tick"], 120)
            self.assertEqual(arr[0]["data"], {"order_id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"})
            c = snapshots(rows)[-1]["customers"][0]
            self.assertEqual((c["order_tick"], c["order_status"], c["reserved"]), (120, "reserved", {"ca_loc": 1}))
            self.assertEqual(c["patience_ticks_left"], 3599)  # đầy lúc đến, giảm từ bước sau
            self.assertEqual(snapshots(rows)[-1]["tables"][0]["customer_id"], "C1")

    def test_ac_p1_21_no_dish_when_nothing_cookable(self):
        with Workdir() as w:
            rows = run_quan(w, {"stock": {"ca_linh": 2}}, ticks=121, every=200)
            self.assertEqual([(e["tick"], e["data"]) for e in events(rows, "no_dish")], [(120, {})])
            self.assertEqual(events(rows, "customer_arrived"), [])

    def test_ac_p1_22_reservation_blocks_second_order_and_table_busy_skips(self):
        """Đổi ở P2: quán có 4 bàn (v1.1), scenario chỉ cập nhật chứ không xóa bàn mặc định; để còn đúng
        tình huống "mọi bàn bận -> bỏ lượt" ta đặt sẵn khách unfulfillable (không giữ gì) ở T2–T4."""
        with Workdir() as w:
            busy = [customer(id=f"C{i}", table_id=f"T{i}", order_status="unfulfillable") for i in (2, 3, 4)]
            sc = {"stock": {"ca_loc": 1}, "customers": busy}
            rows = run_quan(w, sc, ticks=120 + 900 + 1, every=2000)
            self.assertEqual(len(events(rows, "customer_arrived")), 1)  # bàn duy nhất đang có khách -> bỏ lượt
            self.assertEqual(events(rows, "no_dish"), [])

    def test_ac_p1_23_patience_runs_out_reputation_drops(self):
        with Workdir() as w:
            sc = {"stock": {"ca_loc": 1}, "random_customers": False,
                  "customers": [customer(patience_ticks_left=2)]}
            rows = run_quan(w, sc, ticks=5)
            left = events(rows, "customer_left")
            self.assertEqual(left[0]["tick"], 2)
            self.assertEqual(left[0]["data"], {"order_id": "C1", "table_id": "T1", "reason": "patience", "reputation": 2.5})
            s = snap_at(rows, 2)
            self.assertEqual(s["customers"], [])
            self.assertEqual(s["stock"], {"ca_loc": 1})  # nhả phần giữ thô

    def test_ac_p1_24_arrival_choice_is_seeded_and_deterministic(self):
        stock = {"ca_loc": 1, "bong_sung": 2, "ca_linh": 3, "bong_dien_dien": 1}
        picks = set()
        for seed in range(1, 9):
            with Workdir() as w:
                rows = run_quan(w, {"stock": stock}, ticks=120, every=500, seed=seed)
                picks.add(events(rows, "customer_arrived")[0]["data"]["dish_id"])
        self.assertGreater(len(picks), 1)
        outs = []
        for _ in range(2):
            with Workdir() as w:
                run_quan(w, {"stock": stock}, ticks=300, seed=5)
                with open(w.path("q.jsonl"), "rb") as f:
                    outs.append(f.read())
        self.assertEqual(outs[0], outs[1])


class Lat4BepBungPhucVuTien(unittest.TestCase):
    def test_ac_p1_30_cook_pick_flow(self):
        with Workdir() as w:
            sc = {"stock": {"ca_loc": 2}, "random_customers": False, "player": {"pos": AT_STOVE},
                  "customers": [customer()]}
            inputs = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False},
                      {"tick": 361, "interact": True}]
            rows = run_quan(w, sc, inputs, ticks=363, every=400)
            cs = events(rows, "cook_started")[0]
            self.assertEqual(cs["tick"], 1)
            self.assertEqual(cs["data"], {"stove_id": "B1", "order_id": "C1", "dish_id": "ca_loc_nuong_trui",
                                          "items": ["ca_loc"], "base_price": 60})
            self.assertEqual(events(rows, "dish_ready")[0]["tick"], 361)
            picked = events(rows, "dish_picked")[0]
            self.assertEqual(picked["tick"], 362)
            s = snapshots(rows)[-1]
            self.assertEqual(s["hand"], PAY60)
            self.assertEqual(s["stock"], {"ca_loc": 1})
            self.assertEqual(s["stoves"][0]["state"], "idle")
            self.assertEqual(s["customers"][0]["order_status"], "assigned")

    def test_ac_p1_31_serve_with_tip_then_paid(self):
        with Workdir() as w:
            sc = {"random_customers": False, "player": {"pos": AT_TABLE}, "hand": PAY60,
                  "customers": [customer(order_status="assigned")]}
            rows = run_quan(w, sc, [{"tick": 0, "interact": True}], ticks=700, every=1000)
            served = events(rows, "served")[0]
            self.assertEqual(served["data"], {"order_id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                              "patience_ticks_left": 3599, "base_price": 60, "tip": 12})
            paid = events(rows, "paid")[0]
            self.assertEqual(paid["tick"], 601)
            self.assertEqual(paid["data"], {"order_id": "C1", "table_id": "T1", "base_price": 60, "tip": 12,
                                            "amount": 72, "reason": "finished_eating"})
            s = snapshots(rows)[-1]
            self.assertEqual((s["money"], s["earned"]), (72, 72))
            self.assertAlmostEqual(s["reputation"], 3.2, places=2)
            self.assertEqual(s["score"], 72 + 300)

    def test_ac_p1_32_tip_threshold_uses_patience_after_step1(self):
        for patience, tip in ((1801, 12), (1800, 0)):
            with Workdir() as w:
                sc = {"random_customers": False, "player": {"pos": AT_TABLE}, "hand": PAY60,
                      "customers": [customer(order_status="assigned", patience_ticks_left=patience)]}
                rows = run_quan(w, sc, [{"tick": 0, "interact": True}], ticks=1)
                self.assertEqual(events(rows, "served")[0]["data"]["tip"], tip, patience)

    def test_ac_p1_33_wrong_order_or_empty_hand_does_nothing(self):
        with Workdir() as w:
            sc = {"random_customers": False, "player": {"pos": AT_TABLE}, "stock": {"ca_loc": 1},
                  "customers": [customer()]}
            rows = run_quan(w, sc, [{"tick": 0, "interact": True}], ticks=1)
            self.assertEqual(events(rows), [])

    def test_ac_p1_34_stove_beats_table_at_equal_distance(self):
        with Workdir() as w:
            sc = {"random_customers": False, "player": {"pos": [2.5, 8]}, "stock": {"ca_loc": 1},
                  "tables": [{"id": "T1", "pos": [3, 8]}], "customers": [customer()]}
            rows = run_quan(w, sc, [{"tick": 0, "interact": True}], ticks=1)
            self.assertEqual([e["name"] for e in events(rows)], ["cook_started"])

    def test_ac_p1_35_leaving_customer_discards_dish(self):
        with Workdir() as w:
            sc = {"random_customers": False,
                  "stoves": [{"id": "B1", "state": "cooking", "dish": PAY60, "cook_ticks_left": 100}],
                  "customers": [customer(order_status="assigned", patience_ticks_left=1)]}
            rows = run_quan(w, sc, ticks=2)
            self.assertEqual(events(rows, "customer_left")[0]["data"]["reason"], "patience")
            st = snap_at(rows, 1)["stoves"][0]
            self.assertEqual((st["state"], st["dish"]), ("idle", None))

    def test_ac_p1_36_closing_pays_eaters_and_releases_waiters(self):
        with Workdir() as w:
            sc = {"random_customers": False, "time_left_ticks": 1,
                  "customers": [customer(state="eating", order_status="served", eat_ticks_left=300,
                                         base_price=60, tip=12)]}
            rows = run_quan(w, sc, ticks=5)
            paid = events(rows, "paid")[0]["data"]
            self.assertEqual((paid["reason"], paid["amount"]), ("closing", 72))
            end = events(rows, "quan_end")[0]
            self.assertEqual(end["tick"], 1)
            self.assertEqual(end["data"], {"reason": "time", "money": 72, "earned": 72, "shift_earned": 72,
                                           "reputation": 3.2})
            self.assertEqual(rows[-1]["reason"], "time")
        with Workdir() as w:
            sc = {"random_customers": False, "time_left_ticks": 1, "stock": {"ca_loc": 1}, "customers": [customer()]}
            rows = run_quan(w, sc, ticks=5)
            left = events(rows, "customer_left")[0]["data"]
            self.assertEqual((left["reason"], left["reputation"]), ("closing", 3.0))
            self.assertEqual([e["name"] for e in events(rows)], ["customer_left", "quan_end"])

    def test_ac_p1_37_reputation_clamped(self):
        with Workdir() as w:
            sc = {"random_customers": False, "reputation": 0.2, "customers": [customer(patience_ticks_left=1)],
                  "stock": {"ca_loc": 1}}
            rows = run_quan(w, sc, ticks=1)
            self.assertEqual(events(rows, "customer_left")[0]["data"]["reputation"], 0)

    def test_ac_p1_38_inventory_file_feeds_stock(self):
        with Workdir() as w:
            rows = run_quan(w, None, ticks=0, inventory={"bong_sung": 2, "ca_loc": 1})
            self.assertEqual(snapshots(rows)[0]["stock"], {"bong_sung": 2, "ca_loc": 1})
            self.assertEqual((snapshots(rows)[0]["money"], snapshots(rows)[0]["reputation"]), (0, 3.0))


class FixtureMauThuan(unittest.TestCase):
    def test_ac_p1_39_inconsistent_fixtures_exit_2_before_output(self):
        bad = [
            {"stock": {}, "customers": [customer(reserved={"ca_loc": 1})]},                     # giữ quá tồn
            {"stock": {"ca_loc": 2}, "customers": [customer(reserved={"ca_loc": 2})]},          # giữ khác công thức
            {"hand": PAY60, "customers": [customer(order_status="reserved")], "stock": {"ca_loc": 1}},  # tay giữ đơn chưa assigned
            {"customers": [customer(order_status="assigned")]},                                 # assigned không có món
            {"hand": PAY60, "stoves": [{"id": "B1", "state": "ready", "dish": PAY60}],
             "customers": [customer(order_status="assigned")]},                                 # bếp và tay giữ cùng đơn
            {"customers": [customer(state="eating", order_status="served", eat_ticks_left=10)]},  # eating thiếu giá/boa
            {"customers": [customer(dish_id="pho_bo")]},                                        # món ngoài phạm vi
            {"customers": [customer(mood="vui")]},                                              # trường lạ
            {"stoves": [{"id": "B1", "state": "cooking", "dish": PAY60, "cook_ticks_left": 0}],
             "customers": [customer(order_status="assigned")]},                                 # cooking timer 0
        ]
        for sc in bad:
            with Workdir() as w:
                code, wrote = code_of(w, sc)
                self.assertEqual(code, 2, sc)
                self.assertFalse(wrote, sc)

    def test_ac_p1_40_reserved_omitted_is_allocated_or_unfulfillable(self):
        with Workdir() as w:
            sc = {"random_customers": False, "stock": {"ca_loc": 1},
                  "tables": [{"id": "T1", "pos": [9, 2]}],
                  "customers": [customer()]}
            rows = run_quan(w, sc, ticks=0)
            self.assertEqual(snapshots(rows)[0]["customers"][0]["reserved"], {"ca_loc": 1})
        with Workdir() as w:
            rows = run_quan(w, {"random_customers": False, "customers": [customer()]}, ticks=0)
            c = snapshots(rows)[0]["customers"][0]
            self.assertEqual((c["order_status"], c["reserved"]), ("unfulfillable", {}))


class HaiTienTrinh(unittest.TestCase):
    def test_ac_p1_41_gather_then_quan_share_inventory_file(self):
        with Workdir() as w:
            dock = write_json(w.path("dock.json"), {"gather": {"hold": ["ca_loc", "bong_sung", "bong_sung"]}})
            di = write_json(w.path("dock-inputs.json"), {"frames": [{"tick": 0, "interact": True}]})
            code, err = run_headless("--mode", "gather", "--seed", "42", "--scenario", dock, "--inputs", di,
                                     "--ticks", "1", "--out", w.path("g.jsonl"), "--inventory-out", w.path("catch.json"))
            self.assertEqual(code, 0, err)
            with open(w.path("catch.json"), encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {"bong_sung": 2, "ca_loc": 1}})
            code, err = run_headless("--mode", "quan", "--seed", "42", "--inventory", w.path("catch.json"),
                                     "--ticks", "0", "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)
            self.assertEqual(snapshots(read_jsonl(w.path("q.jsonl")))[0]["stock"], {"bong_sung": 2, "ca_loc": 1})


if __name__ == "__main__":
    unittest.main()
