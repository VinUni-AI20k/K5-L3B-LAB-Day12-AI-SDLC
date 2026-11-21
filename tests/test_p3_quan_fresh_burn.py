"""Phase 3 (HoangQuan23112004): Quán v1.2 (hao tươi 0.25/s, spoiled, giữ lại, giá theo tươi,
cook_started.items) và mở rộng Cháy món (`burn`, burn_s=20).

Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_p3_quan_fresh_burn -v
"""

import copy
import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def run_quan(w, block, ticks, inputs=None):
    b = dict(block)
    b.setdefault("random_customers", False)
    sc = write_json(w.path("sc.json"), {"quan": b})
    args = ["--mode", "quan", "--seed", "1", "--ticks", str(ticks), "--scenario", sc,
            "--snapshot-every", "1", "--out", w.path("o.jsonl")]
    if inputs is not None:
        args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
    code, err = run_headless(*args)
    assert code == 0, err
    return read_jsonl(w.path("o.jsonl"))


def snap_at(rows, tick):
    return next(s for s in snapshots(rows) if s["tick"] == tick)


class QuanFreshnessAndPricing(unittest.TestCase):
    def test_spoiled_at_threshold_30_rereserves_freshest_or_becomes_unfulfillable(self):
        """Cá thể fresh=30 ươn ở tick 1 -> phát spoiled(stock) theo id; đơn nhả & giữ lại 1 lần (tươi nhất, hòa id) hoặc unfulfillable."""
        with Workdir() as w:
            block = {
                "stock": [
                    {"id": "I1", "kind": "ca_loc", "fresh": 30},    # C1 đang giữ -> ươn ở tick 1
                    {"id": "I2", "kind": "ca_loc", "fresh": 80},    # thay thế tươi nhất cho C1
                    {"id": "I3", "kind": "ca_loc", "fresh": 60},    # thay thế kém tươi hơn
                    {"id": "I10", "kind": "bong_sung", "fresh": 30},  # C2 đang giữ -> ươn ở tick 1
                    {"id": "I4", "kind": "bong_sung", "fresh": 90},   # C2 chỉ còn 1 bông súng (cần 2) -> unfulfillable
                ],
                "customers": [
                    {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_tick": 10, "reserved": ["I1"]},
                    {"id": "C2", "table_id": "T2", "dish_id": "goi_bong_sung", "order_tick": 20, "reserved": ["I10", "I4"]},
                ],
            }
            rows = run_quan(w, block, 1)
            sp = events(rows, "spoiled")
            # Phát theo id: I1 trước I10
            self.assertEqual([(e["tick"], e["data"]) for e in sp], [
                (1, {"item_id": "I1", "kind": "ca_loc", "location": "stock"}),
                (1, {"item_id": "I10", "kind": "bong_sung", "location": "stock"}),
            ])
            s1 = snap_at(rows, 1)
            by_id = {c["id"]: c for c in s1["customers"]}
            self.assertEqual(by_id["C1"]["order_status"], "reserved")
            self.assertEqual(by_id["C1"]["reserved"], ["I2"])
            self.assertEqual(by_id["C2"]["order_status"], "unfulfillable")
            self.assertEqual(by_id["C2"]["reserved"], [])

    def test_cook_price_uses_average_freshness_and_tip_uses_locked_base_price(self):
        """base_price = floor(giá × fresh TB / 100); boa = floor(base_price × 0.2); cook_started.items sắp (kind, id)."""
        with Workdir() as w:
            # goi_bong_sung (giá 40) dùng I10 (fresh 80) và I2 (fresh 40) -> TB ban đầu 60, sau 1 tick hao (1/240):
            # TB = 60 - 1/240 -> 40 * (60 - 1/240) / 100 = 23.9983... -> floor = 23; tip = floor(23 * 0.2) = 4
            block = {
                "player": {"pos": [2, 8]},
                "stock": [
                    {"id": "I10", "kind": "bong_sung", "fresh": 80},
                    {"id": "I2", "kind": "bong_sung", "fresh": 40},
                ],
                "customers": [
                    {"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "reserved": ["I10", "I2"]},
                ],
            }
            rows = run_quan(w, block, 1, [{"tick": 0, "interact": True}])
            cs = events(rows, "cook_started")[0]["data"]
            self.assertEqual(cs["base_price"], 23)
            # Sắp theo kind rồi id: I2 đứng trước I10
            self.assertEqual([it["id"] for it in cs["items"]], ["I2", "I10"])


class BurnExtension(unittest.TestCase):
    def _make_sim_with_burn(self, scenario):
        tuning = copy.deepcopy(load_contract()["tuning"])
        tuning["quan"]["burn_s"] = 20  # 1200 ticks
        return QuanSim(tuning, {"random_customers": False, **scenario}, Streams(1), IdAllocator())

    def test_exact_1200_ready_ticks_still_pickable(self):
        """Đúng 1.200 tick vẫn bưng được (không cháy)."""
        dish = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}
        sim = self._make_sim_with_burn({
            "player": {"pos": [2, 8]},
            "stoves": [{"id": "B1", "state": "ready", "dish": dish, "ready_ticks": 1199}],
            "customers": [{
                "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                "state": "waiting", "order_status": "assigned", "reserved": [], "base_price": 60,
            }],
        })
        # Bước này ready_ticks tăng 1199 -> 1200 (không > 1200), rồi interact bưng được
        ev = sim.step(InputState((0.0, 0.0), {"interact": True}, {"interact"}))
        self.assertEqual([e[0] for e in ev], ["dish_picked"])
        self.assertEqual(sim.hand, dish)
        self.assertEqual(sim.stoves[0]["state"], "idle")

    def test_burn_at_1201_rereserves_when_stock_available(self):
        """ready_ticks > 1200 -> cháy, bếp idle, nguyên liệu đã dùng mất, giữ lại được -> order_status=reserved."""
        dish = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}
        sim = self._make_sim_with_burn({
            "stock": [
                {"id": "I1", "kind": "ca_loc", "fresh": 50},
                {"id": "I2", "kind": "ca_loc", "fresh": 90},
            ],
            "stoves": [{"id": "B1", "state": "ready", "dish": dish, "ready_ticks": 1200}],
            "customers": [{
                "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                "state": "waiting", "order_status": "assigned", "reserved": [], "base_price": 60,
            }],
        })
        ev = sim.step(InputState((0.0, 0.0), {}, set()))
        self.assertEqual(ev, [("dish_burnt", {
            "stove_id": "B1", "order_id": "C1", "dish_id": "ca_loc_nuong_trui", "order_status": "reserved",
        })])
        self.assertEqual(sim.stoves[0]["state"], "idle")
        self.assertIsNone(sim.stoves[0]["dish"])
        self.assertEqual(sim.customers[0]["order_status"], "reserved")
        self.assertEqual(sim.customers[0]["reserved"], ["I2"])  # chọn cá thể tươi nhất
        self.assertIsNone(sim.customers[0]["base_price"])

    def test_burn_at_1201_becomes_unfulfillable_when_no_fresh_stock(self):
        """Cháy khi không còn nguyên liệu chưa ươn -> dish_burnt(order_status=unfulfillable), khách tiếp tục chờ."""
        dish = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}
        sim = self._make_sim_with_burn({
            "stock": [{"id": "I1", "kind": "ca_loc", "fresh": 20}],  # đã ươn
            "stoves": [{"id": "B1", "state": "ready", "dish": dish, "ready_ticks": 1200}],
            "customers": [{
                "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                "state": "waiting", "order_status": "assigned", "reserved": [], "base_price": 60,
            }],
        })
        ev = sim.step(InputState((0.0, 0.0), {}, set()))
        self.assertEqual(ev, [("dish_burnt", {
            "stove_id": "B1", "order_id": "C1", "dish_id": "ca_loc_nuong_trui", "order_status": "unfulfillable",
        })])
        self.assertEqual(sim.customers[0]["order_status"], "unfulfillable")
        self.assertEqual(sim.customers[0]["reserved"], [])
        self.assertEqual(sim.customers[0]["state"], "waiting")


