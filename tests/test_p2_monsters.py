"""Test lát 2 Phase 2 (LeBao403): Cá Sấu Năm Chèo, Máu, bất tử, ngất do quái. Ticket-02 mục 1.2, 4.4, 4.5.
Kiểu hộp đen: chạy headless_cmd, đọc JSONL; số liệu đọc từ game.contract.json.

Chạy: PYTHONPATH=tests:. python3 -m unittest discover -s tests -p "test_p2_monsters.py" -v
"""

import json
import math
import unittest

from helpers import Workdir, close, events, frames, read_jsonl, run_headless, snapshots, write_json

with open("game.contract.json", encoding="utf-8") as _f:
    G = json.load(_f)["tuning"]["gather"]
MON = G["monsters"]
SAU = MON["species"]["ca_sau"]
THR = SAU["depths"][0]  # ngưỡng độ sâu của loài (10)


def mon(mid="M1", pos=(51, 20), waypoints=None, **kw):
    pos = list(pos)
    return {"id": mid, "kind": "ca_sau", "pos": pos,
            "waypoints": waypoints or [pos, [pos[0] + 4, pos[1]]], **kw}


def run(block, ticks, inputs=None, every=1, day_block=True):
    """Chạy gather (cá tắt) với scenario `block`; trả rows."""
    with Workdir() as w:
        sc = write_json(w.path("sc.json"), {"gather": {"random_fish": False, **block}})
        args = ["--mode", "gather", "--seed", "1", "--ticks", str(ticks), "--scenario", sc,
                "--snapshot-every", str(every), "--out", w.path("o.jsonl")]
        if inputs is not None:
            args += ["--inputs", write_json(w.path("in.json"), inputs)]
        code, err = run_headless(*args)
        assert code == 0, err
        return read_jsonl(w.path("o.jsonl"))


def snap(rows, tick):
    return {s["tick"]: s for s in snapshots(rows)}[tick]


def m_at(rows, tick, mid="M1"):
    return {m["id"]: m for m in snap(rows, tick)["monsters"]}[mid]


class Patrol(unittest.TestCase):
    def test_tuan_tra_qua_lai_hai_waypoint(self):
        """M1 mặc định [60,24] -> [64,24] ở 1 m/s: tới nơi ở tick 240, đổi đích, quay về."""
        rows = run({}, 300)  # người chơi ở bến (mặt nước), không bị phát hiện
        self.assertEqual(m_at(rows, 0)["target_idx"], 1)
        self.assertTrue(close(m_at(rows, 120)["pos"][0], 62, 0.01))
        m = m_at(rows, 240)
        self.assertEqual((m["pos"], m["target_idx"], m["state"]), ([64, 24], 0, "patrol"))
        self.assertTrue(close(m_at(rows, 300)["pos"][0], 63, 0.01))

    def test_nguoi_choi_nong_khong_bi_phat_hien(self):
        rows = run({"player": {"pos": [58, THR - 0.5]}}, 30)
        self.assertEqual(m_at(rows, 30)["state"], "patrol")
        self.assertEqual(events(rows, "monster_hit"), [])


