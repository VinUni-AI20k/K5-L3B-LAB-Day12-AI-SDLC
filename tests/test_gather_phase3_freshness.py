"""Unit & session tests cho Phase 3 Gather (TV2 — T310, T311, T312, TICKET-03 v1.2).

Kiểm độc lập trên `chonoi/sim/freshness.py` + `GatherSim` + `Session` với bản sao tuning có
`tuning.freshness` (không sửa `game.contract.json`, `inventory.py`, `scenario.py`, `runner.py`
khi TV1/TV6 chưa hoàn tất T301–T306), đồng thời bảo đảm không làm vỡ hành vi v1.0/v1.1.
"""

import copy
import json
import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import BUTTONS_V11, InputPlayer, STRINGS_V11
from chonoi.jsonl import dumps
from chonoi.rng import Streams
from chonoi.runner import Session
from chonoi.sim.freshness import UNITS_PER_FRESH, fresh_to_units, units_to_fresh
from chonoi.sim.gather import GatherSim

FRESHNESS_V12 = {
    "initial": 100,
    "gather_decay_per_s": 0.5,
    "quan_decay_per_s": 0.25,
    "spoiled_below": 30,
}


def make_v12_tuning():
    tuning = copy.deepcopy(load_contract()["tuning"])
    tuning["freshness"] = dict(FRESHNESS_V12)
    return tuning


def run_gather_session(tuning, scenario, frames, ticks, seed=1):
    """Chạy GatherSim qua Session (dùng chung lớp pause/tick/snapshot với headless)."""
    sess = Session("gather", tuning, scenario, seed)
    player = InputPlayer(frames, BUTTONS_V11, STRINGS_V11)
    rows = [sess.snapshot()]
    for frame in range(ticks):
        if sess.done:
            break
        ev_rows = sess.step(player.advance(frame))
        rows.extend(ev_rows)
        rows.append(sess.snapshot())
    rows.append(sess.end_row())
    return sess, rows


def evs(rows, name=None):
    return [r for r in rows if r["type"] == "event" and (name is None or r["name"] == name)]


