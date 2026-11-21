"""M3 Phase 2 — Quán v1.1: 4 bàn, 2 bếp, 6 món, lọc món theo kế hoạch ngày (AC-P2-C1 … C7).

Dựng QuanSim trực tiếp với tuning của game.contract.json (đã là v1.1), không cần headless,
nên bám sát luật mà không phụ thuộc phần CLI/`day` của người khác.

Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_quan_m3_v11 -v
"""

import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim

IDLE = InputState((0.0, 0.0), {}, set())
RICH = {"ca_loc": 20, "ca_linh": 20, "bong_sung": 20, "bong_dien_dien": 20, "ca_keo": 20, "keo_neo": 20}
SIX_DISHES = ["ca_keo_nuong", "ca_loc_nuong_trui", "canh_chua_ca_loc", "goi_bong_sung",
              "lau_ca_linh_dien_dien", "lau_mam"]


def make_sim(scenario=None, seed=1, allowed=None):
    tuning = load_contract()["tuning"]
    return QuanSim(tuning, scenario or {}, Streams(seed), IdAllocator(), allowed_dishes=allowed)


def run(sim, until_tick):
    """Chạy đến hết bước `until_tick`; trả danh sách (tick, tên, data) của mọi event."""
    out = []
    for tick in range(sim.phase_tick + 1, until_tick + 1):
        for name, data in sim.step(IDLE):
            out.append((tick, name, data))
    return out


def named(evs, name):
    return [(t, d) for t, n, d in evs if n == name]


def cust(cid, table, dish="ca_loc_nuong_trui", **kw):
    return {"id": cid, "table_id": table, "dish_id": dish, **kw}


class ContractV11(unittest.TestCase):
    def test_contract_has_v11_restaurant(self):  # AC-P2-C2: số chuẩn đọc từ dữ liệu
        t = load_contract()["tuning"]
        self.assertEqual([s["id"] for s in t["quan"]["stoves"]], ["B1", "B2"])
        self.assertEqual([x["id"] for x in t["quan"]["tables"]], ["T1", "T2", "T3", "T4"])
        self.assertEqual(sorted(t["menu"]), SIX_DISHES)
        self.assertEqual(t["menu"]["lau_mam"]["recipe"],
                         {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1})
        self.assertEqual((t["menu"]["lau_mam"]["cook_s"], t["menu"]["lau_mam"]["price"]), (12, 200))


class Tables(unittest.TestCase):
    def test_c1_customers_take_lowest_free_table_in_order(self):  # AC-P2-C1
        sim = make_sim({"stock": RICH})
        evs = run(sim, 2820)
        arr = named(evs, "customer_arrived")
        self.assertEqual([(t, d["table_id"]) for t, d in arr],
                         [(120, "T1"), (1020, "T2"), (1920, "T3"), (2820, "T4")])
        self.assertEqual([d["order_id"] for _, d in arr], ["K1", "K2", "K3", "K4"])
        self.assertEqual(named(evs, "no_dish"), [])

    def test_c1_freed_table_is_reused_by_next_round(self):  # AC-P2-C1: K1 hết kiên nhẫn đúng lượt 5
        sim = make_sim({"stock": RICH})
        evs = run(sim, 3720)
        self.assertEqual([(t, d["order_id"], d["reason"]) for t, d in named(evs, "customer_left")],
                         [(3720, "K1", "patience")])
        last = named(evs, "customer_arrived")[-1]
        self.assertEqual((last[0], last[1]["table_id"]), (3720, "T1"))  # T1 vừa trống, bàn nhỏ nhất

    def test_c1_all_tables_busy_skips_round_without_no_dish(self):  # AC-P2-C1
        fixtures = [cust(f"C{i}", f"T{i}") for i in range(1, 5)]
        sim = make_sim({"stock": {"ca_loc": 4}, "customers": fixtures})
        evs = run(sim, 130)
        self.assertEqual(named(evs, "customer_arrived"), [])
        self.assertEqual(named(evs, "no_dish"), [])
        self.assertEqual(len(sim.customers), 4)

    def test_c1_fixture_customer_on_t3_keeps_lower_tables_free(self):  # AC-P2-C1
        sim = make_sim({"stock": RICH, "customers": [cust("C1", "T3")]})
        evs = run(sim, 120)
        self.assertEqual(named(evs, "customer_arrived")[0][1]["table_id"], "T1")


