"""Test tập trung cho Gather Lát 2 (TV2): hái rau, bắt cá, giỏ đầy, ưu tiên bến, tích hợp kho.

Chạy hộp đen qua `headless_cmd` trong game.contract.json để giữ tính độc lập với khung.
Lưu ý: payload chi tiết của `gather`, `fish_caught`, `hold_full` và vài biên PRD-0 chưa có
trong repo nên test chỉ kiểm các hành vi/bất biến đã xác minh từ starter & game.contract.json.
"""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def _tuning_gather():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]["gather"]


class GatherSlice2PlantTests(unittest.TestCase):
    def test_harvest_at_surface_sets_regrow_and_regrows(self):
        g = _tuning_gather()
        regrow_ticks = int(round(g["regrow_s"] * 60))
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [20, 0]},
                "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [21, 0]}],
                "random_fish": False,
            }})
            inp = write_json(w.path("in.json"), frames(
                {"tick": 0, "interact": True},
                {"tick": 1, "interact": False},
                {"tick": 2, "interact": True},  # nút đang mọc lại -> không hái được
            ))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "5",
                                     "--scenario", sc, "--inputs", inp,
                                     "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            gather_evs = events(rows, "gather")
            self.assertEqual(len(gather_evs), 1)
            self.assertEqual(gather_evs[0]["tick"], 1)
            self.assertEqual(gather_evs[0]["data"]["node_id"], "N1")
            snaps = {s["tick"]: s for s in snapshots(rows)}
            self.assertEqual(snaps[1]["hold"], ["bong_dien_dien"] * g["node_yield"])
            self.assertFalse(snaps[1]["nodes"][0]["ready"])
            self.assertEqual(snaps[1]["nodes"][0]["regrow_ticks"], regrow_ticks)
            # Nút chưa mọc lại nên lần interact ở tick 2 không thay đổi giỏ
            self.assertEqual(snaps[3]["hold"], ["bong_dien_dien"] * g["node_yield"])

        # Kiểm tra nút mọc lại sau regrow_ticks rồi hái lại được
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [20, 0]},
                "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [20.5, 0], "regrow_ticks": 3}],
                "random_fish": False,
            }})
            inp = write_json(w.path("in.json"), frames(
                {"tick": 0, "interact": True},   # regrow_ticks còn 2 -> chưa ready
                {"tick": 1, "interact": False},
                {"tick": 2, "interact": True},   # bước này regrow_ticks về 0 -> node_regrown rồi hái được
            ))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "4",
                                     "--scenario", sc, "--inputs", inp,
                                     "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            regrown = events(rows, "node_regrown")
            self.assertEqual(len(regrown), 1)
            self.assertEqual(regrown[0]["tick"], 3)
            self.assertEqual(regrown[0]["data"]["node_id"], "N1")
            gather_evs = events(rows, "gather")
            self.assertEqual(len(gather_evs), 1)
            self.assertEqual(gather_evs[0]["tick"], 3)
            self.assertEqual(snapshots(rows)[-1]["hold"], ["bong_sung"] * g["node_yield"])

    def test_harvest_blocked_underwater_and_out_of_radius(self):
        g = _tuning_gather()
        with Workdir() as w:
            # Dưới nước nhưng trong bán kính phẳng
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [20, g["surface_depth"] + 0.5]},
                "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [20, 0]}],
                "random_fish": False,
            }})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(events(rows, "gather"), [])
            self.assertEqual(snapshots(rows)[-1]["hold"], [])

            # Mặt nước nhưng ngoài interact_radius
            sc2 = write_json(w.path("sc2.json"), {"gather": {
                "player": {"pos": [20, 0]},
                "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [20 + g["interact_radius"] + 0.5, 0]}],
                "random_fish": False,
            }})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", sc2, "--inputs", inp, "--out", w.path("o2.jsonl"))
            self.assertEqual(code, 0, err)
            rows2 = read_jsonl(w.path("o2.jsonl"))
            self.assertEqual(events(rows2, "gather"), [])
            self.assertEqual(snapshots(rows2)[-1]["hold"], [])

    def test_harvest_deterministic_distance_and_id_tiebreak(self):
        with Workdir() as w:
            # Hai nút cách đều 1.0 đơn vị; N10 đứng trước N2 trong scenario nhưng N2 phải được chọn trước
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [30, 0]},
                "nodes": [
                    {"id": "N10", "kind": "bong_sung", "pos": [31, 0]},
                    {"id": "N2", "kind": "bong_dien_dien", "pos": [29, 0]},
                ],
                "random_fish": False,
            }})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            gather_evs = events(read_jsonl(w.path("o.jsonl")), "gather")
            self.assertEqual(len(gather_evs), 1)
            self.assertEqual(gather_evs[0]["data"]["node_id"], "N2")

            # Nút gần hơn luôn thắng dù id lớn hơn
            sc2 = write_json(w.path("sc2.json"), {"gather": {
                "player": {"pos": [30, 0]},
                "nodes": [
                    {"id": "N1", "kind": "bong_dien_dien", "pos": [31.5, 0]},
                    {"id": "N9", "kind": "bong_sung", "pos": [29.5, 0]},
                ],
                "random_fish": False,
            }})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", sc2, "--inputs", inp, "--out", w.path("o2.jsonl"))
            self.assertEqual(code, 0, err)
            gather_evs2 = events(read_jsonl(w.path("o2.jsonl")), "gather")
            self.assertEqual(gather_evs2[0]["data"]["node_id"], "N9")


