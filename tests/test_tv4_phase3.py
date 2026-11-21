"""Unit test suite cho Phase 3 (TV4 - Nguyễn Anh Quân - AnhQuanHANU).
Kiểm chứng:
1. Chốt giá món theo độ tươi trung bình (floor(giá * avg_fresh / 100)).
2. Thứ tự items trong cook_started sắp xếp theo kind rồi id.
3. Tính tiền boa dựa trên giá đã chốt theo fresh.
4. Ngưỡng ươn 30 và quy tắc chỉ phát spoiled khi đi từ >= 30 xuống < 30.
5. Hòa id khi nhiều cá thể cùng ươn.
6. Mở rộng Cháy món (burn) re-reserve cá thể tươi nhất và bỏ qua hàng ươn.
7. Thanh toán đóng ca với giá đã chốt.
"""

from fractions import Fraction
import json
import math
import os
from pathlib import Path
from types import SimpleNamespace
import unittest

from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim
from chonoi.sim.shop import ShopSim

try:
    from helpers import ROOT
except ImportError:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def make_inp(move=(0, 0), interact=False):
    return SimpleNamespace(move=move, pressed=lambda name: (name == "interact" if interact else False))


class TestTV4Phase3(unittest.TestCase):
    def setUp(self):
        self.contract_path = Path(ROOT) / "game.contract.json"
        self.tuning = json.loads(self.contract_path.read_text(encoding="utf-8"))["tuning"]

    def create_sim(self, stock, customers=None, player_pos=(2.0, 8.0), scenario_extra=None):
        sc = {
            "player": {"pos": list(player_pos)},
            "customers": customers or [],
            "random_customers": False
        }
        if scenario_extra:
            sc.update(scenario_extra)
        return QuanSim(self.tuning, sc, Streams(42), IdAllocator(), inventory=stock)

    def test_cook_multi_item_recipe_price_calculation_and_item_order(self):
        """Kiểm tra nấu món nhiều nguyên liệu: chốt base_price = floor(giá * avg_fresh / 100), items xếp theo kind rồi id."""
        # Món: lau_ca_linh_dien_dien (3 ca_linh + 1 bong_dien_dien), giá niêm yết: 120
        # Độ tươi các cá thể:
        # bong_dien_dien: 90.0
        # ca_linh: 80.0, 70.0, 60.0
        # Trung bình: (90 + 80 + 70 + 60) / 4 = 75.0
        # base_price = floor(120 * 75.0 / 100) = 90
        stock = [
            {"id": "I1", "kind": "ca_linh", "fresh": 80.0},
            {"id": "I2", "kind": "ca_linh", "fresh": 70.0},
            {"id": "I3", "kind": "ca_linh", "fresh": 60.0},
            {"id": "I4", "kind": "bong_dien_dien", "fresh": 90.0},
        ]
        customers = [
            {
                "id": "C1",
                "table_id": "T1",
                "dish_id": "lau_ca_linh_dien_dien",
                "order_tick": 0,
                "reserved": ["I1", "I2", "I3", "I4"]
            }
        ]
        sim = self.create_sim(stock, customers, player_pos=(2.0, 8.0))

        # Người chơi tương tác với bếp B1 [2.0, 8.0]
        events = sim.step(make_inp(interact=True))
        cook_events = [ev for ev in events if ev[0] == "cook_started"]
        self.assertEqual(len(cook_events), 1)

        name, data = cook_events[0]
        self.assertEqual(data["order_id"], "C1")
        self.assertEqual(data["dish_id"], "lau_ca_linh_dien_dien")
        # Theo thứ tự trong tick của Quán: hao tươi (giảm 0.25/60 = 1/240 mỗi tick) xảy ra TRƯỚC tương tác nấu.
        # Do đó tại thời điểm nấu, trung bình fresh là 75 - 1/240 = 74.995833...
        # base_price = floor(120 * 74.995833 / 100) = floor(89.995) = 89
        self.assertEqual(data["base_price"], 89)

        # Kiểm tra items được sắp xếp theo kind rồi id:
        # 'bong_dien_dien' < 'ca_linh', nên I4 (bong_dien_dien) phải đứng đầu, sau đó đến I1, I2, I3 (ca_linh)
        item_kinds = [it["kind"] for it in data["items"]]
        item_ids = [it["id"] for it in data["items"]]
        self.assertEqual(item_kinds, ["bong_dien_dien", "ca_linh", "ca_linh", "ca_linh"])
        self.assertEqual(item_ids, ["I4", "I1", "I2", "I3"])

        # Bếp B1 đang cooking với base_price đã chốt
        stove_b1 = next(s for s in sim.stoves if s["id"] == "B1")
        self.assertEqual(stove_b1["state"], "cooking")
        self.assertEqual(stove_b1["base_price"], 89)

    def test_serve_tip_and_payment_based_on_locked_fresh_price(self):
        """Kiểm tra tiền boa và thanh toán dựa trên giá đã chốt theo fresh (không dùng giá niêm yết gốc)."""
        # Giả sử món cá lóc nướng trui (giá gốc 60) nhưng fresh thấp nên base_price đã chốt là 40.
        # Khi giao món tại bàn T1 lúc kiên nhẫn >= 50%: tip = floor(40 * 0.2) = 8.
        # Khi thanh toán: amount = 40 + 8 = 48.
        sim = self.create_sim(
            stock=[],
            customers=[
                {
                    "id": "C1",
                    "table_id": "T1",
                    "dish_id": "ca_loc_nuong_trui",
                    "patience_ticks_left": 3000,
                    "base_price": 40,
                    "order_status": "assigned"
                }
            ],
            player_pos=(9.0, 2.0),
            scenario_extra={
                "hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 40}
            }
        )

        # Giao món tại bàn T1
        events = sim.step(make_inp(interact=True))
        served_ev = [ev for ev in events if ev[0] == "served"]
        self.assertEqual(len(served_ev), 1)
        self.assertEqual(served_ev[0][1]["base_price"], 40)
        self.assertEqual(served_ev[0][1]["tip"], 8)

        # Tua 600 ticks ăn
        for _ in range(600):
            events = sim.step(make_inp(interact=False))

        paid_ev = [ev for ev in events if ev[0] == "paid"]
        self.assertEqual(len(paid_ev), 1)
        self.assertEqual(paid_ev[0][1]["base_price"], 40)
        self.assertEqual(paid_ev[0][1]["tip"], 8)
        self.assertEqual(paid_ev[0][1]["amount"], 48)
        self.assertEqual(sim.money, 48)
        self.assertEqual(sim.reputation, 3.2)

    def test_freshness_spoiled_only_transitions_from_ge_30_to_lt_30(self):
        """Hàng đúng 30 hao thành < 30 thì phát spoiled; hàng vốn đã < 30 không phát lại."""
        stock = [
            {"id": "I1", "kind": "ca_loc", "fresh": 30.0},
            {"id": "I2", "kind": "ca_loc", "fresh": 25.0},  # Đã ươn sẵn từ trước
            {"id": "I3", "kind": "ca_loc", "fresh": 80.0},  # Còn rất tươi
        ]
        sim = self.create_sim(stock, customers=[])

        # Step 1 tick: hao tươi kho
        events = sim.step(make_inp(interact=False))
        spoiled_ev = [ev for ev in events if ev[0] == "spoiled"]

        # Chỉ có I1 phát spoiled vì chuyển từ 30.0 xuống < 30.0
        self.assertEqual(len(spoiled_ev), 1)
        self.assertEqual(spoiled_ev[0][1]["item_id"], "I1")
        self.assertEqual(spoiled_ev[0][1]["location"], "stock")

    def test_spoiled_tiebreak_emits_by_id_order(self):
        """Khi nhiều cá thể cùng chạm ngưỡng ươn trong cùng tick, phát theo thứ tự id."""
        stock = [
            {"id": "I10", "kind": "ca_linh", "fresh": 30.0},
            {"id": "I2", "kind": "ca_linh", "fresh": 30.0},
            {"id": "I1", "kind": "ca_linh", "fresh": 30.0},
        ]
        sim = self.create_sim(stock, customers=[])
        events = sim.step(make_inp(interact=False))

        spoiled_ev = [ev for ev in events if ev[0] == "spoiled"]
        self.assertEqual(len(spoiled_ev), 3)
        # Theo thứ tự id: I1, I2, I10
        emitted_ids = [ev[1]["item_id"] for ev in spoiled_ev]
        self.assertEqual(emitted_ids, ["I1", "I2", "I10"])

    def test_burnt_dish_re_reserves_freshest_valid_stock(self):
        """Mở rộng Cháy món (burn): khi cháy, giải phóng bếp và re-reserve cá thể tươi nhất chưa ươn."""
        # Bếp B1 đang có món cá lóc nướng trui đã chín (ready)
        # Tồn kho: I1 (fresh 85), I2 (fresh 50), I3 (fresh 20 - ươn)
        stock = [
            {"id": "I1", "kind": "ca_loc", "fresh": 85.0},
            {"id": "I2", "kind": "ca_loc", "fresh": 50.0},
            {"id": "I3", "kind": "ca_loc", "fresh": 20.0},
        ]
        customers = [
            {
                "id": "C1",
                "table_id": "T1",
                "dish_id": "ca_loc_nuong_trui",
                "order_status": "assigned",
                "reserved": []
            }
        ]
        tuning_with_burn = dict(self.tuning)
        tuning_with_burn["quan"] = dict(tuning_with_burn["quan"], burn_s=20)

        sc = {
            "player": {"pos": [8.0, 5.0]},
            "customers": customers,
            "stoves": [
                {
                    "id": "B1",
                    "state": "ready",
                    "dish": "ca_loc_nuong_trui",
                    "order_id": "C1",
                    "base_price": 50,
                    "ready_ticks": 1200  # Ngưỡng bắt đầu cháy khi vượt 1200
                }
            ],
            "random_customers": False
        }
        sim = QuanSim(tuning_with_burn, sc, Streams(42), IdAllocator(), inventory=stock)

        # Tick tiếp theo: ready_ticks tăng lên 1201 > 1200 -> cháy
        events = sim.step(make_inp(interact=False))
        burnt_ev = [ev for ev in events if ev[0] == "dish_burnt"]
        self.assertEqual(len(burnt_ev), 1)
        self.assertEqual(burnt_ev[0][1]["order_status"], "reserved")

        # C1 được re-reserve cá thể tươi nhất là I1 (85 fresh)
        self.assertEqual(sim.customers[0]["order_status"], "reserved")
        self.assertEqual(sim.customers[0]["reserved"], ["I1"])

    def test_shop_snapshot_supports_list_stock_schema(self):
        """Kiểm tra ShopSim.snapshot hỗ trợ kho dạng danh sách cá thể."""
        stock = [
            {"id": "I1", "kind": "ca_loc", "fresh": 95.0},
            {"id": "I2", "kind": "ca_linh", "fresh": 88.5}
        ]
        shop = ShopSim(tuning=self.tuning, state={"stock": stock, "money": 300, "earned": 300})
        snap = shop.snapshot()
        self.assertIsInstance(snap["stock"], list)
        self.assertEqual(len(snap["stock"]), 2)
        self.assertEqual(snap["stock"][0]["id"], "I1")
        self.assertEqual(snap["stock"][0]["fresh"], 95.0)


if __name__ == "__main__":
    unittest.main()