class Reservation(unittest.TestCase):
    def test_c3_reservations_accumulate_across_customers(self):  # AC-P2-C3
        # 2 khách chờ, mỗi người giữ 1 cá lóc: kho 2 thì không còn món nào gọi thêm được
        sim = make_sim({"stock": {"ca_loc": 2}, "customers": [cust("C1", "T1"), cust("C2", "T2")]})
        self.assertEqual(sim._available_stock()["ca_loc"], 0)
        evs = run(sim, 120)
        self.assertEqual([t for t, _ in named(evs, "no_dish")], [120])
        self.assertEqual(named(evs, "customer_arrived"), [])

    def test_c3_third_customer_only_when_stock_left_after_holds(self):  # AC-P2-C3
        sim = make_sim({"stock": {"ca_loc": 3}, "customers": [cust("C1", "T1"), cust("C2", "T2")]})
        evs = run(sim, 120)
        arr = named(evs, "customer_arrived")
        self.assertEqual((len(arr), arr[0][1]["table_id"], arr[0][1]["dish_id"]),
                         (1, "T3", "ca_loc_nuong_trui"))
        self.assertEqual(sim._available_stock()["ca_loc"], 0)

    def test_c2_lau_mam_reserves_four_kinds(self):  # AC-P2-C2, C3
        stock = {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1}
        sim = make_sim({"stock": stock, "customers": [cust("C1", "T1", "lau_mam")]})
        c = sim.customers[0]
        self.assertEqual(c["reserved"], stock)
        self.assertEqual(sim._available_stock(), {k: 0 for k in stock})
        snap = sim.snapshot()["customers"][0]
        self.assertEqual(list(snap["reserved"]), sorted(stock))  # xuất theo thứ tự kind

    def test_c2_lau_mam_needs_every_ingredient(self):  # AC-P2-C2
        sim = make_sim({"stock": {"ca_linh": 2, "ca_keo": 1, "bong_dien_dien": 1}})  # thiếu keo_neo
        self.assertNotIn("lau_mam", sim._cookable_dishes())
        sim = make_sim({"stock": {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1}})
        self.assertEqual(sim._cookable_dishes(), ["lau_mam"])

    def test_c2_standalone_quan_offers_all_six_dishes(self):  # AC-P2-C6
        sim = make_sim({"stock": RICH})
        self.assertEqual(sim._cookable_dishes(), SIX_DISHES)
        seen = set()
        for seed in range(1, 60):
            evs = run(make_sim({"stock": RICH}, seed=seed), 120)
            seen.add(named(evs, "customer_arrived")[0][1]["dish_id"])
        self.assertEqual(seen, set(SIX_DISHES))  # đủ 6 món đều có thể được gọi


class PlanFilter(unittest.TestCase):
    def test_c4_filter_applies_before_stock(self):  # AC-P2-C4
        for seed in range(1, 15):
            sim = make_sim({"stock": RICH}, seed=seed, allowed={"goi_bong_sung"})
            self.assertEqual(sim._cookable_dishes(), ["goi_bong_sung"])
            evs = run(sim, 120)
            self.assertEqual(named(evs, "customer_arrived")[0][1]["dish_id"], "goi_bong_sung")

    def test_c4_planned_dish_without_ingredients_gives_no_dish_even_if_others_cookable(self):  # AC-P2-C4
        sim = make_sim({"stock": {"ca_loc": 5}}, allowed={"goi_bong_sung"})  # có cá lóc nhưng không có trong kế hoạch
        evs = run(sim, 120)
        self.assertEqual([t for t, _ in named(evs, "no_dish")], [120])
        self.assertEqual(named(evs, "customer_arrived"), [])

    def test_c4_multi_dish_plan_only_picks_planned_dishes(self):  # AC-P2-C4 (Ngày 1 của day_plan)
        plan = {"ca_loc_nuong_trui", "goi_bong_sung"}
        seen = set()
        for seed in range(1, 40):
            evs = run(make_sim({"stock": RICH}, seed=seed, allowed=plan), 120)
            seen.add(named(evs, "customer_arrived")[0][1]["dish_id"])
        self.assertEqual(seen, plan)

    def test_c5_no_quota_customers_keep_ordering_beyond_planned_servings(self):  # AC-P2-C5
        sim = make_sim({"stock": {"ca_loc": 4}}, allowed={"ca_loc_nuong_trui"})  # kế hoạch giả định chỉ 1 suất
        evs = run(sim, 2820)
        self.assertEqual(len(named(evs, "customer_arrived")), 4)
        self.assertTrue(all(d["dish_id"] == "ca_loc_nuong_trui" for _, d in named(evs, "customer_arrived")))

    def test_c4_empty_plan_means_no_dish(self):  # AC-P2-C4
        evs = run(make_sim({"stock": RICH}, allowed=set()), 120)
        self.assertEqual([t for t, _ in named(evs, "no_dish")], [120])

    def test_c4_unknown_dish_in_plan_is_rejected(self):  # AC-P2-C4
        with self.assertRaises(BadInput):
            make_sim({"stock": RICH}, allowed={"mon_la"})

    def test_c4_filter_does_not_touch_fixture_customers(self):  # AC-P2-C4: fixture là dữ liệu dựng sẵn
        sim = make_sim({"stock": RICH, "customers": [cust("C1", "T1", "lau_mam")]}, allowed={"goi_bong_sung"})
        self.assertEqual(sim.customers[0]["dish_id"], "lau_mam")

    def test_c7_default_none_matches_unfiltered_behaviour(self):  # AC-P2-C7: không đổi hành vi Phase 1
        a = run(make_sim({"stock": RICH}, seed=3), 1100)
        b = run(make_sim({"stock": RICH}, seed=3, allowed=set(SIX_DISHES)), 1100)
        self.assertEqual(a, b)

    def test_c4_same_seed_same_choices(self):  # AC-P2-C7: tất định
        a = run(make_sim({"stock": RICH}, seed=9, allowed={"goi_bong_sung", "ca_keo_nuong"}), 2820)
        b = run(make_sim({"stock": RICH}, seed=9, allowed={"goi_bong_sung", "ca_keo_nuong"}), 2820)
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
