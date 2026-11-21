"""Lát 3 Phase 3 (minhtriet061203): kho quán cá thể, hao tươi, ươn, giữ chỗ theo id (TICKET-03 mục 1).

Chạy với tuning v1.2 dựng trong test (thêm khối `freshness`), độc lập với version của manifest:
manifest chỉ bật "1.2" ở bước tích hợp p25 (docs/plan/phase-3.md). Số liệu đọc từ game.contract.json.
Fixture dùng fresh biểu diễn chính xác bằng 240 đơn vị/điểm: quán hao 1 đơn vị (1/240 điểm) mỗi tick.
"""

import copy
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.items import UNITS, ItemIds
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim

V12 = copy.deepcopy(load_contract()["tuning"])
V12.setdefault("freshness", {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30})
MENU = V12["menu"]
FIRST = V12["quan"]["first_customer_tick"]
SPOIL = V12["freshness"]["spoiled_below"]
STEP = 1 / UNITS  # điểm tươi mất mỗi tick ở quán (0.25/s ÷ 60)
IDLE = InputState((0.0, 0.0), set(), set())
B1 = V12["quan"]["stoves"][0]


def it(iid, kind, fresh):
    return {"id": iid, "kind": kind, "fresh": fresh}


def make(scenario=None, seed=1, inventory=None, **kw):
    return QuanSim(V12, scenario or {}, Streams(seed), IdAllocator(), inventory=inventory, **kw)


def step(sim, n=1, inp=IDLE):
    out = []
    for _ in range(n):
        out += sim.step(inp)
    return out


def one(dish="ca_loc_nuong_trui", **kw):
    return dict({"id": "C1", "table_id": "T1", "dish_id": dish}, **kw)


class StockSchema(unittest.TestCase):
    def test_snapshot_stock_is_item_array_sorted_by_id(self):
        sim = make({"stock": [it("I10", "ca_loc", 50), it("I2", "bong_sung", 100)]})
        self.assertEqual(sim.snapshot()["stock"], [it("I2", "bong_sung", 100), it("I10", "ca_loc", 50)])

    def test_spoiled_items_stay_in_stock(self):
        sim = make({"stock": [it("I1", "ca_loc", 10)]})
        step(sim, 5)
        self.assertEqual([s["id"] for s in sim.snapshot()["stock"]], ["I1"])

    def test_item_ids_continue_after_loaded_stock(self):
        ids = ItemIds()
        make({"stock": [it("I7", "ca_loc", 100)]}, item_ids=ids)
        self.assertEqual(ids.new(), "I8")


class Decay(unittest.TestCase):
    """Kho quán giảm 0.25/s (1 đơn vị/tick), kể cả hàng đang giữ; kẹp 0."""

    def test_decay_quarter_point_per_second(self):
        sim = make({"stock": [it("I1", "ca_loc", 100)], "random_customers": False})
        step(sim, 60)
        self.assertAlmostEqual(sim.snapshot()["stock"][0]["fresh"], 100 - V12["freshness"]["quan_decay_per_s"], places=6)

    def test_reserved_item_also_decays(self):
        sim = make({"stock": [it("I1", "ca_loc", 100)], "random_customers": False, "customers": [one()]})
        step(sim, 240)
        self.assertEqual(sim.snapshot()["customers"][0]["reserved"], ["I1"])
        self.assertAlmostEqual(sim.snapshot()["stock"][0]["fresh"], 99.0, places=6)

    def test_clamped_at_zero(self):
        sim = make({"stock": [it("I1", "ca_loc", STEP)], "random_customers": False})
        step(sim, 3)
        self.assertEqual(sim.snapshot()["stock"][0]["fresh"], 0)