class Chase(unittest.TestCase):
    def test_phat_hien_duoi_roi_can(self):
        """Người chơi đứng yên ở [55,20], cách M1 khoảng 6.4 m: chase ngay bước 1, đuổi 3 m/s rồi chạm."""
        rows = run({"player": {"pos": [55, 20]}}, 150)
        self.assertEqual(m_at(rows, 1)["state"], "chase")
        p0, p1 = m_at(rows, 0)["pos"], m_at(rows, 1)["pos"]
        self.assertTrue(close(math.dist(p0, p1), SAU["chase_speed"] / 60, 0.001))
        hits = events(rows, "monster_hit")
        self.assertEqual(len(hits), 1)
        d = math.dist([60, 24], [55, 20])
        self.assertTrue(abs(hits[0]["tick"] - math.ceil((d - SAU["hit_radius"]) / (SAU["chase_speed"] / 60))) <= 2)
        self.assertEqual(hits[0]["data"]["monster_id"], "M1")
        self.assertEqual(hits[0]["data"]["pos"], [55, 20])

    def test_thoi_duoi_khi_nguoi_choi_len_nong(self):
        rows = run({"player": {"pos": [50, 12], "vel": [0, -4]}, "monsters": [mon(pos=(50, 20))]}, 40,
                   inputs=frames({"tick": 0, "move": [0, -1]}))
        self.assertEqual(m_at(rows, 1)["state"], "chase")
        # người chơi lên d < 10 sau khoảng 30 tick -> quái về patrol
        last = snapshots(rows)[-1]
        self.assertLess(last["player"]["pos"][1], THR)
        self.assertEqual(m_at(rows, last["tick"])["state"], "patrol")

    def test_thoi_duoi_khi_xa_hon_exit_radius(self):
        rows = run({"player": {"pos": [10, 20]},
                    "monsters": [mon(pos=(30, 20), state="chase")]}, 1)
        self.assertEqual(m_at(rows, 1)["state"], "patrol")


class Hit(unittest.TestCase):
    HOLD = ["ca_loc", "bong_sung", "ca_linh", "keo_neo", "ca_keo"]

    def test_cham_mat_mau_rot_nua_gio_lifo_bat_tu_recoil(self):
        rows = run({"player": {"pos": [50, 20]}, "hold": self.HOLD, "monsters": [mon(pos=(51, 20))]}, 2)
        hits = events(rows, "monster_hit")
        self.assertEqual([h["tick"] for h in hits], [1])
        self.assertEqual(hits[0]["data"], {"monster_id": "M1", "hp": G["hp_max"] - 1,
                                           "lost": ["ca_keo", "keo_neo"], "pos": [50, 20]})
        s = snap(rows, 1)
        self.assertEqual(s["hold"], self.HOLD[:3])
        self.assertEqual(s["player"]["invuln_ticks"], MON["invuln_ticks"])
        m = m_at(rows, 1)
        self.assertEqual((m["state"], m["state_ticks_left"], m["recoil_dir"]), ("recoil", SAU["recoil_ticks"], [1, 0]))

    def test_recoil_60_buoc_lui_2m_roi_ve_patrol(self):
        rows = run({"player": {"pos": [50, 20]}, "monsters": [mon(pos=(51, 20), waypoints=[[51, 20], [51, 20]])]},
                   62)
        x1 = m_at(rows, 1)["pos"][0]  # vị trí lúc chạm (recoil bắt đầu từ bước sau)
        self.assertEqual(m_at(rows, 60)["state"], "recoil")
        m61 = m_at(rows, 61)
        self.assertEqual((m61["state"], m61["recoil_dir"]), ("patrol", None))
        self.assertTrue(close(m61["pos"][0] - x1, SAU["recoil_dist"], 0.001))
        self.assertEqual(len(events(rows, "monster_hit")), 1)

    def test_bat_tu_90_tick_moi_bi_cham_lai(self):
        """Hai con cạnh người chơi: một hit mỗi bước (con gần nhất); con kia đuổi theo nhưng chỉ chạm lại khi hết
        bất tử ở tick 1 + 90, và trong bất tử không bị đẩy sang recoil."""
        rows = run({"player": {"pos": [50, 20]},
                    "monsters": [mon("M1", (51, 20)), mon("M2", (50, 21.2), waypoints=[[50, 21.2], [50, 21.2]])]},
                   95)
        hits = events(rows, "monster_hit")
        self.assertEqual([(h["tick"], h["data"]["monster_id"]) for h in hits],
                         [(1, "M1"), (1 + MON["invuln_ticks"], "M2")])
        self.assertEqual(m_at(rows, 50, "M2")["state"], "chase")

    def test_mot_buoc_toi_da_mot_hit_chon_gan_nhat_hoa_id(self):
        rows = run({"player": {"pos": [50, 20]},
                    "monsters": [mon("M2", (51, 20)), mon("M1", (49, 20))]}, 1)
        hits = events(rows, "monster_hit")
        self.assertEqual([h["data"]["monster_id"] for h in hits], ["M1"])  # bằng khoảng cách -> id nhỏ

    def test_nguoi_choi_nong_khong_bi_cham(self):
        rows = run({"player": {"pos": [50, THR - 0.5]}, "monsters": [mon(pos=(50, THR))]}, 5)
        self.assertEqual(events(rows, "monster_hit"), [])

    def test_recoil_bi_chan_theo_dai_do_sau_loai(self):
        """Quái nằm trên người chơi, lùi thẳng lên: bị chặn ở d = depths[0]."""
        rows = run({"player": {"pos": [50, 11.5]}, "monsters": [mon(pos=(50, 10.5))]}, 70)
        self.assertEqual(m_at(rows, 1)["recoil_dir"], [0, -1])
        self.assertEqual(m_at(rows, 61)["pos"][1], THR)


