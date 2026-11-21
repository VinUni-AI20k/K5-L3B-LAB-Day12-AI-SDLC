"""Test Phase 2 cho TV4 (AnhQuanHANU): ShopSim (Nâng cấp) và Mở rộng Cháy món (burn)."""

import unittest

from chonoi.sim.shop import ShopSim
from chonoi.sim.quan import QuanSim
from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.rng import Streams


class DummyInput:
    def __init__(self, move=(0.0, 0.0), held=None, edges=None, buy=None):
        self.move = move
        self.held = held or {}
        self._edges = edges or set()
        self.buy = buy

    def pressed(self, name: str) -> bool:
        return name in self._edges


class TestShopTV4(unittest.TestCase):
    def test_shop_buy_oxygen_and_hp_success_and_failures(self):
        """Kiểm tra mua oxy và hp: thành công, thiếu tiền (funds), vượt cấp (max_level), lệnh lạ (unknown)."""
        tuning = load_contract()["tuning"]
        state = {
            "money": 1000,
            "earned": 1000,
            "reputation": 3.2,
            "upgrades": {"oxygen": 0, "hp": 0},
            "active_upgrades": {"oxygen": 0, "hp": 0},
            "time_left_ticks": 600,
        }
        shop = ShopSim(tuning, state)

        # 1. Mua oxygen cấp 1 (giá 200)
        ev1 = shop.step(DummyInput(buy="oxygen"))
        bought1 = [e for e in ev1 if e[0] == "bought"]
        self.assertEqual(len(bought1), 1)
        self.assertEqual(bought1[0][1]["upgrade"], "oxygen")
        self.assertEqual(bought1[0][1]["level"], 1)
        self.assertEqual(bought1[0][1]["price"], 200)
        self.assertEqual(bought1[0][1]["money"], 800)
        self.assertEqual(shop.upgrades["oxygen"], 1)

        # 2. Mua oxygen cấp 2 (giá 400)
        ev2 = shop.step(DummyInput(buy="oxygen"))
        bought2 = [e for e in ev2 if e[0] == "bought"]
        self.assertEqual(len(bought2), 1)
        self.assertEqual(bought2[0][1]["level"], 2)
        self.assertEqual(bought2[0][1]["money"], 400)
        self.assertEqual(shop.upgrades["oxygen"], 2)

        # 3. Mua oxygen tiếp khi đã max level -> buy_failed (max_level)
        ev3 = shop.step(DummyInput(buy="oxygen"))
        failed3 = [e for e in ev3 if e[0] == "buy_failed"]
        self.assertEqual(len(failed3), 1)
        self.assertEqual(failed3[0][1]["reason"], "max_level")

        # 4. Mua hp cấp 1 (giá 250) với 400 tiền -> còn 150 tiền
        ev4 = shop.step(DummyInput(buy="hp"))
        bought4 = [e for e in ev4 if e[0] == "bought"]
        self.assertEqual(len(bought4), 1)
        self.assertEqual(bought4[0][1]["level"], 1)
        self.assertEqual(bought4[0][1]["money"], 150)
        self.assertEqual(shop.upgrades["hp"], 1)

        # 5. Mua hp cấp 2 (giá 500) khi chỉ còn 150 tiền -> buy_failed (funds)
        ev5 = shop.step(DummyInput(buy="hp"))
        failed5 = [e for e in ev5 if e[0] == "buy_failed"]
        self.assertEqual(len(failed5), 1)
        self.assertEqual(failed5[0][1]["reason"], "funds")

        # 6. Lệnh lạ -> buy_failed (unknown)
        ev6 = shop.step(DummyInput(buy="sung_laser"))
        failed6 = [e for e in ev6 if e[0] == "buy_failed"]
        self.assertEqual(len(failed6), 1)
        self.assertEqual(failed6[0][1]["reason"], "unknown")

    def test_shop_exit_by_button_and_by_timeout(self):
        """Kiểm tra đóng shop bằng nút shop_done và bằng timeout 600 tick."""
        tuning = load_contract()["tuning"]

        # Đóng bằng nút shop_done
        shop1 = ShopSim(tuning, {"money": 500, "time_left_ticks": 600})
        ev1 = shop1.step(DummyInput(edges={"shop_done"}))
        end1 = [e for e in ev1 if e[0] == "shop_end"]
        self.assertEqual(len(end1), 1)
        self.assertEqual(end1[0][1]["reason"], "done")
        self.assertTrue(shop1.done)

        # Đóng bằng timeout (hết 600 ticks)
        shop2 = ShopSim(tuning, {"money": 500, "time_left_ticks": 1})
        ev2 = shop2.step(DummyInput())
        end2 = [e for e in ev2 if e[0] == "shop_end"]
        self.assertEqual(len(end2), 1)
        self.assertEqual(end2[0][1]["reason"], "time")
        self.assertTrue(shop2.done)


class TestDishBurnTV4(unittest.TestCase):
    def test_dish_burnt_when_ready_ticks_exceeds_timeout(self):
        """Kiểm tra mở rộng cháy món: ready_ticks <= 1200 bưng được; > 1200 cháy, bếp rảnh, re-order."""
        contract = load_contract()
        tuning = contract["tuning"]
        # Bật burn_s = 20s (1200 tick)
        tuning["quan"]["burn_s"] = 20

        # Scenario có bếp B1 đã chín món với ready_ticks = 1200
        scenario = {
            "stoves": [
                {
                    "id": "B1", "pos": [2, 8], "state": "ready", "dish": "ca_loc_nuong_trui",
                    "order_id": "C1", "ready_ticks": 1200
                }
            ],
            "customers": [
                {
                    "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                    "order_status": "assigned", "state": "waiting", "patience_ticks_left": 3000
                }
            ],
            "stock": {"ca_loc": 1}  # Còn 1 cá lóc trong kho để re-order
        }

        streams = Streams(42)
        ids = IdAllocator()
        sim = QuanSim(tuning, scenario, streams, ids)

        # Bước 1: ready_ticks ở đầu bước là 1200 -> tăng thành 1201 ở bước 1 -> vượt quá 1200 -> cháy!
        ev = sim.step(DummyInput())
        burnt_ev = [e for e in ev if e[0] == "dish_burnt"]
        self.assertEqual(len(burnt_ev), 1)
        self.assertEqual(burnt_ev[0][1]["stove_id"], "B1")
        self.assertEqual(burnt_ev[0][1]["dish_id"], "ca_loc_nuong_trui")
        # Do kho còn 1 cá lóc, đơn được giữ lại tự động (reserved)
        self.assertEqual(burnt_ev[0][1]["order_status"], "reserved")

        # Bếp trở về idle
        self.assertEqual(sim.stoves[0]["state"], "idle")
        self.assertIsNone(sim.stoves[0]["dish"])


if __name__ == "__main__":
    unittest.main()

