"""Unit tests Phase 3 (TICKET-03, Contract v1.2) — Phần việc của TV1:
- Schema & Adapter kho cá thể {id, kind, fresh} (từ chối kho đếm -> mã 2).
- Hao tươi trong giỏ (-0.5/s), ngưỡng spoiled tại 30, phát theo id đúng một lần.
- Rơi hàng cá thể theo LIFO khi monster_hit và faint.
- Mở rộng: Dòng nước lũ (current) — warning t-120, start t=1800k, lực 1.5 m/s ở d >= 10, end elapsed/phase_end.
"""

import json
import unittest

from chonoi.errors import BadInput
from chonoi.inventory import read_inventory, validate_items
from helpers import Workdir, close, events, frames, read_jsonl, run_headless, snapshots, write_json


class TestPhase3TV1(unittest.TestCase):
    def test_spoiled_threshold_at_30_emits_once_in_id_order(self):
        """Mẫu chuẩn TICKET-03: cá thể bắt đầu đúng fresh 30 nên ươn ở bước đầu (tick 1)."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "hold": [
                        {"id": "I10", "kind": "ca_loc", "fresh": 30},
                        {"id": "I1", "kind": "ca_linh", "fresh": 30},
                    ],
                    "random_fish": False,
                    "monsters": [],
                }
            })
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", sc, "--out", w.path("out.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("out.jsonl"))
            sp = events(rows, "spoiled")
            # Phát đúng 1 lần ở tick 1 theo thứ tự id (I1 trước I10), không phát lại ở tick 2
            self.assertEqual(len(sp), 2)
            self.assertEqual(sp[0], {
                "type": "event", "tick": 1, "phase": "gather", "name": "spoiled",
                "data": {"item_id": "I1", "kind": "ca_linh", "location": "hold"},
            })
            self.assertEqual(sp[1], {
                "type": "event", "tick": 1, "phase": "gather", "name": "spoiled",
                "data": {"item_id": "I10", "kind": "ca_loc", "location": "hold"},
            })

    def test_new_item_starts_at_100_and_decays_next_tick(self):
        """Hàng mới hái/bắt có fresh = 100 ở bước lấy, bắt đầu hao từ bước sau."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {"pos": [12, 0]},
                    "random_fish": False,
                    "monsters": [],
                }
            })
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", sc, "--inputs", inp, "--snapshot-every", "1",
                                     "--out", w.path("out.jsonl"))
            self.assertEqual(code, 0, err)
            snaps = {r["tick"]: r for r in snapshots(read_jsonl(w.path("out.jsonl")))}
            self.assertEqual(snaps[1]["hold"], [{"id": "I1", "kind": "bong_dien_dien", "fresh": 100}])
            self.assertTrue(close(snaps[2]["hold"][0]["fresh"], 100 - 0.5 / 60.0, 0.01))

    def test_v12_rejects_count_inventory_and_invalid_items(self):
        """Contract v1.2 trả mã 2 cho file kho đếm hoặc sai schema, kind lạ, id trùng, fresh ngoài miền."""
        for bad in (
            {"ca_linh": 3},
            [{"id": "I1", "kind": "ca_linh"}],
            [{"id": "", "kind": "ca_linh", "fresh": 100}],
            [{"id": "I1", "kind": "ca_la", "fresh": 100}],
            [{"id": "I1", "kind": "ca_linh", "fresh": 100}, {"id": "I1", "kind": "ca_loc", "fresh": 90}],
            [{"id": "I1", "kind": "ca_linh", "fresh": -0.1}],
            [{"id": "I1", "kind": "ca_linh", "fresh": 100.1}],
        ):
            with self.assertRaises(BadInput):
                validate_items(bad)

    def test_current_warning_start_push_and_elapsed_end(self):
        """Dòng nước lũ: warning ở 1680, start ở 1800, đẩy 1.5 m/s ở d >= 10, end(elapsed) ở 2280."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {"pos": [50.0, 15.0], "oxygen_ticks": 1800},
                    "random_fish": False,
                    "monsters": [],
                    "current_direction": 1,
                }
            })
            # Tại 1680 giữ đủ oxy bằng cách cho player nổi rồi lặn, hoặc kiểm tra với scenario
            inp = write_json(w.path("in.json"), frames(
                {"tick": 0, "move": [0, -1]},     # bơi lên mặt nước lấy oxy
                {"tick": 1550, "move": [0, 1]},   # lặn xuống d >= 10 trước tick 1800
                {"tick": 1790, "move": [0, 0]},   # đứng yên tại d >= 10 trước 1800
            ))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2285",
                                     "--scenario", sc, "--inputs", inp, "--snapshot-every", "1",
                                     "--out", w.path("c.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("c.jsonl"))
            warns = events(rows, "current_warning")
            starts = events(rows, "current_start")
            ends = events(rows, "current_end")
            self.assertEqual(warns[0], {
                "type": "event", "tick": 1680, "phase": "gather",
                "name": "current_warning", "data": {"starts_at_phase_tick": 1800},
            })
            self.assertEqual(starts[0], {
                "type": "event", "tick": 1800, "phase": "gather",
                "name": "current_start", "data": {"direction": 1, "duration_ticks": 480},
            })
            self.assertEqual(ends[0], {
                "type": "event", "tick": 2280, "phase": "gather",
                "name": "current_end", "data": {"direction": 1, "reason": "elapsed"},
            })
            snaps = {r["tick"]: r for r in snapshots(rows)}
            # Đếm cả tick hoạt động vừa chụp: ở 1800 là 480, ở 2279 là 1, ở 2280 là None
            self.assertEqual(snaps[1800]["current"], {"direction": 1, "ticks_left": 480})
            self.assertEqual(snaps[2279]["current"], {"direction": 1, "ticks_left": 1})
            self.assertIsNone(snaps[2280]["current"])
            # Lực dòng đẩy +1.5 m/s trong 8s (480 tick) = +12.0 m mà không tích lũy vào vel
            self.assertEqual(snaps[1850]["player"]["vel"], [0.0, 0.0])
            self.assertTrue(close(snaps[2279]["player"]["pos"][0] - snaps[1799]["player"]["pos"][0], 12.0, 0.05))

    def test_current_ends_with_phase_end_before_faint_and_gather_end(self):
        """Nếu ca kết thúc khi dòng lũ đang chạy, phát current_end(phase_end) trước faint và gather_end."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {"pos": [50.0, 15.0], "hp": 1},
                    "random_fish": False,
                    "monsters": [],
                    "current_direction": -1,
                    "time_left_ticks": 1800,
                }
            })
            inp = write_json(w.path("in.json"), frames({"tick": 0, "move": [0, -1]}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2000",
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("end.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("end.jsonl"))
            ev_names = [(r["tick"], r["name"], r["data"]) for r in rows if r["type"] == "event"]
            # Tại tick 1800: current_start -> current_end(phase_end) -> gather_end(time)
            t1800 = [(n, d) for t, n, d in ev_names if t == 1800]
            self.assertEqual([n for n, _ in t1800], ["current_start", "current_end", "gather_end"])
            self.assertEqual(t1800[1][1], {"direction": -1, "reason": "phase_end"})


if __name__ == "__main__":
    unittest.main()