class Spoiled(unittest.TestCase):
    """Phát spoiled (location stock) đúng một lần khi từ ≥ 30 xuống < 30; nhiều cá thể -> theo id."""

    def test_exactly_at_30_spoils_on_first_step(self):
        sim = make({"stock": [it("I1", "ca_linh", SPOIL)], "random_customers": False})
        self.assertEqual(sim.step(IDLE), [("spoiled", {"item_id": "I1", "kind": "ca_linh", "location": "stock"})])
        self.assertEqual(step(sim, 10), [], "chỉ phát một lần")

    def test_just_above_threshold_spoils_on_exact_tick(self):
        sim = make({"stock": [it("I1", "ca_loc", SPOIL + 2 * STEP)], "random_customers": False})
        self.assertEqual(step(sim, 2), [])
        self.assertEqual([n for n, _ in sim.step(IDLE)], ["spoiled"])

    def test_already_spoiled_never_emits(self):
        sim = make({"stock": [it("I1", "ca_loc", 29)], "random_customers": False})
        self.assertEqual(step(sim, 5), [])

    def test_multiple_spoil_same_tick_in_id_order(self):
        sim = make({"stock": [it("I10", "ca_loc", SPOIL), it("I2", "bong_sung", SPOIL), it("I3", "ca_linh", 80)],
                    "random_customers": False})
        self.assertEqual([d["item_id"] for _, d in sim.step(IDLE)], ["I2", "I10"])

    def test_spoiled_not_available_for_new_orders(self):
        # chỉ có cá lóc ươn -> no_dish
        sim = make({"stock": [it("I1", "ca_loc", 20)]})
        ev = step(sim, FIRST)
        self.assertEqual(ev, [("no_dish", {})])


class ReserveById(unittest.TestCase):
    """Giữ theo id: mỗi loại lấy cá thể khả dụng tươi nhất, hòa theo id."""

    def test_new_customer_reserves_freshest_then_smallest_id(self):
        stock = [it("I1", "bong_sung", 60), it("I2", "bong_sung", 90), it("I3", "bong_sung", 90), it("I4", "bong_sung", 95)]
        sim = make({"stock": stock})
        step(sim, FIRST)
        c = sim.snapshot()["customers"][0]
        self.assertEqual((c["dish_id"], c["reserved"]), ("goi_bong_sung", ["I2", "I4"]))

    def test_second_customer_takes_remaining_items(self):
        t = copy.deepcopy(V12)
        t["quan"]["tables"] = t["quan"]["tables"][:2]
        interval = int(round(t["quan"]["customer_interval_s"] * 60))
        sim = QuanSim(t, {"stock": [it("I1", "ca_loc", 70), it("I2", "ca_loc", 90)]}, Streams(1), IdAllocator())
        step(sim, FIRST + interval)
        self.assertEqual([c["reserved"] for c in sim.snapshot()["customers"]], [["I2"], ["I1"]])
        self.assertEqual(sim.available(), {})

    def test_spoiled_skipped_when_reserving(self):
        sim = make({"stock": [it("I1", "ca_loc", 99), it("I2", "ca_loc", 10)]})
        step(sim, FIRST)
        self.assertEqual(sim.snapshot()["customers"][0]["reserved"], ["I1"])


