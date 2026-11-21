"""Lát 3 Phase 2 (minhtriet061203): AC-P2-31 (4 bàn, 6 món) và AC-P2-32 (lọc menu theo day_plan).

Số liệu đọc từ game.contract.json v1.1 (TICKET-02 mục 1.3, 2.1, 2.2), không hard-code.
"""

import unittest

from chonoi.contract import load_contract, recipe_sum
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator, sort_by_id
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim

from helpers import Workdir, events, read_jsonl, run_headless, write_json

TUNING = load_contract()["tuning"]
Q = TUNING["quan"]
MENU = TUNING["menu"]
PLAN = {p["day"]: p for p in TUNING["day_plan"]}
FIRST = Q["first_customer_tick"]
INTERVAL = int(round(Q["customer_interval_s"] * 60))
IDLE = InputState((0.0, 0.0), set(), set())


def make(scenario=None, seed=1, inventory=None, **kw):
    return QuanSim(TUNING, scenario or {}, Streams(seed), IdAllocator(), inventory=inventory, **kw)


def run_until(sim, tick):
    out = []
    while sim.phase_tick < tick and not sim.done:
        for name, data in sim.step(IDLE):
            out.append((sim.phase_tick, name, data))
    return out


def arrivals(ev):
    return [(tk, d["table_id"], d["dish_id"]) for tk, n, d in ev if n == "customer_arrived"]


def plenty():
    """Kho đủ cho mọi món nhiều lần (6 nguyên liệu)."""
    return {k: 50 for k in ("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo")}


class FourTables(unittest.TestCase):
    """AC-P2-31: 4 bàn T1–T4, khách vào bàn trống id nhỏ nhất, hết bàn bỏ lượt."""

    def test_preset_v11_has_four_tables_and_six_dishes(self):
        self.assertEqual([t["id"] for t in sort_by_id(Q["tables"])], ["T1", "T2", "T3", "T4"])
        self.assertEqual(len(MENU), 6)

    def test_customers_fill_tables_in_id_order(self):
        sim = make(inventory=plenty())
        n = len(Q["tables"])
        ev = run_until(sim, FIRST + (n - 1) * INTERVAL)
        got = arrivals(ev)
        self.assertEqual([(tk, tb) for tk, tb, _ in got],
                         [(FIRST + k * INTERVAL, t["id"]) for k, t in enumerate(sort_by_id(Q["tables"]))])
        self.assertEqual(len(sim.customers), n)

    def test_all_four_tables_busy_skips_turn(self):
        cust = [{"id": f"C{i}", "table_id": t["id"], "dish_id": "goi_bong_sung"}
                for i, t in enumerate(sort_by_id(Q["tables"]), start=1)]
        sim = make({"stock": {"bong_sung": 2 * len(cust) + 2}, "customers": cust})
        ev = run_until(sim, FIRST)
        self.assertEqual(ev, [], "hết bàn: bỏ lượt, không customer_arrived, không no_dish")

    def test_freed_smallest_table_is_reused(self):
        # T1, T3 có khách sắp rời; T2 có khách -> khách mới vào T1 (id nhỏ nhất đang trống)
        cust = [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "patience_ticks_left": FIRST},
                {"id": "C2", "table_id": "T2", "dish_id": "goi_bong_sung"},
                {"id": "C3", "table_id": "T3", "dish_id": "goi_bong_sung", "patience_ticks_left": FIRST}]
        sim = make({"stock": {"bong_sung": 8}, "customers": cust})
        ev = run_until(sim, FIRST)
        self.assertEqual([(n, d["table_id"]) for _, n, d in ev],
                         [("customer_left", "T1"), ("customer_left", "T3"), ("customer_arrived", "T1")])

    def test_four_tables_through_headless_snapshot(self):
        with Workdir() as w:
            inv = write_json(w.path("kho.json"), {"items": plenty()})
            out = w.path("o.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "5", "--ticks", str(FIRST + 3 * INTERVAL),
                                     "--inventory", inv, "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            self.assertEqual([e["data"]["table_id"] for e in events(rows, "customer_arrived")],
                             ["T1", "T2", "T3", "T4"])
            last = [r for r in rows if r["type"] == "snapshot"][-1]
            self.assertEqual([t["customer_id"] for t in last["tables"]], ["C1", "C2", "C3", "C4"])


class SixDishes(unittest.TestCase):
    """AC-P2-31: quán độc lập (không có kế hoạch) chọn trong cả 6 món."""

    def test_standalone_uses_all_six_dishes(self):
        picks = set()
        for seed in range(80):
            sim = make(inventory=plenty(), seed=seed)
            picks |= {dish for _, _, dish in arrivals(run_until(sim, FIRST))}
        self.assertEqual(picks, set(MENU))

    def test_new_dish_only_when_its_recipe_is_available(self):
        sim = make(inventory={"ca_keo": 2})
        self.assertEqual([d for _, _, d in arrivals(run_until(sim, FIRST))], ["ca_keo_nuong"])
        sim = make(inventory=dict(recipe_sum({"lau_mam": 1}, MENU)))
        self.assertEqual([d for _, _, d in arrivals(run_until(sim, FIRST))], ["lau_mam"])
        self.assertEqual(sim.available(), {k: 0 for k in MENU["lau_mam"]["recipe"]})


