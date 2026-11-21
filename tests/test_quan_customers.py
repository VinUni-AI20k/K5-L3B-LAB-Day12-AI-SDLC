"""Lát 3 (minhtriet061203): khách quán — lịch đến, chọn món, giữ chỗ, kiên nhẫn, uy tín, fixture.

AC-P1-30..34 trong docs/plan/phase-1.md. Số liệu đọc từ game.contract.json, không hard-code.
Tên sự kiện / trường khách theo docs/contracts/README.md mục 3–4 (order_id = id khách).
"""

import copy
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim

from helpers import hold_items, tuning_v11, Workdir, events, read_jsonl, run_headless, write_json

V12 = "freshness" in load_contract()["tuning"]
TUNING = tuning_v11()  # v1.2 [THAY THẾ] kho đếm: giữ nhánh v1.1, luật v1.2 ở test_quan_v12_stock.py
Q = TUNING["quan"]
FIRST = Q["first_customer_tick"]
INTERVAL = int(round(Q["customer_interval_s"] * 60))
PATIENCE = int(round(Q["patience_s"] * 60))
IDLE = InputState((0.0, 0.0), set(), set())
PAY = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": TUNING["menu"]["ca_loc_nuong_trui"]["price"]}


def make(scenario=None, seed=1, inventory=None, tuning=None):
    return QuanSim(tuning or TUNING, scenario or {}, Streams(seed), IdAllocator(), inventory=inventory)


def run_until(sim, tick):
    """Chạy tới khi sim.phase_tick == tick; trả [(phase_tick, name, data)]."""
    out = []
    while sim.phase_tick < tick and not sim.done:
        for name, data in sim.step(IDLE):
            out.append((sim.phase_tick, name, data))
    return out


def two_tables():
    t = copy.deepcopy(TUNING)
    t["quan"]["tables"] = [{"id": "T2", "pos": [12, 2]}, {"id": "T1", "pos": [9, 2]}]
    return t


class Schedule(unittest.TestCase):
    """AC-P1-30: lịch theo phase_tick, bàn trống id nhỏ nhất, hết bàn thì bỏ lượt."""

    def test_first_customer_at_first_customer_tick(self):
        sim = make(inventory={"bong_sung": 2, "ca_loc": 1})
        ev = run_until(sim, FIRST)
        arrived = [e for e in ev if e[1] == "customer_arrived"]
        self.assertEqual(len(arrived), 1)
        self.assertEqual(arrived[0][0], FIRST)
        self.assertEqual(list(arrived[0][2]), ["order_id", "table_id", "dish_id"])
        self.assertEqual(arrived[0][2]["order_id"], "C1")
        self.assertEqual(arrived[0][2]["table_id"], Q["tables"][0]["id"])

    def test_next_arrival_after_interval_and_smallest_free_table(self):
        sim = make(inventory={"bong_sung": 10, "ca_loc": 10}, tuning=two_tables())
        ev = run_until(sim, FIRST + INTERVAL)
        arrived = [(tk, d["table_id"]) for tk, n, d in ev if n == "customer_arrived"]
        self.assertEqual(arrived, [(FIRST, "T1"), (FIRST + INTERVAL, "T2")])

    def test_no_free_table_skips_turn(self):
        one_table = copy.deepcopy(TUNING)  # v1.1 preset có 4 bàn; dựng quán 1 bàn để kiểm hết bàn
        one_table["quan"]["tables"] = one_table["quan"]["tables"][:1]
        sim = make(inventory={"bong_sung": 10, "ca_loc": 10}, tuning=one_table)
        ev = run_until(sim, FIRST + INTERVAL)
        names = [n for _, n, _ in ev]
        self.assertEqual(names.count("customer_arrived"), 1)
        self.assertNotIn("no_dish", names)
        self.assertEqual(len(sim.customers), 1)

    def test_random_customers_false_disables_schedule(self):
        sim = make({"random_customers": False, "stock": {"ca_loc": 5}})
        self.assertEqual([e for e in run_until(sim, FIRST + 1) if e[1] == "customer_arrived"], [])

    def test_runs_through_headless_jsonl(self):
        with Workdir() as w:
            inv = write_json(w.path("kho.json"), {"items": hold_items("bong_sung", "bong_sung", "ca_loc")})  # v1.2
            out = w.path("o.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "3", "--ticks", str(FIRST), "--inventory", inv,
                                     "--out", out)
            self.assertEqual(code, 0, err)
            arr = events(read_jsonl(out), "customer_arrived")
            self.assertEqual([e["tick"] for e in arr], [FIRST])


