"""Unit test phần TV3 — vòng đời khách trong `chonoi/sim/quan.py` + kiểm mâu thuẫn scenario quan.

Số liệu đọc từ game.contract.json qua `load_contract()` (không hard-code): first_customer_tick=120,
customer_interval_s=15 (900 ticks), patience_s=60 (3600 ticks), left_reputation_delta=-0.5,
reputation_min=0, reputation_max=5.
Chạy: PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
"""

import copy
import os
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.scenario import load_scenario
from chonoi.sim.quan import TICK, QuanSim

from helpers import Workdir, run_headless, write_json

TUNING = load_contract()["tuning"]
Q = TUNING["quan"]
MENU = TUNING["menu"]
FIRST = Q["first_customer_tick"]                        # 120
INTERVAL = int(round(Q["customer_interval_s"] * TICK))  # 900
PATIENCE = int(round(Q["patience_s"] * TICK))           # 3600
IDLE = InputState((0, 0), frozenset(), frozenset())


def full_stock():
    return {"ca_loc": 9, "ca_linh": 9, "bong_sung": 9, "bong_dien_dien": 9}


def two_tables_tuning():
    """Nhân bản tuning thêm bàn T2 (fixture test; KHÔNG sửa game.contract.json)."""
    t = copy.deepcopy(TUNING)
    t["quan"]["tables"] = list(Q["tables"]) + [{"id": "T2", "pos": [Q["bounds"]["x"][1] - 1, 2]}]
    return t


def make_sim(scenario=None, seed=1, stock=None, tuning=TUNING):
    sc = dict(scenario or {})
    if stock is not None:
        sc["stock"] = stock
    return QuanSim(tuning, sc, Streams(seed), IdAllocator())


def run_steps(sim, n):
    evs = []
    for _ in range(n):
        evs.extend(sim.step(IDLE))
    return evs


def by_name(evs, name):
    return [data for ename, data in evs if ename == name]


def waiting_customer(cid="C1", dish_id="ca_loc_nuong_trui", patience=PATIENCE):
    # khách waiting không khai base_price/tip (chỉ khách eating phải khai, xem Commit 1)
    return {"id": cid, "table_id": "T1", "dish_id": dish_id, "order_tick": 0, "state": "waiting",
            "order_status": "reserved", "patience_ticks_left": patience, "eat_ticks_left": 0,
            "reserved": dict(MENU[dish_id]["recipe"])}


class Schedule(unittest.TestCase):
    """Lịch khách: first_customer_tick, customer_interval_s, hết bàn thì bỏ lượt."""

    def test_den_dung_first_tick_va_lap_theo_interval(self):
        sim = make_sim(tuning=two_tables_tuning(), stock=full_stock())
        evs = run_steps(sim, FIRST - 1)
        self.assertEqual(by_name(evs, "customer_arrived"), [], "chưa tới lịch không được có khách")
        evs += run_steps(sim, 1)
        arr = by_name(evs, "customer_arrived")
        self.assertEqual(len(arr), 1)
        self.assertEqual(sim.phase_tick, FIRST)
        self.assertEqual(arr[0]["table_id"], "T1", "bàn trống có id nhỏ nhất")
        self.assertEqual(arr[0]["order_id"], "C1")
        evs += run_steps(sim, INTERVAL - 1)
        self.assertEqual(len(by_name(evs, "customer_arrived")), 1, "giữa hai lịch không đến thêm")
        evs += run_steps(sim, 1)
        arr = by_name(evs, "customer_arrived")
        self.assertEqual(len(arr), 2, f"đúng lịch {FIRST} + {INTERVAL} ticks phải có khách thứ hai")
        self.assertEqual(arr[1]["table_id"], "T2")
        self.assertEqual(arr[1]["order_id"], "C2")
        evs += run_steps(sim, INTERVAL)
        self.assertEqual(len(by_name(evs, "customer_arrived")), 2, "hết bàn trống -> bỏ lượt")

    def test_mot_ban_khong_den_them_khi_dang_co_khach(self):
        sim = make_sim(stock=full_stock())  # tuning chỉ có T1
        evs = run_steps(sim, FIRST + INTERVAL)
        self.assertEqual(len(by_name(evs, "customer_arrived")), 1)
        self.assertEqual(by_name(evs, "no_dish"), [], "hết bàn là bỏ lượt im lặng, không no_dish")

    def test_random_customers_false_thi_khong_sinh_khach(self):
        sim = make_sim({"random_customers": False}, stock=full_stock())
        evs = run_steps(sim, FIRST + INTERVAL)
        self.assertEqual(by_name(evs, "customer_arrived"), [])
        self.assertEqual(by_name(evs, "no_dish"), [])


