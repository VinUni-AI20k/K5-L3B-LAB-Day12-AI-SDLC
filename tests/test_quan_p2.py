"""Test Quán Phase 2 (TICKET-02, Test Contract v1.1): 2 bếp / 4 bàn, 6 món, kế hoạch Ngày.

Chạy: PYTHONPATH=tests:. python3 -m unittest discover -s tests -p "test_quan_p2.py" -v
(Windows: PYTHONPATH="tests;.")
"""

import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim
from test_quan import stock_items

# P3 [THAY THẾ]: fixtures kho cá thể và giữ chỗ bằng id thay kho đếm.

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

TUNING = load_contract()["tuning"]
NO_INPUT = InputState((0.0, 0.0), {}, set())


def run_quan(w, scenario=None, inputs=None, ticks=1, inventory=None, name="q"):
    args = ["--mode", "quan", "--seed", "1", "--ticks", str(ticks), "--out", w.path(f"{name}.jsonl")]
    if scenario is not None:
        args += ["--scenario", write_json(w.path(f"{name}-sc.json"), {"quan": scenario})]
    if inputs is not None:
        args += ["--inputs", write_json(w.path(f"{name}-in.json"), frames(*inputs))]
    if inventory is not None:
        args += ["--inventory", write_json(w.path(f"{name}-inv.json"), {"items": stock_items(inventory)})]
    code, err = run_headless(*args)
    return code, err, (read_jsonl(w.path(f"{name}.jsonl")) if code == 0 else None)


def sim(stock, plan_dishes=None, carry=None, scenario=None):
    sc = dict(scenario or {}, stock=stock_items(stock))
    return QuanSim(TUNING, sc, Streams(1), IdAllocator(), plan_dishes=plan_dishes, carry=carry)


def step_until(s, phase_tick):
    out = []
    while s.phase_tick < phase_tick:
        out += s.step(NO_INPUT)
    return out


