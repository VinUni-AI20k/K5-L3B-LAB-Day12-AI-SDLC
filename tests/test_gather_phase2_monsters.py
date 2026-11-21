"""Test tập trung cho TV2 Phase 2 (TICKET-02 v1.1): Cá Sấu Năm Chèo (T220–T223) và ngữ cảnh Ngày (T246).

Dùng bản sao contract v1.1 tạm trong `Workdir` (qua biến môi trường `CHONOI_CONTRACT`) chứa
khối `tuning.gather.monsters` chuẩn TICKET-02 §1.2, §4.1 để kiểm độc lập trong khi chờ TV1
nâng `game.contract.json` lên v1.1 — không sửa `game.contract.json` hay fixture của TV6.
"""

import copy
import json
import math
import os
import subprocess
import unittest

from chonoi.ids import IdAllocator
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim
from helpers import ROOT, Workdir, close, events, frames, headless_cmd, read_jsonl, snapshots, write_json

BASE_V11_FIXTURE = os.path.join(ROOT, "tests", "fixtures", "contract-v1.1-day.json")

MONSTERS_TUNING = {
    "species": {
        "ca_sau": {
            "patrol_speed": 1.0,
            "chase_speed": 3.0,
            "detect_radius": 10,
            "exit_radius": 16,
            "depths": [10, 30],
            "hit_radius": 1.5,
            "recoil_ticks": 60,
            "recoil_dist": 2.0,
        }
    },
    "spawns": [
        {"id": "M1", "kind": "ca_sau", "pos": [60, 24], "waypoints": [[60, 24], [64, 24]], "from_day": 1},
        {"id": "M2", "kind": "ca_sau", "pos": [85, 18], "waypoints": [[85, 18], [89, 18]], "from_day": 3},
    ],
    "invuln_ticks": 90,
    "loss_ratio": 0.5,
}


def _make_v11_contract(workdir: Workdir) -> str:
    with open(BASE_V11_FIXTURE, encoding="utf-8") as f:
        c = json.load(f)
    c["tuning"]["gather"]["monsters"] = copy.deepcopy(MONSTERS_TUNING)
    return write_json(workdir.path("contract-v1.1-monsters.json"), c)


def _run_v11(contract_path: str, *args):
    env = dict(os.environ, CHONOI_CONTRACT=contract_path)
    p = subprocess.run([*headless_cmd(), *args], cwd=ROOT, capture_output=True, text=True, env=env)
    return p.returncode, p.stderr


