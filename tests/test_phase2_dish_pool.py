"""Kiểm tra lọc món theo kế hoạch ngày (dish_pool) và bếp ưu tiên chọn đơn cũ nhất:
1. dish_pool=None: khách chọn từ các món nấu được trong toàn bộ menu.
2. dish_pool=["goi_bong_sung"]: chỉ gọi món trong pool bất kể seed (1..20).
3. dish_pool=["goi_bong_sung"], thiếu bông súng: tick 120 phát no_dish dù ca_loc nấu được.
4. dish_pool không hợp lệ (món lạ hoặc rỗng) -> BadInput.
5. dish_pool trùng lặp hoặc dạng dict -> được loại bỏ trùng và sắp xếp id (Unicode).
6. Tính tất định: cùng seed và dish_pool ra cùng chuỗi món của 4 khách đầu.
7. Bếp ưu tiên đơn có order_tick nhỏ hơn, nếu bằng nhau ưu tiên id bàn nhỏ hơn.
"""

import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim
from helpers import Workdir, read_jsonl, run_headless, write_json


def _empty_inp():
    return InputState((0.0, 0.0), set(), set())


class TestPhase2DishPool(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        contract = load_contract()
        cls.tuning = contract["tuning"]

    def test_dish_pool_none_chooses_from_all_available(self):
        """dish_pool=None, kho nấu được 3 món: khách chọn món trong {ca_loc_nuong_trui, goi_bong_sung, canh_chua_ca_loc} và đa dạng qua 30 seed."""
        seen_dishes = set()
        allowed = {"ca_loc_nuong_trui", "goi_bong_sung", "canh_chua_ca_loc"}
        stock = {"ca_loc": 1, "bong_sung": 2, "bong_dien_dien": 1}

        for seed in range(1, 31):
            sim = QuanSim(self.tuning, {"stock": stock}, Streams(seed), IdAllocator(), dish_pool=None)
            inp = _empty_inp()
            events = []
            for _ in range(120):
                events.extend(sim.step(inp))

            arrived = [e for e in events if e[0] == "customer_arrived"]
            self.assertEqual(len(arrived), 1, f"Seed {seed} phải có đúng 1 customer_arrived")
            dish_id = arrived[0][1]["dish_id"]
            self.assertIn(dish_id, allowed, f"Seed {seed}: món {dish_id} không nằm trong {allowed}")
            seen_dishes.add(dish_id)

        self.assertGreaterEqual(len(seen_dishes), 2, "dish_pool=None phải sinh ít nhất 2 món khác nhau qua 30 seed")

    def test_dish_pool_specific_dish_always_chosen(self):
        """dish_pool=['goi_bong_sung'], stock đủ: khách C1 luôn gọi goi_bong_sung với mọi seed 1..20."""
        for seed in range(1, 21):
            streams = Streams(seed)
            ids = IdAllocator()
            scenario = {"stock": {"ca_loc": 5, "bong_sung": 2}}
            sim = QuanSim(self.tuning, scenario, streams, ids, dish_pool=["goi_bong_sung"])
            inp = _empty_inp()
            events = []
            for _ in range(120):
                events.extend(sim.step(inp))

            arrived = [e for e in events if e[0] == "customer_arrived"]
            self.assertEqual(len(arrived), 1, f"Seed {seed} phải có đúng 1 customer_arrived")
            self.assertEqual(
                arrived[0][1]["dish_id"], "goi_bong_sung",
                f"Seed {seed}: khách C1 phải gọi goi_bong_sung"
            )

    def test_dish_pool_unaffordable_planned_dish_emits_no_dish(self):
        """dish_pool=['goi_bong_sung'], thiếu bông súng: tick 120 phát no_dish dù ca_loc_nuong_trui nấu được."""
        streams = Streams(42)
        ids = IdAllocator()
        scenario = {"stock": {"ca_loc": 5}}
        sim = QuanSim(self.tuning, scenario, streams, ids, dish_pool=["goi_bong_sung"])
        inp = _empty_inp()
        events = []
        for _ in range(120):
            events.extend(sim.step(inp))

        arrived = [e for e in events if e[0] == "customer_arrived"]
        no_dish = [e for e in events if e[0] == "no_dish"]
        self.assertEqual(len(arrived), 0, "Không được có customer_arrived khi món trong kế hoạch thiếu nguyên liệu")
        self.assertEqual(len(no_dish), 1, "Phải phát event no_dish ở tick 120")

    def test_dish_pool_invalid_raises_bad_input(self):
        """dish_pool=['khong_co'] hoặc rỗng [] -> BadInput."""
        streams = Streams(42)
        ids = IdAllocator()
        scenario = {"stock": {"ca_loc": 5}}

        with self.assertRaises(BadInput):
            QuanSim(self.tuning, scenario, streams, ids, dish_pool=["khong_co"])

        with self.assertRaises(BadInput):
            QuanSim(self.tuning, scenario, streams, ids, dish_pool=[])

    def test_dish_pool_duplicates_are_deduped(self):
        """dish_pool có món trùng lặp hoặc dạng dict đều được khử trùng và sắp xếp id (Unicode)."""
        sim1 = QuanSim(
            self.tuning, {}, Streams(1), IdAllocator(),
            dish_pool=["goi_bong_sung", "goi_bong_sung", "ca_loc_nuong_trui"]
        )
        self.assertEqual(sim1.dish_pool, ["ca_loc_nuong_trui", "goi_bong_sung"])

        sim2 = QuanSim(
            self.tuning, {}, Streams(1), IdAllocator(),
            dish_pool={"goi_bong_sung": 3, "ca_loc_nuong_trui": 3}
        )
        self.assertEqual(sim2.dish_pool, ["ca_loc_nuong_trui", "goi_bong_sung"])

    def test_dish_pool_determinism_first_four_customers(self):
        """Tất định: cùng seed và dish_pool thì chạy 2 lần ra cùng chuỗi dish_id của 4 khách đầu."""
        pool = ["ca_loc_nuong_trui", "goi_bong_sung", "lau_ca_linh_dien_dien"]
        stock = {"ca_loc": 10, "bong_sung": 10, "ca_linh": 10, "bong_dien_dien": 10}

        def _run_to_four_customers(seed):
            sim = QuanSim(self.tuning, {"stock": stock}, Streams(seed), IdAllocator(), dish_pool=pool)
            inp = _empty_inp()
            dishes = []
            for _ in range(2820):
                for e in sim.step(inp):
                    if e[0] == "customer_arrived":
                        dishes.append(e[1]["dish_id"])
            return dishes

        dishes_run1 = _run_to_four_customers(123)
        dishes_run2 = _run_to_four_customers(123)
        self.assertEqual(len(dishes_run1), 4)
        self.assertEqual(dishes_run1, dishes_run2)
        for d in dishes_run1:
            self.assertIn(d, pool)

    def test_stove_picks_oldest_order_same_order_tick_lower_table_id(self):
        """Bếp B1 ưu tiên đơn cùng order_tick nhưng có id bàn nhỏ hơn (T1 < T2)."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "random_customers": False,
                    "player": {"pos": [2, 8]},
                    "stock": {"ca_loc": 2},
                    "customers": [
                        {"id": "C1", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "order_tick": 0},
                        {"id": "C2", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_tick": 0},
                    ],
                }
            })
            inp = write_json(w.path("inp.json"), {"frames": [{"tick": 0, "interact": True}]})
            out = w.path("out.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "42", "--ticks", "1",
                                     "--scenario", sc, "--inputs", inp, "--out", out)
            self.assertEqual(code, 0, f"Error: {err}")
            rows = read_jsonl(out)
            evs = [r for r in rows if r["type"] == "event" and r["name"] == "cook_started"]
            self.assertEqual(len(evs), 1)
            self.assertEqual(evs[0]["tick"], 1)
            self.assertEqual(evs[0]["data"]["stove_id"], "B1")
            self.assertEqual(evs[0]["data"]["order_id"], "C2")

    def test_stove_picks_oldest_order_different_order_tick(self):
        """Bếp B1 ưu tiên đơn có order_tick cũ hơn (order_tick 0 < 120) bất kể bàn (T2 thắng T1)."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "random_customers": True,
                    "player": {"pos": [2, 8]},
                    "stock": {"ca_loc": 2},
                    "customers": [
                        {"id": "C1", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "order_tick": 0},
                    ],
                }
            })
            inp = write_json(w.path("inp.json"), {"frames": [{"tick": 120, "interact": True}]})
            out = w.path("out.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "42", "--ticks", "121",
                                     "--scenario", sc, "--inputs", inp, "--out", out)
            self.assertEqual(code, 0, f"Error: {err}")
            rows = read_jsonl(out)

            # Khách mới C2 đến ở tick 120 vào bàn T1 (bàn trống id nhỏ nhất)
            arrived_evs = [r for r in rows if r["type"] == "event" and r["name"] == "customer_arrived" and r["tick"] == 120]
            self.assertEqual(len(arrived_evs), 1)
            self.assertEqual(arrived_evs[0]["data"]["table_id"], "T1")
            self.assertEqual(arrived_evs[0]["data"]["order_id"], "C2")

            # Bếp B1 bắt đầu nấu ở tick 121 nhận đơn C1 (order_tick 0 < 120)
            cook_evs = [r for r in rows if r["type"] == "event" and r["name"] == "cook_started"]
            self.assertEqual(len(cook_evs), 1)
            self.assertEqual(cook_evs[0]["tick"], 121)
            self.assertEqual(cook_evs[0]["data"]["stove_id"], "B1")
            self.assertEqual(cook_evs[0]["data"]["order_id"], "C1")


if __name__ == "__main__":
    unittest.main()