class StandardData(unittest.TestCase):
    """Mục 1.3 TICKET-02: số chuẩn quán, thực đơn 6 món, kế hoạch 5 Ngày."""

    def test_bep_ban_chuan(self):
        q = TUNING["quan"]
        self.assertEqual([(s["id"], s["pos"]) for s in q["stoves"]], [("B1", [2, 8]), ("B2", [5, 8])])
        self.assertEqual([(t["id"], t["pos"]) for t in q["tables"]],
                         [("T1", [9, 2]), ("T2", [13, 2]), ("T3", [9, 6]), ("T4", [13, 6])])

    def test_thuc_don_6_mon(self):
        menu = {k: (v["recipe"], v["cook_s"], v["price"]) for k, v in TUNING["menu"].items()}
        self.assertEqual(menu, {
            "ca_loc_nuong_trui": ({"ca_loc": 1}, 6, 60),
            "goi_bong_sung": ({"bong_sung": 2}, 4, 40),
            "lau_ca_linh_dien_dien": ({"ca_linh": 3, "bong_dien_dien": 1}, 10, 120),
            "canh_chua_ca_loc": ({"ca_loc": 1, "bong_dien_dien": 1}, 8, 90),
            "ca_keo_nuong": ({"ca_keo": 2}, 6, 70),
            "lau_mam": ({"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1}, 12, 200),
        })

    def test_ke_hoach_5_ngay(self):
        plan = TUNING["day_plan"]
        self.assertEqual([p["day"] for p in plan], [1, 2, 3, 4, 5])
        self.assertEqual(plan[0]["dishes"], {"ca_loc_nuong_trui": 3, "goi_bong_sung": 3})
        self.assertEqual(plan[0]["ingredients"], {"ca_loc": 3, "bong_sung": 6})
        self.assertEqual(sum(plan[3]["ingredients"].values()), 9)   # D4: 9 ô (11 nếu bắt đàn)
        self.assertEqual(sum(plan[4]["ingredients"].values()), 10)  # D5: 10 ô


class StandaloneQuan(unittest.TestCase):
    def test_snapshot_co_2_bep_4_ban(self):
        with Workdir() as w:
            code, err, rows = run_quan(w, ticks=0)
            self.assertEqual(code, 0, err)
            s = snapshots(rows)[0]
            self.assertEqual([x["id"] for x in s["stoves"]], ["B1", "B2"])
            self.assertEqual([x["id"] for x in s["tables"]], ["T1", "T2", "T3", "T4"])
            self.assertTrue(all(x["customer_id"] is None for x in s["tables"]))

    def test_kho_nhan_ca_keo_keo_neo_va_quan_rieng_dung_ca_6_mon(self):
        """Chỉ đủ nguyên liệu cho lẩu mắm (món mới) -> khách gọi đúng món đó."""
        with Workdir() as w:
            inv = {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1}
            code, err, rows = run_quan(w, ticks=120, inventory=inv)
            self.assertEqual(code, 0, err)
            self.assertEqual(snapshots(rows)[0]["stock"], stock_items(inv))
            arr = events(rows, "customer_arrived")
            self.assertEqual(arr[0]["data"], {"order_id": "C1", "table_id": "T1", "dish_id": "lau_mam"})

    def test_khach_thu_hai_ngoi_ban_trong_tiep_theo(self):
        with Workdir() as w:
            code, err, rows = run_quan(w, ticks=1020, inventory={"ca_keo": 4})
            self.assertEqual(code, 0, err)
            arr = [(e["tick"], e["data"]["table_id"], e["data"]["dish_id"]) for e in events(rows, "customer_arrived")]
            self.assertEqual(arr, [(120, "T1", "ca_keo_nuong"), (1020, "T2", "ca_keo_nuong")])

    def test_bep_B2_nau_khi_B1_dang_ban(self):
        cook = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}
        sc = {"random_customers": False, "stock": stock_items({"ca_keo": 2}), "player": {"pos": [5, 7]},
              "stoves": [{"id": "B1", "state": "cooking", "dish": cook, "cook_ticks_left": 100}],
              "customers": [
                  {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "assigned"},
                  {"id": "C2", "table_id": "T2", "dish_id": "ca_keo_nuong", "order_tick": 5}]}
        with Workdir() as w:
            code, err, rows = run_quan(w, sc, [{"tick": 0, "interact": True}], ticks=1)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "cook_started")[0]["data"],
                             {"stove_id": "B2", "order_id": "C2", "dish_id": "ca_keo_nuong",
                              "items": stock_items({"ca_keo": 2}, 1), "base_price": 69})


class DayHooks(unittest.TestCase):
    """Giao diện cho mode `day` (lát day/Shop gọi): lọc món theo kế hoạch, mang tiền/uy tín qua Ngày."""

    def test_loc_mon_theo_ke_hoach_truoc_khi_xet_nguyen_lieu(self):
        # Đủ cả cá lóc nướng lẫn gỏi, nhưng kế hoạch chỉ có gỏi -> khách gọi gỏi.
        s = sim({"ca_loc": 5, "bong_sung": 2}, plan_dishes=["goi_bong_sung"])
        ev = step_until(s, 120)
        self.assertEqual(ev, [("customer_arrived", {"order_id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung"})])

    def test_mon_ngoai_ke_hoach_khong_tinh_nen_no_dish(self):
        s = sim({"ca_loc": 5}, plan_dishes=["goi_bong_sung"])
        self.assertEqual(step_until(s, 120), [("no_dish", {})])

    def test_khach_goi_tiep_khi_da_ban_du_so_suat(self):
        """Số suất chỉ để tính mục tiêu thu gom: còn nguyên liệu thì vẫn gọi tiếp."""
        plan = TUNING["day_plan"][0]["dishes"]  # D1: ca_loc_nuong_trui x3, goi x3
        s = sim({"ca_loc": 10}, plan_dishes=list(plan))
        for c in range(4):
            s.customers.append({"id": f"X{c}", "table_id": f"T{c + 1}", "dish_id": "ca_loc_nuong_trui",
                                "order_tick": 0, "state": "eating", "patience_ticks_left": 0,
                                "eat_ticks_left": 1, "order_status": "served", "reserved": [],
                                "base_price": 60, "tip": 0})
        step_until(s, 1)  # 4 khách ăn xong, trả tiền, bàn trống
        ev = step_until(s, 120)
        self.assertEqual([e[1]["dish_id"] for e in ev if e[0] == "customer_arrived"], ["ca_loc_nuong_trui"])

    def test_mang_tien_uy_tin_tu_ngay_truoc(self):
        s = sim({}, carry={"money": 150, "earned": 380, "reputation": 4.2})
        self.assertEqual((s.money, s.earned, s.shift_earned, s.reputation), (150, 380, 0, 4.2))
        s.customers.append({"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "order_tick": 0,
                            "state": "eating", "patience_ticks_left": 3000, "eat_ticks_left": 1,
                            "order_status": "served", "reserved": [], "base_price": 40, "tip": 8})
        ev = step_until(s, 1)
        self.assertEqual(ev[0][0], "paid")
        self.assertEqual((s.money, s.earned, s.shift_earned, s.reputation), (198, 428, 48, 4.4))

    def test_mac_dinh_quan_rieng_khong_doi(self):
        s = sim({})
        self.assertEqual((s.money, s.earned, s.reputation), (0, 0, TUNING["quan"]["reputation_initial"]))
        self.assertEqual(s.dish_pool, sorted(TUNING["menu"]))