class MonsterPatrolChaseTests(unittest.TestCase):
    def test_patrol_speed_1ms_and_waypoint_flip(self):
        """AC-P2-08: Cá Sấu tuần tra 1.0 m/s giữa [60,24] và [64,24], đổi waypoint bước sau khi tới."""
        with Workdir() as w:
            contract = _make_v11_contract(w)
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [2, 0]},
                "random_fish": False,
            }})
            code, err = _run_v11(contract, "--mode", "gather", "--seed", "1", "--ticks", "245",
                                 "--scenario", sc, "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            snaps = {s["tick"]: s for s in snapshots(read_jsonl(w.path("o.jsonl")))}
            # Ngày 1 / gather độc lập: chỉ có M1, chưa có M2
            self.assertEqual([m["id"] for m in snaps[0]["monsters"]], ["M1"])
            self.assertEqual(snaps[0]["monsters"][0]["pos"], [60, 24])
            self.assertEqual(snaps[0]["monsters"][0]["target_idx"], 1)
            # Sau 60 tick (1 giây) đi đúng 1.0 m
            m60 = snaps[60]["monsters"][0]
            self.assertEqual(m60["state"], "patrol")
            self.assertTrue(close(m60["pos"][0], 61.0, 0.005), m60)
            self.assertTrue(close(m60["pos"][1], 24.0, 0.005), m60)
            # Sau 240 tick (4 giây) tới [64, 24] và đổi target_idx sang 0 cho bước sau
            m240 = snaps[240]["monsters"][0]
            self.assertTrue(close(m240["pos"][0], 64.0, 0.005), m240)
            self.assertEqual(m240["target_idx"], 0)
            # Bước 241 bắt đầu quay lại về [60, 24]
            m241 = snaps[241]["monsters"][0]
            self.assertLess(m241["pos"][0], 64.0)

    def test_chase_trigger_speed_and_exit_thresholds(self):
        """AC-P2-09: d >= 10 và dist <= 10 -> chase 3.0 m/s; d < 10 hoặc dist > 16 -> patrol."""
        with Workdir() as w:
            contract = _make_v11_contract(w)
            # 1) Người chơi ở d = 9.5 (< 10) dù cách chỉ 5 m -> KHÔNG chase
            sc_shallow = write_json(w.path("sc_shallow.json"), {"gather": {
                "player": {"pos": [60, 9.5]},
                "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [60, 14.5], "waypoints": [[60, 14.5], [64, 14.5]]}],
                "random_fish": False,
            }})
            code, err = _run_v11(contract, "--mode", "gather", "--seed", "1", "--ticks", "5",
                                 "--scenario", sc_shallow, "--snapshot-every", "1", "--out", w.path("o_sh.jsonl"))
            self.assertEqual(code, 0, err)
            self.assertEqual(snapshots(read_jsonl(w.path("o_sh.jsonl")))[-1]["monsters"][0]["state"], "patrol")

            # 2) Người chơi ở d = 10.0, cách đúng 10.0 m -> chuyển chase và bơi 3.0 m/s (0.05 m/tick)
            sc_chase = write_json(w.path("sc_chase.json"), {"gather": {
                "player": {"pos": [50, 10]},
                "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [60, 10], "waypoints": [[60, 10], [64, 10]]}],
                "random_fish": False,
            }})
            code, err = _run_v11(contract, "--mode", "gather", "--seed", "1", "--ticks", "60",
                                 "--scenario", sc_chase, "--snapshot-every", "1", "--out", w.path("o_ch.jsonl"))
            self.assertEqual(code, 0, err)
            snaps = {s["tick"]: s for s in snapshots(read_jsonl(w.path("o_ch.jsonl")))}
            self.assertEqual(snaps[1]["monsters"][0]["state"], "chase")
            # Sau 60 tick ở 3.0 m/s: từ x=60 về x=57.0
            self.assertTrue(close(snaps[60]["monsters"][0]["pos"][0], 57.0, 0.01), snaps[60]["monsters"][0])
            self.assertTrue(close(snaps[60]["monsters"][0]["pos"][1], 10.0, 0.01), snaps[60]["monsters"][0])

            # 3) Thoát chase khi dist > 16 m (nhưng giữ chase ở đúng dist = 16.0 m)
            sc_exit_dist = write_json(w.path("sc_ed.json"), {"gather": {
                "player": {"pos": [44, 15]},
                "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [60, 15], "waypoints": [[60, 15], [64, 15]],
                              "state": "chase"}],
                "random_fish": False,
            }})
            code, err = _run_v11(contract, "--mode", "gather", "--seed", "1", "--ticks", "1",
                                 "--scenario", sc_exit_dist, "--snapshot-every", "1", "--out", w.path("o_ed16.jsonl"))
            self.assertEqual(code, 0, err)
            self.assertEqual(snapshots(read_jsonl(w.path("o_ed16.jsonl")))[1]["monsters"][0]["state"], "chase")

            sc_exit_far = write_json(w.path("sc_ef.json"), {"gather": {
                "player": {"pos": [43.9, 15]},
                "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [60, 15], "waypoints": [[60, 15], [64, 15]],
                              "state": "chase"}],
                "random_fish": False,
            }})
            code, err = _run_v11(contract, "--mode", "gather", "--seed", "1", "--ticks", "1",
                                 "--scenario", sc_exit_far, "--snapshot-every", "1", "--out", w.path("o_ef.jsonl"))
            self.assertEqual(code, 0, err)
            self.assertEqual(snapshots(read_jsonl(w.path("o_ef.jsonl")))[1]["monsters"][0]["state"], "patrol")

            # 4) Thoát chase khi người chơi lên d < 10
            sc_exit_depth = write_json(w.path("sc_edep.json"), {"gather": {
                "player": {"pos": [60, 9.9]},
                "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [60, 12], "waypoints": [[60, 12], [64, 12]],
                              "state": "chase"}],
                "random_fish": False,
            }})
            code, err = _run_v11(contract, "--mode", "gather", "--seed", "1", "--ticks", "1",
                                 "--scenario", sc_exit_depth, "--snapshot-every", "1", "--out", w.path("o_edep.jsonl"))
            self.assertEqual(code, 0, err)
            self.assertEqual(snapshots(read_jsonl(w.path("o_edep.jsonl")))[1]["monsters"][0]["state"], "patrol")


