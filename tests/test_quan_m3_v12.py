"""M3 Phase 3 — Quán v1.2 "Mùa Nước Nổi": kho cá thể có độ tươi (AC-P3-C1 … C9, xem docs/plan/phase-3.md).

Dựng QuanSim trực tiếp với kho là MẢNG cá thể {id, kind, fresh}. Chưa đi qua headless vì `game.contract.json`
còn `contract_version: "1.1"` (M6.4 bật 1.2 sau); các test hộp đen sẽ thêm sau khi bật.

Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_quan_m3_v12 -v
"""

import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.runner import Session
from chonoi.sim.quan import QuanSim

IDLE = InputState((0.0, 0.0), {}, set())
LOC = "ca_loc_nuong_trui"        # ca_loc x1
GOI = "goi_bong_sung"            # bong_sung x2
LAU_LINH = "lau_ca_linh_dien_dien"  # ca_linh x3 + bong_dien_dien x1


def item(iid, kind, fresh):
    return {"id": iid, "kind": kind, "fresh": fresh}


def cust(cid, table, dish=LOC, **kw):
    return {"id": cid, "table_id": table, "dish_id": dish, **kw}


def make_sim(stock, customers=(), random_customers=False, seed=1, **extra):
    sc = {"stock": list(stock), "customers": list(customers), "random_customers": random_customers, **extra}
    return QuanSim(load_contract()["tuning"], sc, Streams(seed), IdAllocator())


def run(sim, n):
    """Chạy n bước; trả [(tick, tên, data)] với tick tính từ lúc gọi."""
    out = []
    for _ in range(n):
        tick = sim.phase_tick + 1
        for name, data in sim.step(IDLE):
            out.append((tick, name, data))
    return out


def fresh_of(sim, iid):
    return next(x for x in sim.snapshot()["stock"] if x["id"] == iid)["fresh"]


def cust_of(sim, cid):
    return next(c for c in sim.snapshot()["customers"] if c["id"] == cid)


def named(evs, name):
    return [(t, d) for t, n, d in evs if n == name]


class StockSchema(unittest.TestCase):
    def test_c1_snapshot_stock_is_array_of_items_sorted_by_id(self):  # AC-P3-C1
        sim = make_sim([item("I10", "ca_loc", 97.5), item("I2", "ca_linh", 100), item("I1", "bong_sung", 60)])
        self.assertEqual(sim.snapshot()["stock"], [item("I1", "bong_sung", 60.0), item("I2", "ca_linh", 100.0),
                                                   item("I10", "ca_loc", 97.5)])

    def test_c1_count_stock_still_supported(self):  # AC-P3-C9: kho đếm v1.1 chạy như cũ
        sim = QuanSim(load_contract()["tuning"], {"stock": {"ca_loc": 2}, "random_customers": False},
                      Streams(1), IdAllocator())
        self.assertFalse(sim.item_mode)
        self.assertEqual(sim.snapshot()["stock"], {"ca_loc": 2})


class Decay(unittest.TestCase):
    def test_c2_quan_decay_is_quarter_point_per_second(self):  # AC-P3-C2: 0.25/s = 1 đơn vị/tick
        sim = make_sim([item("I1", "ca_loc", 100)])
        run(sim, 240)  # 4 s
        self.assertEqual(fresh_of(sim, "I1"), 99.0)

    def test_c2_handed_over_stock_not_decayed_before_first_step(self):  # AC-P3-C2: snapshot tick 0 = file
        sim = make_sim([item("I1", "ca_loc", 87.25)])
        self.assertEqual(fresh_of(sim, "I1"), 87.25)

    def test_c2_decay_clamps_at_zero(self):  # AC-P3-C2
        sim = make_sim([item("I1", "ca_loc", 0.0), item("I2", "ca_loc", 1 / 240)])
        run(sim, 5)
        self.assertEqual([x["fresh"] for x in sim.snapshot()["stock"]], [0.0, 0.0])

    def test_c2_reserved_stock_decays_too(self):  # AC-P3-C2: "kể cả hàng đang giữ chỗ"
        sim = make_sim([item("I1", "ca_loc", 100)], [cust("C1", "T1")])
        self.assertEqual(cust_of(sim, "C1")["reserved"], ["I1"])
        run(sim, 240)
        self.assertEqual(fresh_of(sim, "I1"), 99.0)

    def test_c2_pause_freezes_decay(self):  # AC-P3-C2: Pause dừng hao tươi
        tuning = load_contract()["tuning"]
        sess = Session("quan", tuning, {"stock": [item("I1", "ca_loc", 100)], "random_customers": False}, seed=1)
        for _ in range(120):
            sess.step(IDLE)
        before = next(x for x in sess.snapshot()["stock"])["fresh"]
        pause = InputState((0.0, 0.0), {"pause": True}, {"pause"})
        sess.step(pause)
        for _ in range(300):  # đang pause: không hao
            sess.step(IDLE)
        self.assertEqual(sess.snapshot()["state"], "paused")
        self.assertEqual(next(x for x in sess.snapshot()["stock"])["fresh"], before)


