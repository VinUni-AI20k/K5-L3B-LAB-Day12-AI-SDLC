"""Tests Phase 3 cho Lát 2 (TV2): Độ tươi trong GatherSim, ngưỡng ươn 30, cấp ID, LIFO và validate scenario."""

import copy
import math
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.scenario import _validate_gather
from chonoi.sim.gather import GatherSim


def make_v12_tuning():
    t = copy.deepcopy(load_contract()["tuning"])
    t["freshness"] = {
        "initial": 100,
        "gather_decay_per_s": 0.5,
        "quan_decay_per_s": 0.25,
        "spoiled_below": 30,
    }
    return t


def inp(move=(0.0, 0.0), interact=False, catch=False):
    edges = set()
    if interact:
        edges.add("interact")
    if catch:
        edges.add("catch")
    return InputState(move, {"interact": interact, "catch": catch}, edges)


class GatherFreshnessPhase3Tests(unittest.TestCase):
    def test_spoiled_at_threshold_30_once_and_id_order(self):
        """Scenario chuẩn PRD: fresh=30 ươn ngay tick 1, phát spoiled đúng 1 lần theo thứ tự ID."""
        t = make_v12_tuning()
        sc = {
            "hold": [
                {"id": "I10", "kind": "ca_loc", "fresh": 30},
                {"id": "I2", "kind": "ca_linh", "fresh": 30},
            ],
            "random_fish": False,
            "monsters": [],
        }
        sim = GatherSim(t, sc, Streams(1), IdAllocator())
        evs1 = sim.step(inp())
        self.assertEqual(evs1, [
            ("spoiled", {"item_id": "I2", "kind": "ca_linh", "location": "hold"}),
            ("spoiled", {"item_id": "I10", "kind": "ca_loc", "location": "hold"}),
        ])
        self.assertLess(sim.hold[0]["fresh"], 30.0)
        # Tick 2 không phát spoiled lần nữa
        evs2 = sim.step(inp())
        self.assertEqual([e for e in evs2 if e[0] == "spoiled"], [])

    def test_new_items_fresh_100_no_decay_same_tick_and_id_continues(self):
        """Hái/bắt cấp ID tiếp sau max trong hold, fresh=100 không hao trong bước nhận."""
        t = make_v12_tuning()
        sc = {
            "player": {"pos": [12.0, 0.0]},
            "hold": [{"id": "I5", "kind": "ca_loc", "fresh": 90}],
            "random_fish": False,
            "monsters": [],
        }
        sim = GatherSim(t, sc, Streams(1), IdAllocator())
        sim.step(inp(interact=True))
        self.assertEqual(len(sim.hold), 2)
        self.assertEqual(sim.hold[0]["id"], "I5")
        self.assertAlmostEqual(sim.hold[0]["fresh"], 90.0 - 0.5 / 60.0, places=6)
        self.assertEqual(sim.hold[1], {"id": "I6", "kind": "bong_dien_dien", "fresh": 100.0})

        # Bước sau I6 mới bắt đầu hao
        sim.step(inp())
        self.assertAlmostEqual(sim.hold[1]["fresh"], 100.0 - 0.5 / 60.0, places=6)

    def test_catch_creates_individual_items_and_lifo_on_hit_and_faint(self):
        """Bắt cá tạo đúng yield cá thể; monster_hit và faint trả lost dạng cá thể LIFO."""
        t = make_v12_tuning()
        sc = {
            "player": {"pos": [15.0, 10.0], "hp": 2},
            "hold": [{"id": "I1", "kind": "bong_sung", "fresh": 80}],
            "random_fish": False,
            "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15.0, 10.0], "heading_deg": 0}],
            "monsters": [],
        }
        sim = GatherSim(t, sc, Streams(1), IdAllocator())
        evs = sim.step(inp(catch=True))
        self.assertIn(("fish_caught", {"fish_id": "F1", "kind": "ca_linh", "yield": 3}), evs)
        self.assertEqual([x["id"] for x in sim.hold], ["I1", "I2", "I3", "I4"])

        # Đặt quái ngay tại vị trí người chơi để kiểm tra monster_hit LIFO (floor(4/2) = 2: I4, I3)
        sim.monsters = [{
            "id": "M1", "kind": "ca_sau", "pos": list(sim.pos),
            "waypoints": [list(sim.pos), [sim.pos[0] + 4, sim.pos[1]]],
            "target_idx": 1, "state": "patrol", "state_ticks_left": 0, "recoil_dir": None,
        }]
        evs_hit = sim.step(inp())
        hit = [d for n, d in evs_hit if n == "monster_hit"][0]
        self.assertEqual([x["id"] for x in hit["lost"]], ["I4", "I3"])

        # Ngất do choke -> bỏ phần còn lại LIFO (I2, I1) và kho rỗng
        sim.oxygen_ticks = 0
        sim.zero_oxy_ticks = t["gather"]["choke_interval_ticks"] - 1
        evs_faint = sim.step(inp())
        faint = [d for n, d in evs_faint if n == "faint"][0]
        self.assertEqual([x["id"] for x in faint["lost"]], ["I2", "I1"])
        end_ev = [d for n, d in evs_faint if n == "gather_end"][0]
        self.assertEqual(end_ev["reason"], "fainted")
        self.assertEqual(end_ev["inventory"], {"items": []})

    def test_dock_exports_sorted_by_id_after_decay(self):
        """Cập bến xuất kho sắp theo id_key (I2 trước I10) và đã trừ hao bước đó."""
        t = make_v12_tuning()
        sc = {
            "hold": [
                {"id": "I10", "kind": "ca_loc", "fresh": 100},
                {"id": "I2", "kind": "bong_sung", "fresh": 100},
            ],
            "random_fish": False,
            "monsters": [],
        }
        sim = GatherSim(t, sc, Streams(1), IdAllocator())
        evs = sim.step(inp(interact=True))
        end_ev = [d for n, d in evs if n == "gather_end"][0]
        self.assertEqual(end_ev["reason"], "docked")
        items = end_ev["inventory"]["items"]
        self.assertEqual([x["id"] for x in items], ["I2", "I10"])
        self.assertAlmostEqual(items[0]["fresh"], 100.0 - 0.5 / 60.0, places=6)

    def test_validate_gather_rejects_invalid_v12_hold(self):
        """Validate scenario v1.2 từ chối hold dạng chuỗi, id trùng, kind lạ, fresh ngoài [0,100]."""
        t = make_v12_tuning()
        bad_holds = [
            ["ca_loc"],
            [{"id": "I1", "kind": "ca_loc", "fresh": 100}, {"id": "I1", "kind": "ca_loc", "fresh": 90}],
            [{"id": "I1", "kind": "unknown", "fresh": 100}],
            [{"id": "I1", "kind": "ca_loc", "fresh": -0.1}],
            [{"id": "I1", "kind": "ca_loc", "fresh": 100.1}],
            [{"id": "I1", "kind": "ca_loc", "fresh": math.nan}],
        ]
        for h in bad_holds:
            with self.assertRaises(BadInput):
                _validate_gather({"hold": h}, t)