class ReReserve(unittest.TestCase):
    """Phần giữ vừa ươn -> nhả toàn bộ, giữ lại đúng một lần; thiếu -> unfulfillable, khách chờ tới hạn."""

    def test_rereserve_with_another_fresh_item(self):
        sim = make({"stock": [it("I1", "ca_loc", SPOIL), it("I2", "ca_loc", 50)], "random_customers": False,
                    "customers": [one(reserved=["I1"])]})
        ev = sim.step(IDLE)
        self.assertEqual(ev, [("spoiled", {"item_id": "I1", "kind": "ca_loc", "location": "stock"})])
        c = sim.snapshot()["customers"][0]
        self.assertEqual((c["order_status"], c["reserved"]), ("reserved", ["I2"]))

    def test_whole_reservation_released_on_partial_spoil(self):
        # gỏi giữ I1 (ươn ngay) + I2; giữ lại phải lấy 2 cá thể tươi nhất còn lại: I2 và I3
        stock = [it("I1", "bong_sung", SPOIL), it("I2", "bong_sung", 40), it("I3", "bong_sung", 80)]
        sim = make({"stock": stock, "random_customers": False,
                    "customers": [one("goi_bong_sung", reserved=["I1", "I2"])]})
        sim.step(IDLE)
        self.assertEqual(sim.snapshot()["customers"][0]["reserved"], ["I2", "I3"])

    def test_unfulfillable_when_not_enough(self):
        sim = make({"stock": [it("I1", "ca_loc", SPOIL)], "random_customers": False,
                    "customers": [one(reserved=["I1"], patience_ticks_left=5)]})
        sim.step(IDLE)
        c = sim.snapshot()["customers"][0]
        self.assertEqual((c["order_status"], c["reserved"], c["state"]), ("unfulfillable", [], "waiting"))
        ev = step(sim, 4)
        self.assertEqual([(n, d["reason"]) for n, d in ev], [("customer_left", "patience")], "chờ tới hết kiên nhẫn")

    def test_unfulfillable_not_cooked(self):
        sim = make({"stock": [it("I1", "ca_loc", SPOIL)], "random_customers": False, "player": {"pos": B1["pos"]},
                    "customers": [one(reserved=["I1"])]})
        sim.step(IDLE)
        ev = sim.step(InputState((0.0, 0.0), {"interact"}, {"interact"}))
        self.assertNotIn("cook_started", [n for n, _ in ev])

    def test_affected_orders_processed_by_order_tick_then_table(self):
        # C2 (order_tick 5) xử lý trước C1 (order_tick 9) -> C2 lấy I3 duy nhất còn tươi; C1 unfulfillable
        stock = [it("I1", "ca_loc", SPOIL), it("I2", "ca_loc", SPOIL), it("I3", "ca_loc", 70)]
        sim = make({"stock": stock, "random_customers": False,
                    "customers": [one(order_tick=9, reserved=["I1"]),
                                  {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "order_tick": 5,
                                   "reserved": ["I2"]}]})
        ev = sim.step(IDLE)
        self.assertEqual([d["item_id"] for _, d in ev], ["I1", "I2"], "phát hết spoiled trước")
        got = {c["id"]: (c["order_status"], c["reserved"]) for c in sim.snapshot()["customers"]}
        self.assertEqual(got, {"C1": ("unfulfillable", []), "C2": ("reserved", ["I3"])})

    def test_retry_only_once(self):
        # giữ lại I2 cũng ươn ở bước sau -> lần đó là lần "vừa ươn" mới, được thử giữ lại một lần nữa (I3)
        stock = [it("I1", "ca_loc", SPOIL), it("I2", "ca_loc", SPOIL + STEP), it("I3", "ca_loc", 90)]
        sim = make({"stock": stock, "random_customers": False, "customers": [one(reserved=["I1"])]})
        sim.step(IDLE)
        self.assertEqual(sim.snapshot()["customers"][0]["reserved"], ["I3"], "tươi nhất là I3, không phải I2")