class MonsterHitRecoilInvulnFaintTests(unittest.TestCase):
    def test_hit_exact_boundary_lifo_odd_even_and_id_tiebreak(self):
        """AC-P2-10: hit tại biên <= 1.5 m, d >= 10, rơi floor(n/2) theo LIFO (chẵn/lẻ/1 món), hòa theo id."""
        with Workdir() as w:
            contract = _make_v11_contract(w)

            # 1) Giỏ 5 món (lẻ): rơi floor(5/2) = 2 món mới nhất (cuối mảng trước)
            sc5 = write_json(w.path("sc5.json"), {"gather": {
                "player": {"pos": [60, 10]},
                "hold": ["ca_loc", "bong_sung", "ca_linh", "ca_linh", "bong_dien_dien"],
                # Đặt M1 tại [61.55, 10]: trong 1 bước chase (-0.05 m) vào đúng biên 1.50 m!
                "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [61.55, 10], "waypoints": [[61.55, 10], [65, 10]]}],
                "random_fish": False,
            }})
            code, err = _run_v11(contract, "--mode", "gather", "--seed", "1", "--ticks", "1",
                                 "--scenario", sc5, "--snapshot-every", "1", "--out", w.path("o5.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o5.jsonl"))
            hits = events(rows, "monster_hit")
            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0]["data"], {
                "monster_id": "M1",
                "hp": 2,
                "lost": ["bong_dien_dien", "ca_linh"],
                "pos": [60.0, 10.0],
            })
            snap1 = snapshots(rows)[1]
            self.assertEqual(snap1["hold"], ["ca_loc", "bong_sung", "ca_linh"])
            self.assertEqual(snap1["player"]["hp"], 2)
            self.assertEqual(snap1["player"]["invuln_ticks"], 90)
            self.assertEqual(snap1["monsters"][0]["state"], "recoil")
            self.assertEqual(snap1["monsters"][0]["state_ticks_left"], 60)

            # 2) Ngoài biên (1.56 -> sau bước chase 0.05 còn 1.51 > 1.5) -> KHÔNG hit
            sc_out = write_json(w.path("sc_out.json"), {"gather": {
                "player": {"pos": [60, 10]},
                "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [61.56, 10], "waypoints": [[61.56, 10], [65, 10]]}],
                "random_fish": False,
            }})
            code, err = _run_v11(contract, "--mode", "gather", "--seed", "1", "--ticks", "1",
                                 "--scenario", sc_out, "--snapshot-every", "1", "--out", w.path("o_out.jsonl"))
            self.assertEqual(code, 0, err)
            self.assertEqual(events(read_jsonl(w.path("o_out.jsonl")), "monster_hit"), [])

            # 3) Giỏ 4 món (chẵn) -> rơi floor(4/2) = 2; giỏ 1 món -> rơi floor(1/2) = 0 nhưng vẫn mất Máu
            for hold_init, want_lost, want_rem in (
                (["ca_loc", "bong_sung", "ca_linh", "bong_dien_dien"], ["bong_dien_dien", "ca_linh"], ["ca_loc", "bong_sung"]),
                (["ca_loc"], [], ["ca_loc"]),
            ):
                sc = write_json(w.path("sc_h.json"), {"gather": {
                    "player": {"pos": [60, 15]},
                    "hold": hold_init,
                    "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [60, 15], "waypoints": [[60, 15], [64, 15]]}],
                    "random_fish": False,
                }})
                code, err = _run_v11(contract, "--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", sc, "--snapshot-every", "1", "--out", w.path("o_h.jsonl"))
                self.assertEqual(code, 0, err)
                rows_h = read_jsonl(w.path("o_h.jsonl"))
                self.assertEqual(events(rows_h, "monster_hit")[0]["data"]["lost"], want_lost)
                self.assertEqual(snapshots(rows_h)[1]["hold"], want_rem)

            # 4) Hai con cùng khoảng cách (M10 liệt kê trước M2) -> tối đa 1 hit, chọn M2, M10 không recoil
            sc_tie = write_json(w.path("sc_tie.json"), {"gather": {
                "player": {"pos": [60, 15]},
                "monsters": [
                    {"id": "M10", "kind": "ca_sau", "pos": [61, 15], "waypoints": [[61, 15], [65, 15]]},
                    {"id": "M2", "kind": "ca_sau", "pos": [59, 15], "waypoints": [[59, 15], [55, 15]]},
                ],
                "random_fish": False,
            }})
            code, err = _run_v11(contract, "--mode", "gather", "--seed", "1", "--ticks", "1",
                                 "--scenario", sc_tie, "--snapshot-every", "1", "--out", w.path("o_tie.jsonl"))
            self.assertEqual(code, 0, err)
            rows_t = read_jsonl(w.path("o_tie.jsonl"))
            hits_t = events(rows_t, "monster_hit")
            self.assertEqual(len(hits_t), 1)
            self.assertEqual(hits_t[0]["data"]["monster_id"], "M2")
            by_id = {m["id"]: m for m in snapshots(rows_t)[1]["monsters"]}
            self.assertEqual(by_id["M2"]["state"], "recoil")
            self.assertEqual(by_id["M10"]["state"], "chase")

    def test_recoil_60_ticks_coincident_plus_x_and_invuln_90_ticks(self):
        """AC-P2-11, AC-P2-12: trùng tâm lùi +x đúng 60 bước (2.0 m); bất tử 90 tick; ngạt xuyên bất tử."""
        with Workdir() as w:
            contract = _make_v11_contract(w)
            # Trùng tâm tại [60, 20]: hit ở tick 1 -> recoil_dir = [1, 0], không lùi ở tick 1, lùi 60 bước từ tick 2..61
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [60, 20]},
                "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [60, 20], "waypoints": [[60, 20], [64, 20]]}],
                "random_fish": False,
            }})
            code, err = _run_v11(contract, "--mode", "gather", "--seed", "1", "--ticks", "95",
                                 "--scenario", sc, "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            snaps = {s["tick"]: s for s in snapshots(rows)}
            # Tick 1: vừa hit, chưa lùi, recoil_dir = [1.0, 0.0], state_ticks_left = 60
            m1 = snaps[1]["monsters"][0]
            self.assertEqual(m1["pos"], [60.0, 20.0])
            self.assertEqual(m1["state"], "recoil")
            self.assertEqual(m1["state_ticks_left"], 60)
            self.assertEqual(m1["recoil_dir"], [1.0, 0.0])
            # Tick 60: bước recoil thứ 59, còn 1 tick
            self.assertEqual(snaps[60]["monsters"][0]["state"], "recoil")
            self.assertEqual(snaps[60]["monsters"][0]["state_ticks_left"], 1)
            # Tick 61: hoàn tất bước recoil thứ 60 (+2.0 m -> x=62.0), chuyển về patrol, recoil_dir=None
            m61 = snaps[61]["monsters"][0]
            self.assertTrue(close(m61["pos"][0], 62.0, 0.005), m61)
            self.assertEqual(m61["state"], "patrol")
            self.assertEqual(m61["state_ticks_left"], 0)
            self.assertIsNone(m61["recoil_dir"])
            # Trong suốt 90 tick bất tử (tick 2..90) không có hit thứ 2; hết bất tử ở tick 91 mới hit lại
            hits = events(rows, "monster_hit")
            self.assertEqual([h["tick"] for h in hits], [1, 91])

            # Ngạt xuyên bất tử và không rơi hàng
            sc_choke = write_json(w.path("sc_ch.json"), {"gather": {
                "player": {"pos": [60, 20], "hp": 3, "oxygen_ticks": 0, "zero_oxy_ticks": 59, "invuln_ticks": 50},
                "hold": ["ca_loc", "bong_sung"],
                "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [60, 20], "waypoints": [[60, 20], [64, 20]]}],
                "random_fish": False,
            }})
            code, err = _run_v11(contract, "--mode", "gather", "--seed", "1", "--ticks", "1",
                                 "--scenario", sc_choke, "--snapshot-every", "1", "--out", w.path("o_ch.jsonl"))
            self.assertEqual(code, 0, err)
            rows_c = read_jsonl(w.path("o_ch.jsonl"))
            self.assertEqual([e["name"] for e in events(rows_c)], ["choke"])
            self.assertEqual(events(rows_c, "monster_hit"), [])
            self.assertEqual(snapshots(rows_c)[1]["player"]["hp"], 2)
            self.assertEqual(snapshots(rows_c)[1]["hold"], ["ca_loc", "bong_sung"])
            self.assertEqual(snapshots(rows_c)[1]["monsters"][0]["state"], "chase")  # không recoil khi bất tử

    def test_monster_faint_clears_hold_empty_inventory_and_choke_before_hit(self):
        """AC-P2-13, AC-P2-14: Máu 0 do hit -> faint{cause:'monster', lost, hp:0} -> gather_end fainted, kho {}; ngạt trước hit."""
        with Workdir() as w:
            contract = _make_v11_contract(w)
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [60, 20], "hp": 1},
                "hold": ["ca_loc", "bong_sung", "ca_linh"],
                "fish": [{"id": "F1", "kind": "ca_loc", "pos": [60.5, 20]}],
                "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [60, 20], "waypoints": [[60, 20], [64, 20]]}],
            }})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "catch": True}))
            inv = w.path("inv.json")
            code, err = _run_v11(contract, "--mode", "gather", "--seed", "1", "--ticks", "5",
                                 "--scenario", sc, "--inputs", inp,
                                 "--inventory-out", inv, "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual([e["name"] for e in events(rows)], ["monster_hit", "faint", "gather_end"])
            self.assertEqual(events(rows, "monster_hit")[0]["data"], {
                "monster_id": "M1",
                "hp": 0,
                "lost": ["ca_linh"],
                "pos": [60.0, 20.0],
            })
            self.assertEqual(events(rows, "faint")[0]["data"], {
                "cause": "monster",
                "lost": ["bong_sung", "ca_loc"],
                "hp": 0,
            })
            self.assertEqual(events(rows, "gather_end")[0]["data"], {
                "reason": "fainted",
                "inventory": {"items": {}},
            })
            self.assertEqual(snapshots(rows)[-1]["hold"], [])
            self.assertEqual(len(snapshots(rows)[-1]["fish"]), 1)  # dừng bước sớm, không bắt cá
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {}})

            # Cùng tick vừa ngạt chết (hp 1->0) vừa trùng Cá Sấu -> ngạt trước, không phát monster_hit
            sc_both = write_json(w.path("sc_both.json"), {"gather": {
                "player": {"pos": [60, 20], "hp": 1, "oxygen_ticks": 0, "zero_oxy_ticks": 59},
                "hold": ["ca_loc"],
                "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [60, 20], "waypoints": [[60, 20], [64, 20]]}],
                "random_fish": False,
            }})
            code, err = _run_v11(contract, "--mode", "gather", "--seed", "1", "--ticks", "5",
                                 "--scenario", sc_both, "--out", w.path("o_both.jsonl"))
            self.assertEqual(code, 0, err)
            rows_b = read_jsonl(w.path("o_both.jsonl"))
            self.assertEqual([e["name"] for e in events(rows_b)], ["choke", "faint", "gather_end"])
            self.assertEqual(events(rows_b, "monster_hit"), [])