class Spoiled(unittest.TestCase):
    def test_c3_exact_30_spoils_on_first_step(self):  # AC-P3-C3
        sim = make_sim([item("I1", "ca_linh", 30)])
        evs = run(sim, 3)
        self.assertEqual(named(evs, "spoiled"), [(1, {"item_id": "I1", "kind": "ca_linh", "location": "stock"})])

    def test_c3_threshold_is_exact_not_float(self):  # AC-P3-C3: 30 + 1/240 chỉ ươn ở tick 2
        sim = make_sim([item("I1", "ca_linh", 30 + 1 / 240)])
        evs = run(sim, 3)
        self.assertEqual([t for t, _ in named(evs, "spoiled")], [2])

    def test_c3_spoiled_emitted_exactly_once(self):  # AC-P3-C3
        sim = make_sim([item("I1", "ca_linh", 30)])
        self.assertEqual(len(named(run(sim, 600), "spoiled")), 1)

    def test_c3_already_spoiled_item_emits_nothing(self):  # AC-P3-C3: chỉ khi đi từ >= 30 xuống < 30
        sim = make_sim([item("I1", "ca_linh", 10)])
        self.assertEqual(named(run(sim, 5), "spoiled"), [])

    def test_c3_simultaneous_spoils_ordered_by_id(self):  # AC-P3-C3: I2 trước I10
        sim = make_sim([item("I10", "ca_loc", 30), item("I2", "ca_linh", 30), item("I1", "bong_sung", 99)])
        evs = named(run(sim, 1), "spoiled")
        self.assertEqual([d["item_id"] for _, d in evs], ["I2", "I10"])

    def test_c3_spoiled_item_keeps_its_slot(self):  # AC-P3-C3: ươn vẫn chiếm ô
        sim = make_sim([item("I1", "ca_linh", 30)])
        run(sim, 10)
        self.assertEqual([x["id"] for x in sim.snapshot()["stock"]], ["I1"])
        self.assertLess(fresh_of(sim, "I1"), 30)


class Reservation(unittest.TestCase):
    def test_c4_picks_freshest_then_lowest_id(self):  # AC-P3-C4
        sim = make_sim([item("I1", "ca_loc", 80), item("I3", "ca_loc", 100), item("I2", "ca_loc", 100)],
                       [cust("C1", "T1")])
        self.assertEqual(cust_of(sim, "C1")["reserved"], ["I2"])

    def test_c4_recipe_with_several_kinds_and_counts(self):  # AC-P3-C4
        stock = [item("I1", "ca_linh", 50), item("I2", "ca_linh", 90), item("I3", "ca_linh", 70),
                 item("I4", "ca_linh", 90), item("I5", "bong_dien_dien", 40)]
        sim = make_sim(stock, [cust("C1", "T1", LAU_LINH)])
        self.assertEqual(cust_of(sim, "C1")["reserved"], ["I2", "I3", "I4", "I5"])

    def test_c4_fixture_orders_allocated_by_order_tick_then_table(self):  # AC-P3-C4
        sim = make_sim([item("I1", "ca_loc", 100), item("I2", "ca_loc", 60)],
                       [cust("B", "T1", order_tick=5), cust("A", "T2", order_tick=1)])
        self.assertEqual(cust_of(sim, "A")["reserved"], ["I1"])  # order_tick nhỏ hơn -> được cá tươi nhất
        self.assertEqual(cust_of(sim, "B")["reserved"], ["I2"])

    def test_c4_same_order_tick_ties_by_table_id(self):  # AC-P3-C4
        sim = make_sim([item("I1", "ca_loc", 100), item("I2", "ca_loc", 60)],
                       [cust("B", "T2"), cust("A", "T1")])
        self.assertEqual(cust_of(sim, "A")["reserved"], ["I1"])

    def test_c4_explicit_reserved_ids_are_respected(self):  # AC-P3-C4
        sim = make_sim([item("I1", "ca_loc", 100), item("I2", "ca_loc", 60)],
                       [cust("C1", "T1", reserved=["I2"])])
        self.assertEqual(cust_of(sim, "C1")["reserved"], ["I2"])

    def test_c4_new_customer_reserves_freshest_unspoiled_unreserved(self):  # AC-P3-C4
        stock = [item("I1", "ca_loc", 10), item("I2", "ca_loc", 70), item("I3", "ca_loc", 95)]
        sim = make_sim(stock, [cust("C1", "T1", reserved=["I3"])], random_customers=True)
        evs = run(sim, 120)
        arr = named(evs, "customer_arrived")
        self.assertEqual(len(arr), 1)
        self.assertEqual(cust_of(sim, arr[0][1]["order_id"])["reserved"], ["I2"])  # I1 ươn, I3 đã bị giữ

    def test_c4_spoiled_and_reserved_items_do_not_count_as_available(self):  # AC-P3-C4
        sim = make_sim([item("I1", "ca_loc", 10), item("I2", "ca_loc", 100)], [cust("C1", "T1")],
                       random_customers=True)
        evs = run(sim, 120)
        self.assertEqual([t for t, _ in named(evs, "no_dish")], [120])  # còn I2 nhưng đã giữ, I1 ươn