class GatherSlice2FishTests(unittest.TestCase):
    def test_catch_underwater_yield_removal_and_cooldown(self):
        g = _tuning_gather()
        cd_ticks = int(round(g["catch_cooldown_s"] * 60))
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [30, 10]},
                "fish": [
                    {"id": "F1", "kind": "ca_linh", "pos": [30.5, 10]},
                    {"id": "F2", "kind": "ca_loc", "pos": [31.0, 10]},
                ],
                "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [50, 0]}],
            }})
            inp = write_json(w.path("in.json"), frames(
                {"tick": 0, "catch": True},            # bắt F1 (gần hơn), đặt cooldown = cd_ticks
                {"tick": 1, "catch": False},
                {"tick": 2, "catch": True},            # đang hồi chiêu -> không bắt được F2
                {"tick": 3, "catch": False},
                {"tick": cd_ticks, "catch": True},     # vừa hết hồi chiêu -> bắt được F2
            ))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", str(cd_ticks + 2),
                                     "--scenario", sc, "--inputs", inp,
                                     "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            caught = events(rows, "fish_caught")
            self.assertEqual(len(caught), 2)
            self.assertEqual(caught[0]["tick"], 1)
            self.assertEqual(caught[0]["data"]["fish_id"], "F1")
            self.assertEqual(caught[1]["tick"], cd_ticks + 1)
            self.assertEqual(caught[1]["data"]["fish_id"], "F2")

            snaps = {s["tick"]: s for s in snapshots(rows)}
            self.assertEqual(snaps[1]["player"]["catch_cd_ticks"], cd_ticks)
            self.assertEqual(snaps[1]["hold"], ["ca_linh"] * g["fish_yield"]["ca_linh"])
            self.assertEqual([f["id"] for f in snaps[1]["fish"]], ["F2"])
            # Ở tick 3 (sau lần bấm hụt vì cooldown ở tick 2), F2 vẫn còn
            self.assertEqual([f["id"] for f in snaps[3]["fish"]], ["F2"])
            # Sau khi hết cooldown ở tick cd_ticks + 1, F2 đã được bắt
            self.assertEqual(snaps[cd_ticks + 1]["fish"], [])
            expected_hold = ["ca_linh"] * g["fish_yield"]["ca_linh"] + ["ca_loc"] * g["fish_yield"]["ca_loc"]
            self.assertEqual(snaps[cd_ticks + 1]["hold"], expected_hold)

    def test_catch_blocked_at_surface_and_out_of_radius(self):
        g = _tuning_gather()
        with Workdir() as w:
            # Đang ở mặt nước dù cá nằm trong catch_radius
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [30, g["surface_depth"]]},
                "fish": [{"id": "F1", "kind": "ca_loc", "pos": [30, g["surface_depth"] + 0.5]}],
            }})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "catch": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(events(rows, "fish_caught"), [])
            self.assertEqual(len(snapshots(rows)[-1]["fish"]), 1)

            # Dưới nước nhưng ngoài catch_radius
            sc2 = write_json(w.path("sc2.json"), {"gather": {
                "player": {"pos": [30, 10]},
                "fish": [{"id": "F1", "kind": "ca_loc", "pos": [30 + g["catch_radius"] + 0.5, 10]}],
            }})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", sc2, "--inputs", inp, "--out", w.path("o2.jsonl"))
            self.assertEqual(code, 0, err)
            rows2 = read_jsonl(w.path("o2.jsonl"))
            self.assertEqual(events(rows2, "fish_caught"), [])
            self.assertEqual(len(snapshots(rows2)[-1]["fish"]), 1)

    def test_catch_deterministic_distance_and_id_tiebreak(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [30, 10]},
                "fish": [
                    {"id": "F10", "kind": "ca_loc", "pos": [31, 10]},
                    {"id": "F2", "kind": "ca_linh", "pos": [29, 10]},
                ],
            }})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "catch": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            caught = events(read_jsonl(w.path("o.jsonl")), "fish_caught")
            self.assertEqual(len(caught), 1)
            self.assertEqual(caught[0]["data"]["fish_id"], "F2")