class DishChoice(unittest.TestCase):
    """AC-P1-31: chọn đều theo seed trong món đủ kho khả dụng; không món nào -> no_dish."""

    def test_only_cookable_dish_is_chosen(self):
        sim = make(inventory={"ca_loc": 1})
        ev = run_until(sim, FIRST)
        self.assertEqual([d["dish_id"] for _, n, d in ev if n == "customer_arrived"], ["ca_loc_nuong_trui"])

    def test_no_dish_when_stock_empty(self):
        sim = make(inventory={"bong_sung": 1})
        ev = run_until(sim, FIRST)
        self.assertEqual(ev, [(FIRST, "no_dish", {})])
        self.assertEqual(sim.customers, [])

    def test_available_excludes_reserved(self):
        # khách C1 đã giữ 1 cá lóc -> khả dụng 0 -> khách mới ở bàn T2 không có món
        t = two_tables()
        sim = make({"stock": {"ca_loc": 1},
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}]}, tuning=t)
        self.assertEqual(sim.available().get("ca_loc", 0), 0)
        ev = run_until(sim, FIRST)
        self.assertEqual([(n, d) for _, n, d in ev], [("no_dish", {})])

    def test_same_seed_same_choice_and_uniform_spread(self):
        # v1.1: 6 món -> kho đủ cho từng món (thêm ca_keo, keo_neo)
        stock = {"bong_sung": 2, "ca_loc": 1, "ca_linh": 3, "bong_dien_dien": 1, "ca_keo": 2, "keo_neo": 1}
        picks = []
        for seed in range(60):
            a, b = make(inventory=dict(stock), seed=seed), make(inventory=dict(stock), seed=seed)
            da = [d["dish_id"] for _, n, d in run_until(a, FIRST) if n == "customer_arrived"]
            db = [d["dish_id"] for _, n, d in run_until(b, FIRST) if n == "customer_arrived"]
            self.assertEqual(da, db)
            picks += da
        self.assertEqual(set(picks), set(TUNING["menu"]), "đủ món đều có thể được chọn")


class Reservation(unittest.TestCase):
    """AC-P1-32: giữ chỗ đúng công thức khi gọi; khách rời thì nhả giữ, bỏ món của đơn."""

    def test_reserve_recipe_on_order(self):
        sim = make(inventory={"ca_linh": 3, "bong_dien_dien": 1})
        run_until(sim, FIRST)
        c = sim.customers[0]
        self.assertEqual(c["dish_id"], "lau_ca_linh_dien_dien")
        self.assertEqual(c["reserved"], TUNING["menu"]["lau_ca_linh_dien_dien"]["recipe"])
        self.assertEqual((c["order_status"], c["state"], c["order_tick"]), ("reserved", "waiting", FIRST))
        self.assertEqual((c["base_price"], c["tip"], c["eat_ticks_left"]), (0, 0, 0), "lát 4 điền khi served")
        self.assertEqual(sim.stock, {"ca_linh": 3, "bong_dien_dien": 1}, "giữ chỗ không trừ tồn")
        self.assertEqual(sim.available(), {"ca_linh": 0, "bong_dien_dien": 0})

    def _assigned(self, **extra):
        payload = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}
        sc = {"random_customers": False,
              "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                             "order_status": "assigned", "patience_ticks_left": 1}]}
        if extra.get("on") == "hand":
            sc["hand"] = payload
        else:
            sc["stoves"] = [{"id": "B1", "state": "ready", "dish": payload}]
        return make(sc)

    def test_leave_drops_dish_in_hand(self):
        sim = self._assigned(on="hand")
        ev = run_until(sim, 1)
        self.assertEqual([n for _, n, _ in ev], ["customer_left"])
        self.assertEqual(sim.customers, [])
        self.assertIsNone(sim.hand)

    def test_leave_drops_dish_on_stove(self):
        sim = self._assigned(on="stove")
        run_until(sim, 1)
        self.assertEqual((sim.stoves[0]["state"], sim.stoves[0]["dish"]), ("idle", None))

    def test_reserved_released_on_patience_leave(self):
        sim = make({"stock": {"ca_loc": 1}, "random_customers": False,
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                   "patience_ticks_left": 2}]})
        self.assertEqual(sim.available()["ca_loc"], 0)
        run_until(sim, 2)
        self.assertEqual(sim.available()["ca_loc"], 1)