class Faint(unittest.TestCase):
    def test_ngat_do_quai(self):
        rows = run({"player": {"pos": [50, 20], "hp": 1}, "hold": ["ca_loc", "bong_sung", "ca_linh"],
                    "monsters": [mon(pos=(51, 20))]}, 50)
        self.assertEqual([e["name"] for e in events(rows)], ["monster_hit", "faint", "gather_end"])
        self.assertEqual(events(rows, "monster_hit")[0]["data"]["lost"], ["ca_linh"])
        self.assertEqual(events(rows, "faint")[0]["data"], {"cause": "monster", "lost": ["bong_sung", "ca_loc"], "hp": 0})
        self.assertEqual(events(rows, "gather_end")[0]["data"], {"reason": "fainted", "inventory": {"items": {}}})
        self.assertEqual((rows[-1]["reason"], rows[-1]["ticks"]), ("fainted", 1))

    def test_ngat_xet_truoc_hit_cung_tick(self):
        """Cùng tick: ngạt trừ Máu trước, rồi hit làm Máu về 0 -> faint do quái."""
        rows = run({"player": {"pos": [50, 20], "hp": 2, "oxygen_ticks": 0, "zero_oxy_ticks": 59},
                    "monsters": [mon(pos=(51, 20))]}, 5)
        self.assertEqual([e["name"] for e in events(rows)], ["choke", "monster_hit", "faint", "gather_end"])
        self.assertEqual(events(rows, "faint")[0]["data"]["cause"], "monster")

    def test_ngat_xuyen_bat_tu_va_khong_rot_hang(self):
        rows = run({"player": {"pos": [20, 20], "invuln_ticks": 80, "oxygen_ticks": 0, "zero_oxy_ticks": 59},
                    "hold": ["ca_loc"], "monsters": []}, 1)
        self.assertEqual([(e["name"], e["data"]) for e in events(rows)], [("choke", {"hp": G["hp_max"] - 1})])
        self.assertEqual(snap(rows, 1)["hold"], ["ca_loc"])


class Determinism(unittest.TestCase):
    def test_tat_dinh_tung_byte_voi_quai(self):
        outs = []
        for _ in range(2):
            with Workdir() as w:
                inp = write_json(w.path("in.json"), frames({"tick": 0, "move": [1, 1]}, {"tick": 600, "move": [0, 0]}))
                code, err = run_headless("--mode", "gather", "--seed", "3", "--ticks", "1200", "--inputs", inp,
                                         "--snapshot-every", "7", "--out", w.path("o.jsonl"))
                self.assertEqual(code, 0, err)
                with open(w.path("o.jsonl"), "rb") as f:
                    outs.append(f.read())
        self.assertEqual(outs[0], outs[1])


if __name__ == "__main__":
    unittest.main()