class DishChoice(unittest.TestCase):
    """Chọn món tất định theo seed, giữ chỗ đúng recipe, ảnh hưởng khách kế tiếp."""

    def _first_arrival(self, seed, stock):
        sim = make_sim(tuning=two_tables_tuning(), seed=seed, stock=stock)
        evs = run_steps(sim, FIRST)
        return sim, by_name(evs, "customer_arrived")

    def test_tat_dinh_theo_seed_va_giu_cho_dung_recipe(self):
        stock = {"ca_loc": 2, "bong_sung": 2, "ca_linh": 2, "bong_dien_dien": 2}
        s1, a1 = self._first_arrival(7, stock)
        s2, a2 = self._first_arrival(7, stock)
        self.assertEqual(a1, a2, "cùng seed phải cho cùng event")
        self.assertEqual(s1.customers, s2.customers)
        c = s1.customers[0]
        self.assertEqual(c["reserved"], dict(MENU[c["dish_id"]]["recipe"]))
        self.assertEqual(c["order_tick"], FIRST)
        self.assertEqual(c["state"], "waiting")
        self.assertEqual(c["order_status"], "reserved")
        _, a3 = self._first_arrival(8, stock)
        self.assertIn(a3[0]["dish_id"], MENU, "khác seed vẫn phải chọn món trong menu")

    def test_kho_chi_du_mot_mon_thi_chon_dung_mon_do(self):
        stock = {"ca_linh": 3, "bong_dien_dien": 1}  # chỉ đủ lau_ca_linh_dien_dien
        sim, arr = self._first_arrival(1, stock)
        self.assertEqual(len(arr), 1)
        self.assertEqual(arr[0]["dish_id"], "lau_ca_linh_dien_dien")
        self.assertEqual(sim.customers[0]["reserved"], {"ca_linh": 3, "bong_dien_dien": 1})
        for k, n in sim.customers[0]["reserved"].items():
            self.assertEqual(sim._available()[k], stock[k] - n)

    def test_giu_cho_khien_khach_sau_khong_chon_duoc_mon(self):
        sim = make_sim(tuning=two_tables_tuning(), seed=7, stock={"bong_sung": 2})
        evs = run_steps(sim, FIRST)
        arr = by_name(evs, "customer_arrived")
        self.assertEqual(len(arr), 1)
        self.assertEqual(arr[0]["dish_id"], "goi_bong_sung", "món duy nhất đủ nguyên liệu")
        self.assertEqual(sim.customers[0]["reserved"], {"bong_sung": 2})
        self.assertEqual(sim._available().get("bong_sung"), 0, "phần khả dụng đã bị khách 1 giữ hết")
        evs += run_steps(sim, INTERVAL)  # lịch kế: bàn T2 trống nhưng không còn món khả dụng
        self.assertEqual(len(by_name(evs, "customer_arrived")), 1, "khách 2 không thể đến vì hết món")
        self.assertEqual(by_name(evs, "no_dish"), [{}])


class Patience(unittest.TestCase):
    """Hết kiên nhẫn: customer_left reason=patience, trừ uy tín, nhả reserved, kẹp min."""

    def test_het_kien_nhan_roi_ban_va_giam_uy_tin(self):
        sim = make_sim({"customers": [waiting_customer("C1", patience=PATIENCE)]}, stock={"ca_loc": 1})
        evs = run_steps(sim, PATIENCE)
        left = by_name(evs, "customer_left")
        self.assertEqual(len(left), 1)
        self.assertEqual(left[0]["reason"], "patience")
        self.assertEqual(left[0]["order_id"], "C1")
        self.assertEqual(left[0]["table_id"], "T1")
        self.assertEqual(left[0]["reputation"], Q["reputation_initial"] + Q["left_reputation_delta"])
        self.assertEqual(sim.reputation, Q["reputation_initial"] + Q["left_reputation_delta"])
        self.assertEqual(sim.customers, [])
        self.assertEqual(sim._available().get("ca_loc"), 1, "khách rời phải nhả reserved")
        self.assertFalse(sim.done, "còn giờ thì chưa quan_end")

    def test_uy_tin_kep_khong_xuong_duoi_reputation_min(self):
        sim = make_sim({"reputation": 0.4,
                        "customers": [waiting_customer("C1", patience=1)]}, stock={"ca_loc": 1})
        run_steps(sim, 1)
        self.assertEqual(sim.reputation, Q["reputation_min"], "0.4 - 0.5 bị kẹp tại reputation_min")
        sim.customers.append(waiting_customer("C2", patience=0))
        evs = run_steps(sim, 1)
        self.assertEqual([d["order_id"] for d in by_name(evs, "customer_left")], ["C2"])
        self.assertEqual(sim.reputation, Q["reputation_min"], "rời tiếp vẫn không xuống dưới min")