class Patience(unittest.TestCase):
    """AC-P1-33: kiên nhẫn 3600 tick; về 0 -> customer_left patience, uy tín −0.5, kẹp [0, 5]."""

    def test_patience_runs_out_after_full_patience(self):
        sim = make(inventory={"ca_loc": 1})
        ev = run_until(sim, FIRST + PATIENCE)
        left = [(tk, d) for tk, n, d in ev if n == "customer_left"]
        self.assertEqual(len(left), 1)
        tk, d = left[0]
        self.assertEqual(tk, FIRST + PATIENCE)
        self.assertEqual(d["reason"], "patience")
        self.assertEqual(list(d), ["order_id", "table_id", "reason", "reputation"])
        self.assertEqual((d["order_id"], d["table_id"]), ("C1", Q["tables"][0]["id"]))
        self.assertEqual(d["reputation"], sim.reputation, "uy tín SAU khi cộng delta (clarify #3)")
        self.assertAlmostEqual(sim.reputation, Q["reputation_initial"] + Q["left_reputation_delta"])

    def test_patience_snapshot_countdown(self):
        sim = make(inventory={"ca_loc": 1})
        run_until(sim, FIRST + 10)
        self.assertEqual(sim.snapshot()["customers"][0]["patience_ticks_left"], PATIENCE - 10)

    def test_reputation_clamped_at_min(self):
        sim = make({"stock": {"ca_loc": 1}, "reputation": 0.2, "random_customers": False,
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                   "patience_ticks_left": 1}]})
        run_until(sim, 1)
        self.assertEqual(sim.reputation, Q["reputation_min"])

    def test_eating_customer_does_not_lose_patience(self):
        sim = make({"stock": {}, "random_customers": False,
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "eating",
                                   "patience_ticks_left": 1, "eat_ticks_left": 600, "base_price": 60, "tip": 12}]})
        self.assertEqual(run_until(sim, 5), [])
        self.assertEqual(sim.customers[0]["patience_ticks_left"], 1)