class ReReserve(unittest.TestCase):
    def test_c5_spoiled_reserved_item_is_replaced_by_next_freshest(self):  # AC-P3-C5
        sim = make_sim([item("I1", "ca_loc", 30), item("I2", "ca_loc", 60), item("I3", "ca_loc", 80)],
                       [cust("C1", "T1", reserved=["I1"])])
        evs = run(sim, 1)
        self.assertEqual([n for _, n, _ in evs], ["spoiled"])
        c = cust_of(sim, "C1")
        self.assertEqual((c["reserved"], c["order_status"]), (["I3"], "reserved"))

    def test_c5_whole_reservation_is_released_and_redone(self):  # AC-P3-C5: nhả TOÀN BỘ phần giữ
        stock = [item("I1", "bong_sung", 30), item("I2", "bong_sung", 50), item("I3", "bong_sung", 90),
                 item("I4", "bong_sung", 70)]
        sim = make_sim(stock, [cust("C1", "T1", GOI, reserved=["I1", "I2"])])
        run(sim, 1)
        self.assertEqual(cust_of(sim, "C1")["reserved"], ["I3", "I4"])  # chọn lại tươi nhất, không giữ I2 cũ

    def test_c5_not_enough_fresh_items_becomes_unfulfillable(self):  # AC-P3-C5
        sim = make_sim([item("I1", "ca_loc", 30)], [cust("C1", "T1", reserved=["I1"])])
        run(sim, 1)
        c = cust_of(sim, "C1")
        self.assertEqual((c["reserved"], c["order_status"], c["state"]), ([], "unfulfillable", "waiting"))

    def test_c5_unfulfillable_customer_waits_until_patience_runs_out(self):  # AC-P3-C5: khách chờ tới hạn
        sim = make_sim([item("I1", "ca_loc", 30)], [cust("C1", "T1", reserved=["I1"], patience_ticks_left=50)])
        evs = run(sim, 60)
        left = named(evs, "customer_left")
        self.assertEqual([(t, d["reason"]) for t, d in left], [(50, "patience")])

    def test_c5_retry_happens_only_once(self):  # AC-P3-C5: không giữ lại lần nữa khi hàng mới về
        sim = make_sim([item("I1", "ca_loc", 30)], [cust("C1", "T1", reserved=["I1"])])
        run(sim, 1)
        sim.stock.append({"id": "I9", "kind": "ca_loc", "units": 24000})  # hàng tươi xuất hiện sau
        run(sim, 30)
        self.assertEqual(cust_of(sim, "C1")["order_status"], "unfulfillable")

    def test_c5_affected_orders_processed_by_order_tick_then_table(self):  # AC-P3-C5
        stock = [item("I1", "ca_loc", 30), item("I2", "ca_loc", 30), item("I3", "ca_loc", 100)]
        sim = make_sim(stock, [cust("A", "T2", order_tick=1, reserved=["I1"]),
                               cust("B", "T1", order_tick=2, reserved=["I2"])])
        run(sim, 1)
        self.assertEqual((cust_of(sim, "A")["reserved"], cust_of(sim, "A")["order_status"]), (["I3"], "reserved"))
        self.assertEqual((cust_of(sim, "B")["reserved"], cust_of(sim, "B")["order_status"]), ([], "unfulfillable"))

    def test_c5_same_order_tick_breaks_tie_by_table_id(self):  # AC-P3-C5
        stock = [item("I1", "ca_loc", 30), item("I2", "ca_loc", 30), item("I3", "ca_loc", 100)]
        sim = make_sim(stock, [cust("A", "T2", reserved=["I1"]), cust("B", "T1", reserved=["I2"])])
        run(sim, 1)
        self.assertEqual(cust_of(sim, "B")["order_status"], "reserved")  # T1 trước T2
        self.assertEqual(cust_of(sim, "A")["order_status"], "unfulfillable")

    def test_c5_spoiled_events_come_before_rereservation_effects(self):  # AC-P3-C5: phát hết spoiled rồi mới xử lý
        sim = make_sim([item("I2", "ca_loc", 30), item("I1", "ca_loc", 30), item("I3", "ca_loc", 100)],
                       [cust("C1", "T1", reserved=["I1"])])
        evs = run(sim, 1)
        self.assertEqual([d["item_id"] for _, n, d in evs if n == "spoiled"], ["I1", "I2"])

    def test_c5_unaffected_order_keeps_its_reservation(self):  # AC-P3-C5
        sim = make_sim([item("I1", "ca_loc", 30), item("I2", "ca_loc", 100), item("I3", "ca_loc", 90)],
                       [cust("C1", "T1", reserved=["I2"])])
        run(sim, 1)
        self.assertEqual(cust_of(sim, "C1")["reserved"], ["I2"])  # không bị nhả/đổi sang I3

    def test_c5_item_reserved_at_arrival_spoils_while_waiting(self):  # AC-P3-C5: luồng tự sinh khách
        sim = make_sim([item("I1", "ca_loc", 30.5)], random_customers=True)  # ươn sau 121 tick quán
        evs = run(sim, 125)
        arr = named(evs, "customer_arrived")
        self.assertEqual([t for t, _ in arr], [120])
        self.assertEqual([t for t, _ in named(evs, "spoiled")], [121])
        c = cust_of(sim, arr[0][1]["order_id"])
        self.assertEqual((c["reserved"], c["order_status"]), ([], "unfulfillable"))


