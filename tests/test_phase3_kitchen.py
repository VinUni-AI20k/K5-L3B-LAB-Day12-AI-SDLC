"""Kiểm tra phần Bếp (Người A — `chonoi/sim/kitchen.py`) theo chuẩn Phase 3 (Contract v1.2 — Độ tươi):
- Kho cá thể (`stock` là mảng `{id, kind, fresh}`), giữ theo danh sách `id`.
- Chốt `base_price = floor(giá niêm yết × trung bình fresh / 100)` khi `cook_started`.
- `cook_started.data.items` là mảng cá thể sắp theo `(kind, id_key)`.
- Cháy món `burn_s` trên kho cá thể: bỏ qua hàng ươn (`fresh < 30`), chọn cá thể tươi nhất hòa theo `id`.
- Đơn đặt trước (`reservation_id`): nhân `1.5` làm tròn xuống và chuyển `failed` khi cháy món.
"""

import unittest

from chonoi.sim.kitchen import interact_stove, step_stoves


class _DummySim:
    def __init__(self, stock, customers, stoves=None, burn_s=None):
        self.t = {"burn_s": burn_s}
        self.menu = {
            "ca_loc_nuong_trui": {"recipe": {"ca_loc": 1}, "cook_s": 6, "price": 60},
            "lau_mam": {
                "recipe": {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1},
                "cook_s": 12,
                "price": 200,
            },
        }
        self.stock = stock
        self.customers = customers
        self.stoves = stoves or [{"id": "B1", "state": "idle", "dish": None, "cook_ticks_left": 0, "ready_ticks": 0}]
        self.hand = None
        self.freshness = {"spoiled_below": 30}


class Phase3KitchenTest(unittest.TestCase):
    def test_cook_started_v12_freshness_price_and_item_sorting(self):
        stock = [
            {"id": "I10", "kind": "ca_linh", "fresh": 80},
            {"id": "I2", "kind": "ca_linh", "fresh": 100},
            {"id": "I3", "kind": "ca_keo", "fresh": 90},
            {"id": "I4", "kind": "keo_neo", "fresh": 70},
            {"id": "I5", "kind": "bong_dien_dien", "fresh": 60},
            {"id": "I99", "kind": "ca_loc", "fresh": 100},
        ]
        customers = [{
            "id": "C1",
            "table_id": "T1",
            "dish_id": "lau_mam",
            "order_tick": 0,
            "state": "waiting",
            "order_status": "reserved",
            "reserved": ["I10", "I2", "I3", "I4", "I5"],
        }]
        sim = _DummySim(stock, customers)
        events = []
        interact_stove(sim, sim.stoves[0], events)

        self.assertEqual(len(events), 1)
        name, data = events[0]
        self.assertEqual(name, "cook_started")
        self.assertEqual(data["base_price"], 160)
        self.assertEqual(
            [it["id"] for it in data["items"]],
            ["I5", "I3", "I2", "I10", "I4"],
        )
        self.assertEqual([it["id"] for it in sim.stock], ["I99"])
        self.assertEqual(sim.customers[0]["reserved"], [])
        self.assertEqual(sim.customers[0]["order_status"], "assigned")

    def test_cook_started_v12_floors_fractional_price(self):
        stock = [{"id": "I1", "kind": "ca_loc", "fresh": 97.5}]
        customers = [{
            "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
            "order_tick": 0, "state": "waiting", "order_status": "reserved", "reserved": ["I1"],
        }]
        sim = _DummySim(stock, customers)
        events = []
        interact_stove(sim, sim.stoves[0], events)
        self.assertEqual(events[0][1]["base_price"], 58)

    def test_burn_v12_rereserves_freshest_non_spoiled_tiebreak_id(self):
        stock = [
            {"id": "I1", "kind": "ca_loc", "fresh": 29.9},
            {"id": "I10", "kind": "ca_loc", "fresh": 85},
            {"id": "I2", "kind": "ca_loc", "fresh": 85},
        ]
        stoves = [{
            "id": "B1", "state": "ready", "ready_ticks": 1200, "cook_ticks_left": 0,
            "dish": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
        }]
        customers = [{
            "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
            "order_tick": 0, "state": "waiting", "order_status": "assigned", "reserved": [],
        }]
        sim = _DummySim(stock, customers, stoves=stoves, burn_s=20)
        events = []
        step_stoves(sim, events)

        self.assertEqual(events, [(
            "dish_burnt",
            {"stove_id": "B1", "order_id": "C1", "dish_id": "ca_loc_nuong_trui", "order_status": "reserved"},
        )])
        self.assertEqual(sim.customers[0]["reserved"], ["I2"])

    def test_reservation_freshness_price_multiplier_and_burn_failed(self):
        stock = [{"id": "I1", "kind": "ca_loc", "fresh": 80}]
        customers = [{
            "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
            "order_tick": 0, "state": "waiting", "order_status": "reserved",
            "reserved": ["I1"], "reservation_id": "R1",
        }]
        sim = _DummySim(stock, customers)
        events = []
        interact_stove(sim, sim.stoves[0], events)
        # floor(60 * 0.8) = 48 -> floor(48 * 1.5) = 72
        self.assertEqual(events[0][1]["base_price"], 72)

        sim_burn = _DummySim(
            [{"id": "I2", "kind": "ca_loc", "fresh": 100}],
            [{
                "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                "order_tick": 0, "state": "waiting", "order_status": "assigned",
                "reserved": [], "reservation_id": "R1",
            }],
            stoves=[{
                "id": "B1", "state": "ready", "ready_ticks": 1200, "cook_ticks_left": 0,
                "dish": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 72},
            }],
            burn_s=20,
        )
        evs_b = []
        step_stoves(sim_burn, evs_b)
        self.assertEqual(evs_b, [(
            "dish_burnt",
            {"stove_id": "B1", "order_id": "C1", "dish_id": "ca_loc_nuong_trui", "order_status": "failed"},
        )])
        self.assertEqual(sim_burn.customers[0]["order_status"], "failed")


if __name__ == "__main__":
    unittest.main()