class StepOrder(unittest.TestCase):
    """PRD-0 mục F (Quán): kiên nhẫn giảm ở bước 1, rời bàn ở bước 4 (sau interact), khách mới ở bước 5."""

    def _one(self, **kw):
        c = dict({"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "patience_ticks_left": 1}, **kw)
        return {"stock": {"ca_loc": 1}, "random_customers": False, "customers": [c]}

    def test_served_on_the_tick_patience_hits_zero_does_not_leave(self):
        class ServeInStep3(QuanSim):  # giả lập lát 4: phục vụ ở bước 3 (interact)
            def _move(self, inp):
                super()._move(inp)
                for c in self.customers:
                    c.update(state="eating", order_status="served", eat_ticks_left=600, reserved={})

        sim = ServeInStep3(TUNING, self._one(), Streams(1), IdAllocator())
        ev = sim.step(IDLE)
        self.assertEqual(ev, [])
        self.assertEqual(sim.customers[0]["patience_ticks_left"], 0, "bước 1 đã giảm về 0 trước khi phục vụ")

    def test_leave_then_new_customer_same_tick(self):
        sim = make({"stock": {"ca_loc": 2},
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                   "patience_ticks_left": FIRST}]})
        ev = run_until(sim, FIRST)
        self.assertEqual([(tk, n, d["order_id"]) for tk, n, d in ev],
                         [(FIRST, "customer_left", "C1"), (FIRST, "customer_arrived", "C2")])

    def test_closing_waiting_customer_leaves_without_penalty(self):
        sc = self._one(patience_ticks_left=100)
        sc["time_left_ticks"] = 1
        sim = make(sc)
        ev = sim.step(IDLE)
        self.assertEqual([n for n, _ in ev], ["customer_left", "quan_end"])
        self.assertEqual(ev[0][1]["reason"], "closing")
        self.assertEqual(sim.reputation, Q["reputation_initial"])
        self.assertEqual(sim.snapshot()["customers"], [])

    def test_patience_zero_at_closing_is_closing_not_patience(self):
        sc = self._one(patience_ticks_left=1)
        sc["time_left_ticks"] = 1
        sim = make(sc)
        ev = sim.step(IDLE)
        self.assertEqual(ev[0][1]["reason"], "closing")
        self.assertEqual(sim.reputation, Q["reputation_initial"])

    def test_no_new_customer_when_shift_ends(self):
        sim = make({"stock": {"ca_loc": 1}, "time_left_ticks": FIRST})
        ev = run_until(sim, FIRST)
        self.assertEqual([n for _, n, _ in ev], ["quan_end"])

    def test_schedule_uses_phase_tick_even_when_shift_shortened(self):
        sim = make({"stock": {"ca_loc": 1}, "time_left_ticks": FIRST + 1})
        ev = run_until(sim, FIRST)
        self.assertEqual([(tk, n) for tk, n, _ in ev], [(FIRST, "customer_arrived")])