class BurnExtensionHeadless(unittest.TestCase):
    """Kiểm hộp đen qua headless_cmd với burn_s=20 đã bật trong game.contract.json (AC-P4-06)."""

    def test_headless_burn_boundary_1200_vs_1201(self):
        dish = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}
        # Đúng 1200 tick -> vẫn bưng được qua headless
        with Workdir() as w:
            block = {
                "player": {"pos": [2, 8]},
                "stoves": [{"id": "B1", "state": "ready", "dish": dish, "ready_ticks": 1199}],
                "customers": [{
                    "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                    "state": "waiting", "order_status": "assigned", "reserved": [], "base_price": 60,
                }],
            }
            rows = run_quan(w, block, 1, [{"tick": 0, "interact": True}])
            self.assertEqual([e["name"] for e in events(rows)], ["dish_picked"])

        # 1201 tick -> dish_burnt(reserved) khi còn hàng tươi, dish_burnt(unfulfillable) khi hết hàng
        with Workdir() as w:
            block = {
                "stock": [{"id": "I1", "kind": "ca_loc", "fresh": 85}],
                "stoves": [{"id": "B1", "state": "ready", "dish": dish, "ready_ticks": 1200}],
                "customers": [{
                    "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                    "state": "waiting", "order_status": "assigned", "reserved": [], "base_price": 60,
                }],
            }
            rows = run_quan(w, block, 1)
            burnt = events(rows, "dish_burnt")
            self.assertEqual(len(burnt), 1)
            self.assertEqual(burnt[0]["data"], {
                "stove_id": "B1", "order_id": "C1", "dish_id": "ca_loc_nuong_trui", "order_status": "reserved",
            })
            s1 = snap_at(rows, 1)
            self.assertEqual(s1["stoves"][0]["state"], "idle")
            self.assertEqual(s1["customers"][0]["reserved"], ["I1"])

        with Workdir() as w:
            block = {
                "stock": [],
                "stoves": [{"id": "B1", "state": "ready", "dish": dish, "ready_ticks": 1200}],
                "customers": [{
                    "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                    "state": "waiting", "order_status": "assigned", "reserved": [], "base_price": 60,
                }],
            }
            rows = run_quan(w, block, 1)
            burnt = events(rows, "dish_burnt")
            self.assertEqual(burnt[0]["data"]["order_status"], "unfulfillable")


if __name__ == "__main__":
    unittest.main()