# P3 [THAY THẾ]: hao kho kể cả phần giữ; giữ theo id; giá theo tươi lúc bắt đầu nấu.
class FreshStock(unittest.TestCase):
    @staticmethod
    def item(ident, kind="ca_loc", fresh=100):
        return {"id": ident, "kind": kind, "fresh": fresh}

    @staticmethod
    def order(ident="C1", table="T1", dish="ca_loc_nuong_trui", **updates):
        return dict(id=ident, table_id=table, dish_id=dish, **updates)

    def make_sim(self, items, orders=(), **updates):
        return QuanSim(TUNING, dict(stock=items, customers=list(orders), random_customers=False, **updates),
                       Streams(1), IdAllocator())

    def test_decay_quarter_per_second_including_reserved(self):
        s = self.make_sim([self.item("I1"), self.item("I2")], [self.order()])
        step_until(s, 60)
        self.assertEqual([it["fresh_u"] for it in s.stock], [23940, 23940])
        self.assertEqual([it["fresh"] for it in s.snapshot()["stock"]], [99.75, 99.75])
        self.assertEqual(s.customers[0]["reserved"], ["I1"])

    def test_spoiled_exact_boundary_id_order_once_and_floor_zero(self):
        s = self.make_sim([self.item("I10", fresh=30), self.item("I2", fresh=30),
                           self.item("I1", fresh=0), self.item("I3", fresh=29)])
        self.assertEqual(s.step(NO_INPUT), [
            ("spoiled", {"item_id": "I2", "kind": "ca_loc", "location": "stock"}),
            ("spoiled", {"item_id": "I10", "kind": "ca_loc", "location": "stock"})])
        self.assertEqual(s.stock[0]["fresh_u"], 0)
        self.assertEqual(s.step(NO_INPUT), [])
        self.assertEqual(s.stock[0]["fresh_u"], 0)

    def test_reserve_freshest_then_natural_id_excludes_spoiled(self):
        s = self.make_sim([self.item("I10", fresh=90), self.item("I2", fresh=90),
                           self.item("I1", fresh=29), self.item("I3", fresh=80)], [self.order()])
        self.assertEqual(s.customers[0]["reserved"], ["I2"])

    def test_missing_reserved_inferred_by_order_then_table(self):
        orders = [self.order("C1", "T1", order_tick=1), self.order("C3", "T3", order_tick=0),
                  self.order("C2", "T2", order_tick=0)]
        s = self.make_sim([self.item("I1", fresh=90), self.item("I2", fresh=80), self.item("I3", fresh=70)], orders)
        self.assertEqual({c["id"]: c["reserved"] for c in s.customers},
                         {"C2": ["I1"], "C3": ["I2"], "C1": ["I3"]})

    def test_explicit_reserved_protected_from_inference(self):
        s = self.make_sim([self.item("I1"), self.item("I2", fresh=90)],
                          [self.order("C1", "T1"), self.order("C2", "T2", reserved=["I1"])])
        self.assertEqual(s.customers[0]["reserved"], ["I2"])
        self.assertEqual(s.customers[1]["reserved"], ["I1"])

    def test_spoiled_reservation_replaced_and_cooked_same_step(self):
        s = self.make_sim([self.item("I1", fresh=30), self.item("I2", fresh=80)],
                          [self.order(reserved=["I1"])], player={"pos": [2, 8]})
        ev = s.step(InputState((0, 0), {}, {"interact"}))
        self.assertEqual([name for name, _ in ev], ["spoiled", "cook_started"])
        self.assertEqual([it["id"] for it in ev[1][1]["items"]], ["I2"])
        self.assertEqual(ev[1][1]["base_price"], 47)
        self.assertEqual([it["id"] for it in s.stock], ["I1"])

    def test_replacement_releases_entire_recipe(self):
        items = [self.item("I1", "bong_sung", 30), self.item("I2", "bong_sung", 60),
                 self.item("I3", "bong_sung", 90)]
        s = self.make_sim(items, [self.order(dish="goi_bong_sung", reserved=["I1", "I2"])])
        s.step(NO_INPUT)
        self.assertEqual(s.customers[0]["reserved"], ["I3", "I2"])
        self.assertEqual(len(s.stock), 3)

    def test_failed_replacement_unfulfillable_waits_and_does_not_retry(self):
        orders = [self.order(reserved=["I1"], patience_ticks_left=3),
                  self.order("C2", "T2", reserved=["I2"], patience_ticks_left=1)]
        s = self.make_sim([self.item("I1", fresh=30), self.item("I2")], orders)
        ev = s.step(NO_INPUT)  # I2 vẫn giữ lúc thử lại; sau đó C2 rời nhả I2.
        self.assertEqual([name for name, _ in ev], ["spoiled", "customer_left"])
        self.assertEqual((s.customers[0]["order_status"], s.customers[0]["reserved"]), ("unfulfillable", []))
        s.pos = [2, 8]
        self.assertEqual(s.step(InputState((0, 0), {}, {"interact"})), [])
        self.assertEqual(s.customers[0]["order_status"], "unfulfillable")
        self.assertEqual(s.step(NO_INPUT)[0][0], "customer_left")

    def test_affected_order_priority_and_all_spoiled_before_stove(self):
        for first_order, expected in ((0, "C1"), (1, "C2")):
            with self.subTest(first_order=first_order):
                s = self.make_sim([self.item("I10", fresh=30), self.item("I2", fresh=30), self.item("I3")],
                                  [self.order("C2", "T2", order_tick=0, reserved=["I2"]),
                                   self.order("C1", "T1", order_tick=first_order, reserved=["I10"])],
                                  player={"pos": [2, 8]})
                ev = s.step(InputState((0, 0), {}, {"interact"}))
                self.assertEqual([name for name, _ in ev], ["spoiled", "spoiled", "cook_started"])
                self.assertEqual([e[1]["item_id"] for e in ev[:2]], ["I2", "I10"])
                self.assertEqual(ev[2][1]["order_id"], expected)
                other = next(c for c in s.customers if c["id"] != expected)
                self.assertEqual(other["order_status"], "unfulfillable")

    def test_integer_mean_price_locked_and_tip_on_locked_price(self):
        # Tổng 36001 sau hao, trung bình 75.002083...; giá gỏi floor(40 * mean/100) = 30.
        s = self.make_sim([self.item("I10", "bong_sung", 80),
                           self.item("I2", "bong_sung", 16803 / 240)],
                          [self.order(dish="goi_bong_sung", reserved=["I10", "I2"])], player={"pos": [2, 8]})
        ev = s.step(InputState((0, 0), {}, {"interact"}))
        self.assertEqual(ev[0][1]["base_price"], 30)
        self.assertEqual([it["id"] for it in ev[0][1]["items"]], ["I2", "I10"])
        self.assertEqual(ev[0][1]["items"], [self.item("I2", "bong_sung", round(16802 / 240, 6)),
                                             self.item("I10", "bong_sung", round(19199 / 240, 6))])
        step_until(s, 241)
        s.step(InputState((0, 0), {}, {"interact"}))  # bưng
        s.pos = [9, 2]
        served = s.step(InputState((0, 0), {}, {"interact"}))
        self.assertEqual((served[0][1]["base_price"], served[0][1]["tip"]), (30, 6))
        s.time_left_ticks = 1
        paid = s.step(NO_INPUT)
        self.assertEqual((paid[0][1]["base_price"], paid[0][1]["tip"], s.money), (30, 6, 36))

    def test_items_sorted_by_kind_then_numeric_id_consumes_exact_reserved(self):
        s = self.make_sim([self.item("I10", "ca_linh"), self.item("I2", "ca_linh"),
                           self.item("I3", "ca_linh"), self.item("I4", "bong_dien_dien"),
                           self.item("I1", "ca_linh")],
                          [self.order(dish="lau_ca_linh_dien_dien", reserved=["I10", "I3", "I2", "I4"])],
                          player={"pos": [2, 8]})
        ev = s.step(InputState((0, 0), {}, {"interact"}))
        self.assertEqual([it["id"] for it in ev[0][1]["items"]], ["I4", "I2", "I3", "I10"])
        self.assertEqual([it["id"] for it in s.stock], ["I1"])
        self.assertEqual(s.customers[0]["reserved"], [])

    def test_spoiled_stock_not_available_for_arrivals(self):
        s = self.make_sim([self.item("I1", fresh=29)])
        s.random_customers = True
        self.assertEqual(step_until(s, 120), [("no_dish", {})])

    def test_loaded_inventory_internal_units_copied_and_ids_reserved(self):
        inventory = [{"id": "I10", "kind": "ca_loc", "fresh_u": 7200}]
        s = QuanSim(TUNING, {"random_customers": False}, Streams(1), IdAllocator(), inventory=inventory)
        self.assertEqual(s.ids.new("I"), "I11")
        s.step(NO_INPUT)
        self.assertEqual(inventory[0]["fresh_u"], 7200)
        self.assertEqual(s.stock[0]["fresh_u"], 7199)

    def test_threshold_uses_units_before_output_rounding(self):
        s = self.make_sim([self.item("I1", fresh=7201 / 240)])
        self.assertEqual(s.step(NO_INPUT), [])
        self.assertEqual(s.stock[0]["fresh_u"], 7200)
        self.assertEqual(s.step(NO_INPUT), [
            ("spoiled", {"item_id": "I1", "kind": "ca_loc", "location": "stock"})])

    def test_failed_recipe_releases_healthy_items_for_next_affected_order(self):
        items = [self.item("I1", "bong_sung", 30), self.item("I2", "bong_sung", 60),
                 self.item("I3", "bong_sung", 30), self.item("I4", "bong_sung", 90)]
        s = self.make_sim(items, [self.order(dish="goi_bong_sung", reserved=["I1", "I2"]),
                                 self.order("C2", "T2", dish="goi_bong_sung", reserved=["I3", "I4"])])
        s.step(NO_INPUT)
        self.assertEqual((s.customers[0]["order_status"], s.customers[0]["reserved"]), ("unfulfillable", []))
        self.assertEqual(s.customers[1]["reserved"], ["I4", "I2"])
        self.assertEqual(s.customers[1]["order_status"], "reserved")

    def test_price_integer_floor_at_and_just_below_boundary(self):
        for second_units, expected in ((18000, 29), (18001, 30)):
            with self.subTest(second_units=second_units):
                s = self.make_sim([self.item("I1", "bong_sung", 18001 / 240),
                                   self.item("I2", "bong_sung", second_units / 240)],
                                  [self.order(dish="goi_bong_sung")], player={"pos": [2, 8]})
                ev = s.step(InputState((0, 0), {}, {"interact"}))
                self.assertEqual(ev[0][1]["base_price"], expected)

    def test_bad_reserved_ids_rejected(self):
        from chonoi.errors import BadInput
        for reserved in (["I999"], ["I1", "I1"], [], {}, ["I2"]):
            with self.subTest(reserved=reserved), self.assertRaises(BadInput):
                self.make_sim([self.item("I1"), self.item("I2", fresh=29)], [self.order(reserved=reserved)])
        with self.assertRaises(BadInput):
            self.make_sim([self.item("I1")], [self.order(reserved=["I1"]),
                                             self.order("C2", "T2", reserved=["I1"])])


if __name__ == "__main__":
    unittest.main()