class Fixture(unittest.TestCase):
    """AC-P1-34: fixture quan.customers + mâu thuẫn -> mã 2 (trước khi ghi output)."""

    def _code(self, block, extra=()):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"quan": block})
            code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--scenario", sc,
                                   "--out", w.path("o.jsonl"), *extra)
            return code

    def test_valid_fixture_snapshot(self):
        sim = make({"stock": {"ca_linh": 3, "bong_dien_dien": 1},
                    "customers": [{"id": "C4", "table_id": "T1", "dish_id": "lau_ca_linh_dien_dien",
                                   "patience_ticks_left": 100}]})
        c = sim.snapshot()["customers"][0]
        self.assertEqual((c["id"], c["state"], c["order_status"], c["patience_ticks_left"]),
                         ("C4", "waiting", "reserved", 100))
        self.assertEqual(c["reserved"], {"bong_dien_dien": 1, "ca_linh": 3})
        self.assertEqual(sim.snapshot()["tables"][0]["customer_id"], "C4")
        self.assertEqual(sim.ids.new("C"), "C5", "id khách mới nối tiếp fixture")

    @unittest.skipIf(V12, "v1.2 [THAY THẾ] stock/reserved theo lượng -> cá thể/id; kiểm ở test_quan_v12_stock.FixtureV12 / ScenarioFileV12")
    def test_valid_fixture_exit_0(self):
        self.assertEqual(self._code({"stock": {"ca_loc": 1},
                                     "customers": [{"id": "C1", "table_id": "T1",
                                                    "dish_id": "ca_loc_nuong_trui"}]}), 0)

    @unittest.skipIf(V12, "v1.2 [THAY THẾ] stock/reserved theo lượng -> cá thể/id; kiểm ở test_quan_v12_stock.FixtureV12 / ScenarioFileV12")
    def test_contradictions_exit_2(self):
        base = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}
        bad = [
            {"stock": {}, "customers": [base]},                                              # giữ chỗ quá kho
            {"stock": {"ca_loc": 1}, "customers": [dict(base, dish_id="pho")]},              # món lạ
            {"stock": {"ca_loc": 1}, "customers": [dict(base, state="angry")]},              # state lạ
            {"stock": {"ca_loc": 1}, "customers": [dict(base, patience_ticks_left=-1)]},     # bộ đếm âm
            {"stock": {"ca_loc": 1}, "customers": [dict(base, patience_ticks_left=PATIENCE + 1)]},
            {"stock": {"ca_loc": 1}, "customers": [dict(base, reserved={"ca_loc": 2})]},     # giữ sai công thức
            {"stock": {"ca_loc": 1}, "customers": [dict(base, mood=1)]},                     # trường lạ
            {"customers": [dict(base, state="eating", eat_ticks_left=600)]},                 # eating thiếu giá/tip
            {"customers": [dict(base, state="eating", eat_ticks_left=600, base_price=1, tip=0)]},  # giá sai
            {"stock": {"ca_loc": 1}, "customers": [dict(base, base_price=60)]},              # chờ mà có giá
            {"stock": {"ca_loc": 1}, "customers": [dict(base, order_status="served")]},      # chờ mà đã served
            {"customers": [dict(base, order_status="assigned")]},                            # assigned không có món
            {"customers": [dict(base, order_status="unfulfillable")],
             "hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}},  # unfulfillable có món
            {"stock": {"ca_loc": 1}, "customers": [dict(base, order_id="C1")]},              # trường cũ
            {"random_customers": "yes"},
            # liên kết payload món <-> đơn (PRD-0 mục D)
            {"hand": dict(PAY, order_id="C9")},                                              # liên kết thiếu
            {"customers": [dict(base, order_status="assigned")],
             "hand": dict(PAY, dish_id="goi_bong_sung")},                                    # món không khớp đơn
            {"customers": [dict(base, order_status="assigned")], "hand": dict(PAY, base_price=1)},
            {"customers": [dict(base, order_status="assigned")], "hand": PAY,
             "stoves": [{"id": "B1", "state": "ready", "dish": PAY}]},                       # bếp và tay cùng đơn
            {"customers": [dict(base, order_status="assigned")],
             "stoves": [{"id": "B1", "state": "cooking", "dish": PAY, "cook_ticks_left": 0}]},  # cooking timer 0
            {"stoves": [{"id": "B1", "state": "idle", "cook_ticks_left": 5}]},               # idle có timer
            {"stoves": [{"id": "B1", "state": "burnt"}]},
        ]
        for block in bad:
            with self.subTest(block=block):
                self.assertEqual(self._code(block), 2)

    @unittest.skipIf(V12, "v1.2 [THAY THẾ] stock/reserved theo lượng -> cá thể/id; kiểm ở test_quan_v12_stock.FixtureV12 / ScenarioFileV12")
    def test_valid_links_exit_0(self):
        base = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}
        ok = [
            {"stock": {"ca_loc": 1}, "customers": [dict(base, patience_ticks_left=0)]},      # timer không âm
            {"customers": [dict(base, order_status="assigned")], "hand": PAY},
            {"customers": [dict(base, order_status="assigned")],
             "stoves": [{"id": "B1", "state": "cooking", "dish": PAY, "cook_ticks_left": 30}]},
            {"customers": [dict(base, order_status="unfulfillable")]},
        ]
        for block in ok:
            with self.subTest(block=block):
                self.assertEqual(self._code(block), 0)

    @unittest.skipIf(V12, "v1.2 [THAY THẾ] stock/reserved theo lượng -> cá thể/id; kiểm ở test_quan_v12_stock.FixtureV12 / ScenarioFileV12")
    def test_reserved_over_inventory_file_exit_2(self):
        with Workdir() as w:
            inv = write_json(w.path("kho.json"), {"items": {"bong_sung": 1}})
            code = self._code({"customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung"}]},
                              extra=("--inventory", inv))
            self.assertEqual(code, 2)

    def test_reserved_over_inventory_raises_in_sim(self):
        with self.assertRaises(BadInput):
            make({"customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung"}]},
                 inventory={"bong_sung": 1})


if __name__ == "__main__":
    unittest.main()