class GatherFreshnessT310Tests(unittest.TestCase):
    """T310: cá thể `{id, kind, fresh}`, cấp `I<n>` tất định, hàng mới hao từ bước sau."""

    def test_harvest_and_catch_allocate_ids_and_decay_from_next_tick(self):
        tuning = make_v12_tuning()
        scenario = {
            "player": {"pos": [12, 0]},
            "hold": [],
            "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [12, 0]}],
            "fish": [{"id": "F1", "kind": "ca_linh", "pos": [12, 3]}],
            "random_fish": False,
            "monsters": [],
        }
        ids = IdAllocator()
        sim = GatherSim(tuning, scenario, Streams(1), ids)
        player = InputPlayer([{"tick": 0, "interact": True}], BUTTONS_V11, STRINGS_V11)

        # Tick 1: hái N1 -> thêm I1 ở bước 3 (SAU bước hao) -> fresh vẫn là 100 cuối tick 1
        e1 = sim.step(player.advance(0))
        self.assertEqual([n for n, _ in e1], ["gather"])
        self.assertEqual(sim.snapshot()["hold"], [{"id": "I1", "kind": "bong_dien_dien", "fresh": 100}])

        # Tick 2: đứng yên -> I1 bắt đầu hao 2 đơn vị (23998/240)
        e2 = sim.step(player.advance(1))
        self.assertEqual(e2, [])
        self.assertEqual(sim.snapshot()["hold"], [
            {"id": "I1", "kind": "bong_dien_dien", "fresh": 23998 / UNITS_PER_FRESH},
        ])

        # Dịch xuống cạnh đàn cá F1 và bắt ở tick 3: I1 hao tiếp (23996/240), I2..I4 mới ở 100
        sim.pos = [12.0, 3.0]
        p_catch = InputPlayer([{"tick": 0, "catch": True}], BUTTONS_V11, STRINGS_V11)
        e3 = sim.step(p_catch.advance(0))
        self.assertIn("fish_caught", [n for n, _ in e3])
        self.assertEqual(sim.snapshot()["hold"], [
            {"id": "I1", "kind": "bong_dien_dien", "fresh": 23996 / UNITS_PER_FRESH},
            {"id": "I2", "kind": "ca_linh", "fresh": 100},
            {"id": "I3", "kind": "ca_linh", "fresh": 100},
            {"id": "I4", "kind": "ca_linh", "fresh": 100},
        ])

        # Tick 4: tất cả I1..I4 đều hao 2 đơn vị
        sim.step(p_catch.advance(1))
        self.assertEqual(sim.snapshot()["hold"], [
            {"id": "I1", "kind": "bong_dien_dien", "fresh": 23994 / UNITS_PER_FRESH},
            {"id": "I2", "kind": "ca_linh", "fresh": 23998 / UNITS_PER_FRESH},
            {"id": "I3", "kind": "ca_linh", "fresh": 23998 / UNITS_PER_FRESH},
            {"id": "I4", "kind": "ca_linh", "fresh": 23998 / UNITS_PER_FRESH},
        ])

    def test_reserve_existing_ids_hold_full_no_leak_and_multiday_continuity(self):
        tuning = make_v12_tuning()
        tuning["gather"]["hold_capacity"] = 4
        shared_ids = IdAllocator()

        # Giỏ sẵn I5 và I2 (2 món), bắt đàn cá linh (yield 3 > free 2) -> hold_full, KHÔNG tiêu id
        sc1 = {
            "player": {"pos": [12, 3]},
            "hold": [
                {"id": "I5", "kind": "ca_loc", "fresh": 100},
                {"id": "I2", "kind": "bong_sung", "fresh": 80},
            ],
            "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [12, 0]}],
            "fish": [{"id": "F1", "kind": "ca_linh", "pos": [12, 3]}],
            "random_fish": False,
            "monsters": [],
        }
        sim1 = GatherSim(tuning, sc1, Streams(2), shared_ids, day=1)
        p = InputPlayer([{"tick": 0, "catch": True}], BUTTONS_V11, STRINGS_V11)
        e_full = sim1.step(p.advance(0))
        self.assertIn(("hold_full", {"action": "catch", "fish_id": "F1", "required": 3, "free": 2}), e_full)
        self.assertEqual([it["id"] for it in sim1.snapshot()["hold"]], ["I5", "I2"])

        # Hái 1 nút -> id tiếp theo phải là I6 (sau max đã reserve = I5)
        sim1.pos = [12.0, 0.0]
        p_h = InputPlayer([{"tick": 0, "interact": True}], BUTTONS_V11, STRINGS_V11)
        sim1.step(p_h.advance(0))
        self.assertEqual([it["id"] for it in sim1.snapshot()["hold"]], ["I5", "I2", "I6"])

        # Sang Ngày 2 dùng chung shared_ids -> cá thể mới tiếp tục I7 (tăng xuyên Ngày)
        sc2 = {
            "player": {"pos": [12, 0]},
            "hold": [],
            "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [12, 0]}],
            "random_fish": False,
            "monsters": [],
        }
        sim2 = GatherSim(tuning, sc2, Streams(2), shared_ids, day=2)
        p_h2 = InputPlayer([{"tick": 0, "interact": True}], BUTTONS_V11, STRINGS_V11)
        sim2.step(p_h2.advance(0))
        self.assertEqual(sim2.snapshot()["hold"], [{"id": "I7", "kind": "bong_dien_dien", "fresh": 100}])

    def test_custom_item_ids_allocator_compatibility(self):
        """Tương thích cả IdAllocator lẫn đối tượng ItemIds tùy biến (0-arg `.new()` hoặc `.next()`)."""
        class ZeroArgNew:
            def __init__(self):
                self.n = 0

            def reserve(self, ident):
                if ident.startswith("I") and ident[1:].isdigit():
                    self.n = max(self.n, int(ident[1:]))

            def new(self):
                self.n += 1
                return f"I{self.n}"

        class ZeroArgNext:
            def __init__(self):
                self.n = 10

            def next(self):
                self.n += 1
                return f"I{self.n}"

        tuning = make_v12_tuning()
        sc = {
            "player": {"pos": [12, 0]},
            "hold": [{"id": "I3", "kind": "ca_loc", "fresh": 100}],
            "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [12, 0]}],
            "random_fish": False,
            "monsters": [],
        }

        sim_a = GatherSim(tuning, sc, Streams(1), IdAllocator(), item_ids=ZeroArgNew())
        sim_a.step(InputPlayer([{"tick": 0, "interact": True}], BUTTONS_V11, STRINGS_V11).advance(0))
        self.assertEqual([it["id"] for it in sim_a.snapshot()["hold"]], ["I3", "I4"])

        sim_b = GatherSim(tuning, sc, Streams(1), IdAllocator(), item_ids=ZeroArgNext())
        sim_b.step(InputPlayer([{"tick": 0, "interact": True}], BUTTONS_V11, STRINGS_V11).advance(0))
        self.assertEqual([it["id"] for it in sim_b.snapshot()["hold"]], ["I3", "I11"])