class Closing(unittest.TestCase):
    """Hết ca: khách waiting rời với reason=closing, không trừ uy tín, quan_end sau cùng."""

    def test_het_ca_closing_va_quan_end(self):
        sim = make_sim({"time_left_ticks": 1, "customers": [waiting_customer("C1")]}, stock={"ca_loc": 1})
        evs = run_steps(sim, 1)
        left = by_name(evs, "customer_left")
        end = by_name(evs, "quan_end")
        self.assertEqual(len(left), 1)
        self.assertEqual(left[0]["reason"], "closing")
        self.assertEqual(left[0]["reputation"], Q["reputation_initial"], "closing không trừ uy tín")
        self.assertEqual(sim.reputation, Q["reputation_initial"])
        self.assertEqual(len(end), 1)
        self.assertEqual(end[0]["reason"], "time")
        self.assertLess(evs.index(("customer_left", left[0])), evs.index(("quan_end", end[0])),
                        "phải dọn khách closing trước khi phát quan_end")
        self.assertTrue(sim.done and sim.reason == "time")
        self.assertEqual(sim.customers, [])


class NoDish(unittest.TestCase):
    """Bàn trống nhưng kho không đủ nguyên liệu cho món nào -> no_dish, không sinh khách."""

    def test_no_dish_khi_kho_rong(self):
        sim = make_sim(stock={})
        evs = run_steps(sim, FIRST)
        self.assertEqual(by_name(evs, "customer_arrived"), [])
        self.assertEqual(by_name(evs, "no_dish"), [{}])
        self.assertEqual(sim.customers, [])
        self.assertEqual(sim._available(), {})


class ScenarioValidation(unittest.TestCase):
    """Kiểm mâu thuẫn quan qua load_scenario (BadInput) và headless (mã 2)."""

    def _load(self, block):
        with Workdir() as w:
            load_scenario(write_json(w.path("sc.json"), {"quan": block}), "quan", TUNING)

    def test_reserved_vuot_stock_exit_2(self):
        block = {"stock": {"ca_linh": 2, "bong_dien_dien": 1},
                 "customers": [{"id": "C1", "table_id": "T1", "dish_id": "lau_ca_linh_dien_dien"}]}
        with self.assertRaises(BadInput):
            self._load(block)

    def test_eating_thieu_gia_hoac_tip_exit_2(self):
        with self.assertRaises(BadInput):
            self._load({"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                       "state": "eating", "order_status": "served",
                                       "eat_ticks_left": 10, "base_price": 60}]})  # thiếu tip
        with self.assertRaises(BadInput):
            self._load({"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                       "state": "eating", "order_status": "served",
                                       "eat_ticks_left": 10, "tip": 5}]})  # thiếu base_price

    def test_assigned_khong_co_mon_exit_2(self):
        block = {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                "order_status": "assigned", "reserved": {}}]}
        with self.assertRaises(BadInput):
            self._load(block)

    def test_headless_tra_ma_2(self):
        with Workdir() as w:
            out = w.path("o.jsonl")
            blocks = (
                {"stock": {"ca_linh": 2, "bong_dien_dien": 1},
                 "customers": [{"id": "C1", "table_id": "T1", "dish_id": "lau_ca_linh_dien_dien"}]},
                {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                "state": "eating", "order_status": "served",
                                "eat_ticks_left": 10, "base_price": 60}]},
                {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                "order_status": "assigned", "reserved": {}}]},
            )
            for block in blocks:
                sc = write_json(w.path("sc.json"), {"quan": block})
                code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                         "--scenario", sc, "--out", out)
                self.assertEqual(code, 2, (block, err))
                self.assertFalse(os.path.exists(out), "lỗi đầu vào phải thoát trước khi ghi đầu ra")

    def test_headless_ma_0_voi_khach_hop_le(self):
        with Workdir() as w:
            out = w.path("o.jsonl")
            sc = write_json(w.path("sc.json"), {"quan": {"stock": {"ca_loc": 1},
                                                         "customers": [waiting_customer("C1")]}})
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                     "--scenario", sc, "--out", out)
            self.assertEqual(code, 0, err)


if __name__ == "__main__":
    unittest.main()