class GatherDayContextT246Tests(unittest.TestCase):
    def test_t246_day_context_direct_upgrades_and_m2_from_day_3(self):
        """T246: GatherSim nhận day và active_upgrades trực tiếp; M2 xuất hiện từ Ngày 3."""
        with Workdir() as w:
            contract_path = _make_v11_contract(w)
            with open(contract_path, encoding="utf-8") as f:
                tuning = json.load(f)["tuning"]

            # Mặc định (standalone): Ngày 1 -> chỉ M1, oxy 30s (1800), hp 3
            s1 = GatherSim(tuning, {}, Streams(1), IdAllocator())
            self.assertEqual([m["id"] for m in s1.snapshot()["monsters"]], ["M1"])
            self.assertEqual((s1.oxygen_max, s1.oxygen_ticks, s1.hp, s1.t["hp_max"]), (1800, 1800, 3, 3))

            # Ngày 2 với nâng cấp oxygen lv1 (45s=2700), hp lv1 (4): vẫn chỉ M1
            s2 = GatherSim(tuning, {}, Streams(1), IdAllocator(), day=2, active_upgrades={"oxygen": 1, "hp": 1})
            self.assertEqual([m["id"] for m in s2.snapshot()["monsters"]], ["M1"])
            self.assertEqual((s2.oxygen_max, s2.oxygen_ticks, s2.hp, s2.t["hp_max"]), (2700, 2700, 4, 4))

            # Ngày 3 với nâng cấp cấp 2 (oxy 60s=3600, hp 5): có cả M1 và M2
            s3 = GatherSim(tuning, {}, Streams(1), IdAllocator(), day=3, active_upgrades={"oxygen": 2, "hp": 2})
            self.assertEqual([m["id"] for m in s3.snapshot()["monsters"]], ["M1", "M2"])
            self.assertEqual((s3.oxygen_max, s3.oxygen_ticks, s3.hp, s3.t["hp_max"]), (3600, 3600, 5, 5))

    def test_t246_day_mode_m2_on_day_3_next_day_upgrades_and_determinism(self):
        """AC-P2-15, AC-P2-23, AC-P2-29: trong --mode day, M2 chỉ có từ Ngày 3; nâng cấp chỉ áp từ Ngày sau; tất định."""
        with Workdir() as w:
            contract = _make_v11_contract(w)
            sc = write_json(w.path("sc.json"), {
                "day": {"money": 500, "earned": 500},
                "gather": {"hold": ["ca_loc"], "random_fish": False},
                "quan": {"time_left_ticks": 1},
            })
            # Ngày 1: tick 0 cập bến -> tick 1 quán hết giờ -> tick 2 mua oxygen (200) -> tick 3 mua hp (250) -> tick 4 shop_done
            # Ngày 2: tick 5 cập bến -> tick 6 quán hết giờ -> tick 7 shop_done
            # Ngày 3: tick 8 đang ở gather Ngày 3 -> kiểm có M1 + M2 và nâng cấp đang hiệu lực
            inp = write_json(w.path("in.json"), frames(
                {"tick": 0, "interact": True},
                {"tick": 1, "interact": False},
                {"tick": 2, "buy": "oxygen"},
                {"tick": 3, "buy": "hp"},
                {"tick": 4, "shop_done": True},
                {"tick": 5, "shop_done": False, "interact": True},
                {"tick": 6, "interact": False},
                {"tick": 7, "shop_done": True},
                {"tick": 8, "shop_done": False},
            ))
            out1, out2 = w.path("d1.jsonl"), w.path("d2.jsonl")
            for out in (out1, out2):
                code, err = _run_v11(contract, "--mode", "day", "--days", "3", "--seed", "7", "--ticks", "10",
                                     "--scenario", sc, "--inputs", inp, "--snapshot-every", "1", "--out", out)
                self.assertEqual(code, 0, err)

            # Tất định từng byte
            with open(out1, "rb") as a, open(out2, "rb") as b:
                self.assertEqual(a.read(), b.read())

            snaps = {s["tick"]: s for s in snapshots(read_jsonl(out1))}
            # Ngày 1 gather (tick 0): chỉ M1, chưa có nâng cấp hiệu lực
            self.assertEqual([m["id"] for m in snaps[0]["monsters"]], ["M1"])
            self.assertEqual((snaps[0]["player"]["oxygen_max_ticks"], snaps[0]["player"]["hp_max"]), (1800, 3))
            # Ngày 1 Shop (tick 4, trước đóng shop): vừa mua oxygen+hp -> upgrades có, active_upgrades rỗng
            self.assertEqual(snaps[4]["upgrades"], {"hp": 1, "oxygen": 1})
            self.assertEqual(snaps[4]["active_upgrades"], {})
            # Ngày 2 gather (tick 5, đổi pha sang Ngày 2): nâng cấp bắt đầu có hiệu lực, vẫn chỉ M1
            self.assertEqual((snaps[5]["day"], snaps[5]["phase"]), (2, "gather"))
            self.assertEqual(snaps[5]["active_upgrades"], {"hp": 1, "oxygen": 1})
            self.assertEqual((snaps[5]["player"]["oxygen_max_ticks"], snaps[5]["player"]["hp_max"]), (2700, 4))
            self.assertEqual([m["id"] for m in snaps[5]["monsters"]], ["M1"])
            # Ngày 3 gather (tick 8, đổi pha sang Ngày 3): M2 xuất hiện cùng M1
            self.assertEqual((snaps[8]["day"], snaps[8]["phase"]), (3, "gather"))
            self.assertEqual([m["id"] for m in snaps[8]["monsters"]], ["M1", "M2"])
            self.assertEqual((snaps[8]["player"]["oxygen_max_ticks"], snaps[8]["player"]["hp_max"]), (2700, 4))

    def test_day_mode_monster_faint_opens_quan_with_empty_stock(self):
        """TICKET-02 §1.2 & §4.5: ngất do Cá Sấu trong --mode day vẫn mở Quán cùng tick với kho rỗng."""
        with Workdir() as w:
            contract = _make_v11_contract(w)
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {"pos": [60, 20], "hp": 1},
                    "hold": ["ca_loc", "bong_sung"],
                    "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [60, 20], "waypoints": [[60, 20], [64, 20]]}],
                    "random_fish": False,
                },
                "quan": {"time_left_ticks": 1},
            })
            code, err = _run_v11(contract, "--mode", "day", "--days", "1", "--seed", "1", "--ticks", "3",
                                 "--scenario", sc, "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            tick1_evs = [(e["name"], e["phase"]) for e in events(rows) if e["tick"] == 1]
            self.assertEqual(tick1_evs, [
                ("monster_hit", "gather"),
                ("faint", "gather"),
                ("gather_end", "gather"),
                ("phase_start", "quan"),
            ])
            snap1 = [s for s in snapshots(rows) if s["tick"] == 1][0]
            self.assertEqual((snap1["phase"], snap1["phase_tick"], snap1["stock"]), ("quan", 0, {}))


if __name__ == "__main__":
    unittest.main()