class GatherFreshnessT311Tests(unittest.TestCase):
    """T311: hao giỏ −2 đơn vị/tick, ngưỡng < 30 chính xác, `spoiled` 1 lần theo id, pause dừng hao."""

    def test_ticket03_official_smoke_fresh_30_spoils_at_tick_1_once(self):
        """Mẫu đề TICKET-03: fresh 30 chạy 1 bước không input -> spoiled ở tick 1, không phát lại."""
        tuning = make_v12_tuning()
        scenario = {
            "hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30}],
            "random_fish": False,
            "monsters": [],
        }
        sess, rows = run_gather_session(tuning, scenario, [], ticks=3, seed=1)
        spoiled = evs(rows, "spoiled")
        self.assertEqual(len(spoiled), 1)
        self.assertEqual(spoiled[0], {
            "type": "event",
            "tick": 1,
            "phase": "gather",
            "name": "spoiled",
            "data": {"item_id": "I1", "kind": "ca_linh", "location": "hold"},
        })
        # Hàng ươn vẫn chiếm 1 ô trong giỏ
        self.assertEqual(sess.sim.snapshot()["hold_count"], 1)
        self.assertEqual(sess.sim.hold[0]["u"], 7200 - 6)

    def test_exact_8400_vs_8401_boundary_from_fresh_100(self):
        """ADR-0001 / research P3: 100 -> 30.0 đúng ở tick 8400 (chưa ươn), ươn đúng tick 8401."""
        tuning = make_v12_tuning()
        scenario = {
            "hold": [{"id": "I1", "kind": "ca_linh", "fresh": 100}],
            "random_fish": False,
            "monsters": [],
        }
        sim = GatherSim(tuning, scenario, Streams(1), IdAllocator())
        idle = InputPlayer([], BUTTONS_V11, STRINGS_V11).advance(0)
        spoiled_ticks = []
        for tick in range(1, 8402):
            for name, data in sim.step(idle):
                if name == "spoiled":
                    spoiled_ticks.append((tick, data))
            if tick == 8400:
                self.assertEqual(sim.hold[0]["u"], 7200)
                self.assertEqual(sim.snapshot()["hold"][0]["fresh"], 30)
                self.assertEqual(spoiled_ticks, [])
        self.assertEqual(sim.hold[0]["u"], 7198)
        self.assertEqual(spoiled_ticks, [(8401, {"item_id": "I1", "kind": "ca_linh", "location": "hold"})])

    def test_multiple_spoiled_sorted_by_id_already_spoiled_silent_and_clamp_zero(self):
        """Nhiều cá thể cùng ươn phát theo id_key (I2 trước I10); hàng đã ươn không phát; kẹp đáy 0."""
        tuning = make_v12_tuning()
        scenario = {
            "hold": [
                {"id": "I10", "kind": "ca_loc", "fresh": 30},
                {"id": "I2", "kind": "ca_linh", "fresh": 30},
                {"id": "I1", "kind": "bong_sung", "fresh": 29.999},  # đã ươn từ đầu
                {"id": "I3", "kind": "keo_neo", "fresh": 0},         # đã ở đáy 0
            ],
            "random_fish": False,
            "monsters": [],
        }
        # Bảo đảm fresh_to_units giữ đúng nhánh < 30 cho 29.999
        self.assertLess(fresh_to_units(29.999), 7200)
        self.assertEqual(units_to_fresh(0), 0)

        _, rows = run_gather_session(tuning, scenario, [], ticks=2, seed=1)
        spoiled = evs(rows, "spoiled")
        self.assertEqual([e["data"] for e in spoiled], [
            {"item_id": "I2", "kind": "ca_linh", "location": "hold"},
            {"item_id": "I10", "kind": "ca_loc", "location": "hold"},
        ])
        self.assertEqual([e["tick"] for e in spoiled], [1, 1])
        # Snapshot hold vẫn giữ thứ tự vào giỏ [I10, I2, I1, I3] và I3 kẹp ở 0
        snaps = [r for r in rows if r["type"] == "snapshot"]
        last_hold = snaps[-1]["hold"]
        self.assertEqual([it["id"] for it in last_hold], ["I10", "I2", "I1", "I3"])
        self.assertEqual(last_hold[3]["fresh"], 0)

    def test_spoiled_item_still_occupies_hold_capacity(self):
        tuning = make_v12_tuning()
        tuning["gather"]["hold_capacity"] = 1
        scenario = {
            "player": {"pos": [12, 0]},
            "hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30}],
            "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [12, 0]}],
            "random_fish": False,
            "monsters": [],
        }
        _, rows = run_gather_session(tuning, scenario, [{"tick": 0, "interact": True}], ticks=1)
        names = [e["name"] for e in evs(rows)]
        self.assertEqual(names, ["spoiled", "hold_full"])
        self.assertEqual(evs(rows, "hold_full")[0]["data"], {
            "action": "gather", "node_id": "N1", "required": 1, "free": 0,
        })

    def test_pause_freezes_freshness_decay(self):
        """Pause trong Session dừng hao tươi; resume mới bắt đầu hao ở bước đó."""
        tuning = make_v12_tuning()
        scenario = {
            "hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30}],
            "random_fish": False,
            "monsters": [],
        }
        frames = [
            {"tick": 0, "pause": True},   # tick 1: paused
            {"tick": 1, "pause": False},  # nhả phím pause
            {"tick": 5, "pause": True},   # tick 6: resumed + chạy gameplay bước 1 -> spoiled ở tick 6
        ]
        sess, rows = run_gather_session(tuning, scenario, frames, ticks=6)
        self.assertEqual([(e["tick"], e["name"]) for e in evs(rows)], [
            (1, "paused"),
            (6, "resumed"),
            (6, "spoiled"),
        ])
        # Trước tick 6, I1 vẫn nguyên 30 (chưa hao khi đang pause)
        snaps_by_tick = {r["tick"]: r for r in rows if r["type"] == "snapshot"}
        for t in range(0, 6):
            self.assertEqual(snaps_by_tick[t]["hold"][0]["fresh"], 30)
        self.assertEqual(sess.sim.hold[0]["u"], 7198)


