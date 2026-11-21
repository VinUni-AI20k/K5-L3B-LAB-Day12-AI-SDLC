"""P3-06 (AC-P3-05): HUD độ tươi, hàng ươn, đơn bị ảnh hưởng. Dữ liệu cá thể dựng bằng adapter của P3-02."""

import json
import os
import unittest

from chonoi import freshness_view
from chonoi.contract import load_contract
from chonoi.freshness import Freshness
from chonoi.ids import IdAllocator
from chonoi.inputs import InputPlayer
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim
from chonoi.inventory import counts_to_individuals, hold_to_individuals
from chonoi.live import LiveGame
from chonoi.runner import Session
from helpers import ROOT

TUNING = load_contract()["tuning"]
F = TUNING["freshness"]
SPOIL = F["spoil_below"]
UNIT = 1 / F["units_per_point"]  # một đơn vị nhỏ nhất, tính bằng điểm


def with_fresh(items, *fresh):
    out = [dict(it) for it in items]
    for it, f in zip(out, fresh):
        it["fresh"] = f
    return out


class Gather(unittest.TestCase):
    def snap(self, *fresh):
        hold = with_fresh(hold_to_individuals(["ca_loc", "bong_sung", "ca_linh"]), *fresh)
        return {"phase": "gather", "mode": "gather", "hold": hold}

    def test_items_and_spoiled_boundary(self):
        v = freshness_view.view(self.snap(SPOIL, SPOIL - UNIT, F["fresh_max"]), TUNING)
        self.assertEqual([(i["id"], i["kind"], i["spoiled"]) for i in v["items"]],
                         [("I1", "ca_loc", False), ("I2", "bong_sung", True), ("I3", "ca_linh", False)])
        self.assertEqual((v["spoiled_count"], v["min_fresh"]), (1, SPOIL - UNIT))
        self.assertEqual((v["fresh_max"], v["spoil_below"]), (F["fresh_max"], SPOIL))
        self.assertEqual(v["affected_orders"], [])

    def test_matches_freshness_module(self):
        fr = Freshness(TUNING)
        for units in (fr.spoil_units, fr.spoil_units - 1, 0, fr.max_units):
            v = freshness_view.view(self.snap(fr.to_points(units)), TUNING)
            self.assertEqual(v["items"][0]["spoiled"], fr.is_spoiled(units), units)


class RealGatherV12(unittest.TestCase):
    """Sim gather v1.2 thật (P3-03 của A, PR #45): HUD đánh dấu ươn đúng tick sim phát `spoiled`."""

    def test_spoiled_flag_matches_sim_event_tick(self):
        fr = Freshness(TUNING)
        start = fr.to_points(fr.spoil_units + 2 * fr.decay("gather"))  # còn 2 tick nữa là ươn
        hold = [{"id": "I1", "kind": "ca_loc", "fresh": start}, {"id": "I2", "kind": "ca_linh", "fresh": 100}]
        sim = GatherSim(TUNING, {"random_fish": False, "monsters": [], "player": {"pos": [20, 5]}, "hold": hold},
                        Streams(1), IdAllocator(), contract_version="1.2")
        inp = InputPlayer([])
        seen = []
        for tick in range(1, 5):
            events = sim.step(inp.advance(tick - 1))
            v = freshness_view.view({"phase": "gather", **sim.snapshot()}, TUNING)
            seen.append((tick, any(n == "spoiled" for n, _ in events), v["items"][0]["spoiled"], v["spoiled_count"]))
        first_event = next(t for t, ev, _, _ in seen if ev)
        first_flag = next(t for t, _, flag, _ in seen if flag)
        self.assertEqual(first_flag, first_event)
        self.assertEqual(seen[-1][3], 1)


class Quan(unittest.TestCase):
    def snap(self, customers, *fresh):
        stock = with_fresh(counts_to_individuals({"ca_loc": 2, "bong_sung": 1}), *fresh)
        return {"phase": "quan", "mode": "quan", "stock": stock, "customers": customers}

    def test_affected_orders(self):
        customers = [
            {"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "state": "waiting", "order_status": "reserved",
             "reserved": ["I3"]},                                                     # giữ hàng đã ươn (theo id)
            {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "state": "waiting",
             "order_status": "reserved", "reserved": [{"id": "I1", "kind": "ca_loc", "fresh": 80}]},   # còn tươi
            {"id": "C3", "table_id": "T3", "dish_id": "ca_loc_nuong_trui", "state": "waiting",
             "order_status": "unfulfillable", "reserved": []},                        # không làm được
            {"id": "C4", "table_id": "T4", "dish_id": "goi_bong_sung", "state": "eating", "order_status": "served",
             "reserved": ["I3"]},                                                     # đang ăn: không tính
        ]
        v = freshness_view.view(self.snap(customers, 90, 80, SPOIL - UNIT), TUNING)
        self.assertEqual([(o["customer_id"], o["reason"], o["item_ids"]) for o in v["affected_orders"]],
                         [("C1", "spoiled_reserved", ["I3"]), ("C3", "unfulfillable", [])])
        self.assertEqual(v["spoiled_count"], 1)

    def test_reserved_item_spoiled_inline(self):
        c = [{"id": "C1", "table_id": "T1", "dish_id": "x", "state": "waiting", "order_status": "reserved",
              "reserved": [{"id": "I9", "kind": "ca_loc", "fresh": SPOIL - UNIT}]}]
        v = freshness_view.view(self.snap(c, 90, 90, 90), TUNING)
        self.assertEqual(v["affected_orders"][0]["item_ids"], ["I9"])

    def test_shop_shows_stock_without_orders(self):
        left = [{"id": "C1", "table_id": "T1", "dish_id": "x", "state": "waiting", "order_status": "unfulfillable",
                 "reserved": ["I2"]}]  # Shop không có đơn: dù dữ liệu có khách cũng không tính
        snap = {**self.snap(left, 90, 20, 90), "phase": "shop", "mode": "day"}
        v = freshness_view.view(snap, TUNING)
        self.assertEqual((len(v["items"]), v["spoiled_count"], v["affected_orders"]), (3, 1, []))


class Compatibility(unittest.TestCase):
    def test_v11_snapshots_have_no_freshness_view(self):
        for mode in ("gather", "quan"):
            self.assertIsNone(freshness_view.view(Session(mode, TUNING, {}, 1).snapshot(), TUNING), mode)

    def test_no_freshness_block_in_contract(self):
        t = {k: v for k, v in TUNING.items() if k != "freshness"}
        snap = {"phase": "gather", "hold": hold_to_individuals(["ca_loc"])}
        self.assertIsNone(freshness_view.view(snap, t))

    def test_live_state_carries_view_only_with_individuals(self):
        game = LiveGame("gather", TUNING, {}, 1)
        self.assertNotIn("freshness_hud", json.loads(game.state_json()))
        real = game.session.snapshot
        game.session.snapshot = lambda: {**real(), "hold": with_fresh(hold_to_individuals(["ca_loc"]), SPOIL - UNIT)}
        st = json.loads(game.state_json())
        self.assertEqual(st["freshness_hud"]["spoiled_count"], 1)

    def test_page_reads_both_shapes(self):
        with open(os.path.join(ROOT, "chonoi", "web", "index.html"), encoding="utf-8") as f:
            html = f.read()
        for marker in ("kindOf", "stockText", "Array.isArray(stock)", "freshness_hud", "affected_orders", "✕", "ƯƠN"):
            self.assertIn(marker, html)


if __name__ == "__main__":
    unittest.main()