class CookWithIds(unittest.TestCase):
    """Bắt đầu nấu tiêu đúng các id đang giữ (cùng lát 4); giá chốt theo trung bình fresh."""

    def test_cook_consumes_reserved_ids_and_prices_by_fresh(self):
        stock = [it("I1", "bong_sung", 50), it("I2", "bong_sung", 100), it("I3", "ca_loc", 100)]
        sim = make({"stock": stock, "random_customers": False, "player": {"pos": B1["pos"]},
                    "customers": [one("goi_bong_sung", reserved=["I1", "I2"])]})
        ev = sim.step(InputState((0.0, 0.0), {"interact"}, {"interact"}))
        cook = [d for n, d in ev if n == "cook_started"][0]
        self.assertEqual([i["id"] for i in cook["items"]], ["I1", "I2"])
        avg = (50 - STEP + 100 - STEP) / 2
        self.assertEqual(cook["base_price"], int(MENU["goi_bong_sung"]["price"] * avg // 100))
        self.assertEqual([s["id"] for s in sim.snapshot()["stock"]], ["I3"])


class FixtureV12(unittest.TestCase):
    """Scenario v1.2: reserved mảng id trỏ tới cá thể chưa ươn, đủ công thức, không dùng chung -> sai thì mã 2."""

    def test_missing_reserved_allocated_by_order_tick_then_table(self):
        stock = [it("I1", "ca_loc", 60), it("I2", "ca_loc", 90)]
        sim = make({"stock": stock, "random_customers": False,
                    "customers": [one(order_tick=3),
                                  {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "order_tick": 1}]})
        got = {c["id"]: c["reserved"] for c in sim.snapshot()["customers"]}
        self.assertEqual(got, {"C1": ["I1"], "C2": ["I2"]})

    def test_explicit_reserved_placed_before_auto(self):
        stock = [it("I1", "ca_loc", 60), it("I2", "ca_loc", 90)]
        sim = make({"stock": stock, "random_customers": False,
                    "customers": [one(order_tick=0),
                                  {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "reserved": ["I2"]}]})
        got = {c["id"]: c["reserved"] for c in sim.snapshot()["customers"]}
        self.assertEqual(got, {"C1": ["I1"], "C2": ["I2"]})

    def test_contradictions_raise(self):
        bad = [
            {"stock": [], "customers": [one()]},                                                   # quá tồn
            {"stock": [it("I1", "ca_loc", 90)], "customers": [one(reserved=["I9"])]},              # id không có
            {"stock": [it("I1", "ca_loc", 20)], "customers": [one(reserved=["I1"])]},              # đã ươn
            {"stock": [it("I1", "bong_sung", 90)], "customers": [one(reserved=["I1"])]},           # khác công thức
            {"stock": [it("I1", "ca_loc", 90), it("I2", "ca_loc", 90)],
             "customers": [one(reserved=["I1", "I2"])]},                                           # thừa
            {"stock": [it("I1", "ca_loc", 90)],
             "customers": [one(reserved=["I1"]),
                           {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}]},
            {"stock": [it("I1", "ca_loc", 90)], "customers": [one(order_status="unfulfillable", reserved=["I1"])]},
        ]
        for sc in bad:
            with self.subTest(sc=sc):
                with self.assertRaises(BadInput):
                    make(sc)


class ScenarioFileV12(unittest.TestCase):
    """scenario.py (v1.2): customers[].reserved là mảng id; khách đang ăn / payload mang giá chốt theo fresh."""

    def _load(self, quan):
        from chonoi.scenario import load_scenario
        from helpers import Workdir, write_json
        with Workdir() as w:
            return load_scenario(write_json(w.path("sc.json"), {"quan": quan}), "quan", V12)

    def test_reserved_id_array_ok(self):
        self._load({"stock": [it("I1", "ca_loc", 90)], "customers": [one(reserved=["I1"])]})

    def test_eating_price_by_fresh_ok(self):
        self._load({"customers": [one(state="eating", eat_ticks_left=10, base_price=45, tip=9)]})

    def test_bad_reserved_shapes(self):
        for r in ({"ca_loc": 1}, [1], [""], ["I1", "I1"]):
            with self.subTest(r=r), self.assertRaises(BadInput):
                self._load({"stock": [it("I1", "ca_loc", 90)], "customers": [one(reserved=r)]})

    def test_price_above_list_is_bad(self):
        with self.assertRaises(BadInput):
            self._load({"customers": [one(state="eating", eat_ticks_left=10, base_price=61, tip=0)]})


if __name__ == "__main__":
    unittest.main()