class DayPlanFilter(unittest.TestCase):
    """AC-P2-32: trong day, lọc theo id món trong kế hoạch TRƯỚC khi lọc kho khả dụng."""

    def test_only_plan_dishes_even_if_other_dishes_cookable(self):
        plan = sorted(PLAN[1]["dishes"])
        picks = set()
        for seed in range(40):
            sim = make(inventory=plenty(), seed=seed, menu_filter=plan)
            picks |= {d for _, _, d in arrivals(run_until(sim, FIRST + 3 * INTERVAL))}
        self.assertEqual(picks, set(plan))

    def test_no_dish_when_only_off_plan_dishes_are_cookable(self):
        # kho chỉ đủ cá kèo nướng (ngoài kế hoạch D1) -> no_dish
        sim = make(inventory={"ca_keo": 2}, menu_filter=sorted(PLAN[1]["dishes"]))
        ev = run_until(sim, FIRST)
        self.assertEqual([(n, d) for _, n, d in ev], [("no_dish", {})])

    def test_plan_then_availability(self):
        # D1: ca_loc_nuong_trui, goi_bong_sung; chỉ đủ cá lóc -> luôn ca_loc_nuong_trui
        for seed in range(20):
            sim = make(inventory={"ca_loc": 1, "ca_keo": 9}, seed=seed, menu_filter=sorted(PLAN[1]["dishes"]))
            self.assertEqual([d for _, _, d in arrivals(run_until(sim, FIRST))], ["ca_loc_nuong_trui"])

    def test_keeps_ordering_after_planned_servings(self):
        # kế hoạch 1 suất gỏi, kho đủ 3 suất -> 3 khách đều gọi được gỏi (không có hạn mức số suất)
        sim = make(inventory={"bong_sung": 6}, menu_filter=["goi_bong_sung"])
        got = arrivals(run_until(sim, FIRST + 3 * INTERVAL))
        self.assertEqual([d for _, _, d in got], ["goi_bong_sung"] * 3)
        self.assertEqual([tb for _, tb, _ in got], ["T1", "T2", "T3"])

    def test_same_seed_same_choices_with_plan(self):
        plan = sorted(PLAN[3]["dishes"])
        a = make(inventory=plenty(), seed=9, menu_filter=plan)
        b = make(inventory=plenty(), seed=9, menu_filter=plan)
        self.assertEqual(arrivals(run_until(a, FIRST + 3 * INTERVAL)), arrivals(run_until(b, FIRST + 3 * INTERVAL)))

    def test_every_day_plan_dish_is_in_menu(self):
        for day, p in PLAN.items():
            make(menu_filter=sorted(p["dishes"]))  # không ném lỗi

    def test_unknown_plan_dish_is_bad_input(self):
        with self.assertRaises(BadInput):
            make(menu_filter=["pho_bo"])

    def test_fixture_off_plan_is_bad_input(self):
        plan = sorted(PLAN[1]["dishes"])
        with self.assertRaises(BadInput):
            make({"stock": {"ca_keo": 2}, "random_customers": False,
                  "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_keo_nuong"}]}, menu_filter=plan)
        pay = {"order_id": "C1", "dish_id": "ca_keo_nuong", "base_price": MENU["ca_keo_nuong"]["price"]}
        with self.assertRaises(BadInput):
            make({"random_customers": False, "hand": pay,
                  "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_keo_nuong",
                                 "order_status": "assigned"}]}, menu_filter=plan)

    def test_fixture_in_plan_is_ok(self):
        sim = make({"stock": {"ca_loc": 1}, "random_customers": False,
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}]},
                   menu_filter=sorted(PLAN[1]["dishes"]))
        self.assertEqual(len(sim.customers), 1)


class CarryOverState(unittest.TestCase):
    """Hợp đồng mục 5.3: runner day truyền money/earned/reputation vào QuanSim."""

    def test_initial_money_earned_reputation(self):
        sim = make(money=150, earned=300, reputation=4.5)
        self.assertEqual((sim.money, sim.earned, sim.reputation, sim.shift_earned), (150, 300, 4.5, 0))

    def test_defaults_unchanged_for_standalone(self):
        sim = make()
        self.assertEqual((sim.money, sim.earned, sim.reputation), (0, 0, Q["reputation_initial"]))


if __name__ == "__main__":
    unittest.main()