class GatherSlice2CapacityDockAndInventoryTests(unittest.TestCase):
    def test_hold_capacity_never_exceeded(self):
        g = _tuning_gather()
        cap = g["hold_capacity"]
        with Workdir() as w:
            # Giỏ đã đầy: hái nút phải báo hold_full, không tăng giỏ, nút vẫn ready
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [20, 0]},
                "hold": ["ca_loc"] * cap,
                "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [20.5, 0]}],
                "random_fish": False,
            }})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(events(rows, "gather"), [])
            self.assertEqual(len(events(rows, "hold_full")), 1)
            last = snapshots(rows)[-1]
            self.assertEqual(last["hold_count"], cap)
            self.assertTrue(last["nodes"][0]["ready"])

            # Giỏ đã đầy: bắt cá phải báo hold_full, không tăng giỏ, cá vẫn còn
            sc2 = write_json(w.path("sc2.json"), {"gather": {
                "player": {"pos": [30, 10]},
                "hold": ["ca_loc"] * cap,
                "fish": [{"id": "F1", "kind": "ca_loc", "pos": [30.5, 10]}],
            }})
            inp2 = write_json(w.path("in2.json"), frames({"tick": 0, "catch": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", sc2, "--inputs", inp2, "--out", w.path("o2.jsonl"))
            self.assertEqual(code, 0, err)
            rows2 = read_jsonl(w.path("o2.jsonl"))
            self.assertEqual(events(rows2, "fish_caught"), [])
            self.assertEqual(len(events(rows2, "hold_full")), 1)
            last2 = snapshots(rows2)[-1]
            self.assertEqual(last2["hold_count"], cap)
            self.assertEqual(len(last2["fish"]), 1)

            # Giỏ thiếu chỗ cho fish_yield của ca_linh: tuyệt đối không vượt hold_capacity
            if g["fish_yield"]["ca_linh"] > 1:
                sc3 = write_json(w.path("sc3.json"), {"gather": {
                    "player": {"pos": [30, 10]},
                    "hold": ["ca_loc"] * (cap - 1),
                    "fish": [{"id": "F1", "kind": "ca_linh", "pos": [30.5, 10]}],
                }})
                code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                         "--scenario", sc3, "--inputs", inp2, "--out", w.path("o3.jsonl"))
                self.assertEqual(code, 0, err)
                rows3 = read_jsonl(w.path("o3.jsonl"))
                self.assertLessEqual(snapshots(rows3)[-1]["hold_count"], cap)
                self.assertGreaterEqual(len(events(rows3, "hold_full")), 1)

    def test_dock_priority_over_harvest_and_writes_inventory_once(self):
        g = _tuning_gather()
        dock = g["dock_pos"]
        with Workdir() as w:
            # Đặt nút sẵn sàng ngay tại bến -> bấm interact phải ưu tiên cập bến (docked), không hái
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": list(dock)},
                "hold": ["ca_loc"],
                "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [dock[0] + 0.5, 0]}],
                "random_fish": False,
            }})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            inv = w.path("inv.json")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "10",
                                     "--scenario", sc, "--inputs", inp,
                                     "--inventory-out", inv, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(events(rows, "gather"), [])
            end_evs = events(rows, "gather_end")
            self.assertEqual(len(end_evs), 1)
            self.assertEqual(end_evs[0]["data"]["reason"], "docked")
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {"ca_loc": 1}})

    def test_harvest_catch_dock_handoff_to_quan_and_deterministic_bytes(self):
        g = _tuning_gather()
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [6, 0]},
                "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [6, 0]}],
                "fish": [{"id": "F1", "kind": "ca_linh", "pos": [6, 2]}],
            }})
            # Hái N1 ở tick 0, lặn xuống d~2 (mất ~30-40 tick), bắt F1 ở tick 45, bơi về bến [2,0], cập bến ở tick 200
            inp = write_json(w.path("in.json"), frames(
                {"tick": 0, "interact": True, "move": [0, 1]},
                {"tick": 1, "interact": False},
                {"tick": 40, "move": [0, 0], "catch": True},
                {"tick": 41, "catch": False, "move": [-1, -0.5]},
                {"tick": 200, "move": [0, 0], "interact": True},
            ))
            inv1, inv2 = w.path("inv1.json"), w.path("inv2.json")
            out1, out2 = w.path("g1.jsonl"), w.path("g2.jsonl")
            for out, inv in ((out1, inv1), (out2, inv2)):
                code, err = run_headless("--mode", "gather", "--seed", "7", "--ticks", "250",
                                         "--scenario", sc, "--inputs", inp,
                                         "--inventory-out", inv, "--out", out)
                self.assertEqual(code, 0, err)
            # Tất định từng byte cả JSONL và file kho
            with open(out1, "rb") as a, open(out2, "rb") as b:
                self.assertEqual(a.read(), b.read())
            with open(inv1, "rb") as a, open(inv2, "rb") as b:
                self.assertEqual(a.read(), b.read())

            expected_items = {
                "bong_dien_dien": g["node_yield"],
                "ca_linh": g["fish_yield"]["ca_linh"],
            }
            with open(inv1, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": expected_items})

            # Bàn giao sang chế độ quan
            code, err = run_headless("--mode", "quan", "--seed", "7", "--ticks", "0",
                                     "--inventory", inv1, "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)
            self.assertEqual(snapshots(read_jsonl(w.path("q.jsonl")))[0]["stock"], expected_items)


if __name__ == "__main__":
    unittest.main()