class GatherFreshnessT312Tests(unittest.TestCase):
    """T312: LIFO cá thể, faint monster/choke, snapshot hold, inventory_items(), tất định, không vỡ v1.1."""

    def test_ticket03_handoff_smoke_interact_frame_0_exact_inventory_precision(self):
        """Mẫu bàn giao TICKET-03: fresh 100 + interact frame 0 -> hao 1 lần (23998/240) rồi cập bến."""
        tuning = make_v12_tuning()
        scenario = {
            "hold": [
                {"id": "I10", "kind": "ca_loc", "fresh": 100},
                {"id": "I2", "kind": "ca_linh", "fresh": 100},
            ],
            "random_fish": False,
            "monsters": [],
        }
        sess, rows = run_gather_session(tuning, scenario, [{"tick": 0, "interact": True}], ticks=5)
        expected_fresh = 23998 / UNITS_PER_FRESH
        expected_inv = [
            {"id": "I2", "kind": "ca_linh", "fresh": expected_fresh},
            {"id": "I10", "kind": "ca_loc", "fresh": expected_fresh},
        ]
        self.assertEqual(sess.sim.inventory_items(), expected_inv)
        # Kiểm round-trip chính xác về 23998 đơn vị
        self.assertEqual(fresh_to_units(sess.sim.inventory_items()[0]["fresh"]), 23998)
        end_ev = evs(rows, "gather_end")
        self.assertEqual(len(end_ev), 1)
        self.assertEqual(end_ev[0]["data"], {
            "reason": "docked",
            "inventory": {"items": expected_inv},
        })
        # Snapshot cuối vẫn giữ thứ tự vào giỏ [I10, I2] (khác với inventory sắp theo id)
        snaps = [r for r in rows if r["type"] == "snapshot"]
        self.assertEqual([it["id"] for it in snaps[-1]["hold"]], ["I10", "I2"])

    def test_monster_hit_and_faint_lifo_individual_items_and_empty_inventory(self):
        """Hit rơi floor(n/2) cá thể theo LIFO với fresh sau hao; ngất bỏ phần còn lại theo LIFO, kho []."""
        tuning = make_v12_tuning()
        monster = {
            "id": "M1", "kind": "ca_sau", "pos": [60, 20],
            "waypoints": [[60, 20], [64, 20]], "target_idx": 1, "state": "patrol",
        }
        # 5 cá thể, hp = 2 -> hit rơi floor(5/2) = 2 (I5, I4), còn [I1, I2, I3]
        sc_hit = {
            "player": {"pos": [60.5, 20], "hp": 2},
            "hold": [
                {"id": "I1", "kind": "ca_linh", "fresh": 100},
                {"id": "I2", "kind": "ca_loc", "fresh": 80},
                {"id": "I3", "kind": "ca_keo", "fresh": 60},
                {"id": "I4", "kind": "bong_sung", "fresh": 40},
                {"id": "I5", "kind": "keo_neo", "fresh": 30},  # ươn ngay đầu bước 1 trước hit!
            ],
            "random_fish": False,
            "monsters": [monster],
        }
        sess1, rows1 = run_gather_session(tuning, sc_hit, [], ticks=1)
        self.assertEqual([e["name"] for e in evs(rows1)], ["spoiled", "monster_hit"])
        hit_data = evs(rows1, "monster_hit")[0]["data"]
        self.assertEqual(hit_data["hp"], 1)
        self.assertEqual(hit_data["lost"], [
            {"id": "I5", "kind": "keo_neo", "fresh": 7198 / UNITS_PER_FRESH},
            {"id": "I4", "kind": "bong_sung", "fresh": 9598 / UNITS_PER_FRESH},
        ])
        self.assertEqual([it["id"] for it in sess1.sim.snapshot()["hold"]], ["I1", "I2", "I3"])

        # 3 cá thể, hp = 1 -> hit rơi 1 (I3), rồi ngất bỏ phần còn lại LIFO [I2, I1], kho []
        sc_faint = {
            "player": {"pos": [60.5, 20], "hp": 1},
            "hold": [
                {"id": "I1", "kind": "ca_linh", "fresh": 100},
                {"id": "I2", "kind": "ca_loc", "fresh": 75},
                {"id": "I3", "kind": "ca_keo", "fresh": 50},
            ],
            "random_fish": False,
            "monsters": [monster],
        }
        sess2, rows2 = run_gather_session(tuning, sc_faint, [], ticks=1)
        self.assertEqual([e["name"] for e in evs(rows2)], ["monster_hit", "faint", "gather_end"])
        self.assertEqual(evs(rows2, "monster_hit")[0]["data"]["lost"], [
            {"id": "I3", "kind": "ca_keo", "fresh": 11998 / UNITS_PER_FRESH},
        ])
        self.assertEqual(evs(rows2, "faint")[0]["data"], {
            "cause": "monster",
            "hp": 0,
            "lost": [
                {"id": "I2", "kind": "ca_loc", "fresh": 17998 / UNITS_PER_FRESH},
                {"id": "I1", "kind": "ca_linh", "fresh": 23998 / UNITS_PER_FRESH},
            ],
        })
        self.assertEqual(evs(rows2, "gather_end")[0]["data"], {
            "reason": "fainted",
            "inventory": {"items": []},
        })
        self.assertEqual(sess2.sim.inventory_items(), [])

    def test_choke_faint_drops_all_hold_lifo_and_writes_empty_inventory(self):
        """Ngất do ngạt ở v1.2 bỏ toàn bộ giỏ theo LIFO (cá thể) rồi faint -> gather_end(fainted, [])."""
        tuning = make_v12_tuning()
        sc = {
            "player": {"pos": [20, 10], "hp": 1, "oxygen_ticks": 0, "zero_oxy_ticks": 59},
            "hold": [
                {"id": "I1", "kind": "ca_linh", "fresh": 100},
                {"id": "I2", "kind": "bong_dien_dien", "fresh": 50},
            ],
            "random_fish": False,
            "monsters": [],
        }
        sess, rows = run_gather_session(tuning, sc, [], ticks=1)
        self.assertEqual([e["name"] for e in evs(rows)], ["choke", "faint", "gather_end"])
        self.assertEqual(evs(rows, "faint")[0]["data"], {
            "hp": 0,
            "lost": [
                {"id": "I2", "kind": "bong_dien_dien", "fresh": 11998 / UNITS_PER_FRESH},
                {"id": "I1", "kind": "ca_linh", "fresh": 23998 / UNITS_PER_FRESH},
            ],
        })
        self.assertEqual(evs(rows, "gather_end")[0]["data"], {
            "reason": "fainted",
            "inventory": {"items": []},
        })
        self.assertEqual(sess.sim.inventory_items(), [])

    def test_v12_session_is_byte_deterministic_and_v11_without_freshness_unchanged(self):
        """Tất định từng byte JSONL ở v1.2; không có tuning.freshness giữ nguyên kho đếm v1.1."""
        tuning_v12 = make_v12_tuning()
        sc_v12 = {
            "player": {"pos": [12, 0]},
            "hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30}],
            "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [12, 0]}],
            "random_fish": False,
            "monsters": [],
        }
        frames = [{"tick": 0, "interact": True}]
        _, r1 = run_gather_session(tuning_v12, sc_v12, frames, ticks=10, seed=7)
        _, r2 = run_gather_session(tuning_v12, sc_v12, frames, ticks=10, seed=7)
        self.assertEqual("\n".join(dumps(x) for x in r1), "\n".join(dumps(x) for x in r2))

        # Không có tuning.freshness -> hành vi v1.1 không đổi
        tuning_v11 = copy.deepcopy(load_contract()["tuning"])
        self.assertNotIn("freshness", tuning_v11)
        sc_v11 = {
            "player": {"pos": [2, 0]},
            "hold": ["ca_loc", "ca_linh"],
            "random_fish": False,
            "monsters": [],
        }
        sess_v11, rows_v11 = run_gather_session(tuning_v11, sc_v11, [{"tick": 0, "interact": True}], ticks=2)
        self.assertEqual(evs(rows_v11, "spoiled"), [])
        self.assertEqual(sess_v11.sim.inventory_items(), {"ca_linh": 1, "ca_loc": 1})
        self.assertEqual(sess_v11.sim.snapshot()["hold"], ["ca_loc", "ca_linh"])
        # Không lộ trường nội bộ `u` trong JSONL v1.2
        self.assertNotIn('"u":', "\n".join(dumps(x) for x in r1))
        # Kiểm JSON hợp lệ
        for line in (dumps(x) for x in r1):
            json.loads(line)


if __name__ == "__main__":
    unittest.main()