class Leaving(unittest.TestCase):
    def test_c6_leaving_customer_releases_reserved_items(self):  # AC-P3-C6
        sim = make_sim([item("I1", "ca_loc", 100)], [cust("C1", "T1", patience_ticks_left=2)],
                       random_customers=True)
        run(sim, 3)
        self.assertEqual(sim.customers, [])
        self.assertEqual(sim._cookable_dishes(), [LOC])  # I1 lại khả dụng
        self.assertEqual(len(sim.snapshot()["stock"]), 1)  # hàng không mất khi khách bỏ đi (chưa nấu)


class M4Hooks(unittest.TestCase):
    def test_c7_consume_reserved_takes_exact_ids_sorted_by_kind_then_id(self):  # AC-P3-C7
        stock = [item("I1", "ca_linh", 90), item("I2", "bong_dien_dien", 50), item("I3", "ca_linh", 70),
                 item("I4", "ca_linh", 80), item("I5", "ca_linh", 60)]
        sim = make_sim(stock, [cust("C1", "T1", LAU_LINH)])
        c = next(x for x in sim.customers if x["id"] == "C1")
        self.assertEqual(c["reserved"], ["I1", "I2", "I3", "I4"])
        taken = sim._consume_reserved(c)
        self.assertEqual([(x["kind"], x["id"]) for x in taken],
                         [("bong_dien_dien", "I2"), ("ca_linh", "I1"), ("ca_linh", "I3"), ("ca_linh", "I4")])
        self.assertEqual([x["fresh"] for x in taken], [50.0, 90.0, 70.0, 80.0])
        self.assertEqual([x["id"] for x in sim.snapshot()["stock"]], ["I5"])
        self.assertEqual(c["reserved"], [])

    def test_c7_stock_items_out_returns_handover_array(self):  # AC-P3-C7
        sim = make_sim([item("I2", "ca_loc", 100), item("I1", "ca_linh", 50)])
        run(sim, 240)
        self.assertEqual(sim.stock_items_out(), [item("I1", "ca_linh", 49.0), item("I2", "ca_loc", 99.0)])


class Determinism(unittest.TestCase):
    def test_c8_same_seed_same_events_and_state(self):  # AC-P3-C8
        stock = [item(f"I{i}", k, 40 + 3 * i) for i, k in enumerate(
            ["ca_loc", "ca_loc", "bong_sung", "bong_sung", "ca_linh", "ca_linh", "ca_linh", "bong_dien_dien"], 1)]

        def go():
            sim = make_sim(stock, random_customers=True, seed=7)
            evs = run(sim, 2000)
            return evs, sim.snapshot()
        self.assertEqual(go(), go())


if __name__ == "__main__":
    unittest.main()
