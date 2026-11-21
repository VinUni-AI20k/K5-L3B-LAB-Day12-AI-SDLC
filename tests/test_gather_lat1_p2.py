"""Lát 1 Phase 2 (AC-P2-03): Cá Sấu Năm Chèo — patrol / chase / hit / recoil, Máu và ngất do quái.

Đối chiếu docs/prd/phase-2.md mục 1.2 và 4.5. Test HỘP ĐEN qua headless_cmd; Cá Sấu dựng bằng scenario.monsters.
"""

import json
import unittest

from helpers import Workdir, close, events, frames, read_jsonl, run_headless, snapshots, write_json
from legacy_v11 import setUpModule, tearDownModule  # noqa: F401  v1.2: fixture kho đếm chạy trên manifest v1.1 tạm, xem tests/legacy_v11.py

with open("game.contract.json", encoding="utf-8") as _f:
    G = json.load(_f)["tuning"]["gather"]
SP = G["monsters"]["species"]["ca_sau"]


def croc(mid="M1", pos=(60, 24), wps=((60, 24), (64, 24)), **kw):
    m = {"id": mid, "kind": "ca_sau", "pos": list(pos), "waypoints": [list(w) for w in wps]}
    m.update(kw)
    return m


def run(w, block, ticks, inputs=None, every=1, inv=None, out="o.jsonl"):
    block = dict({"random_fish": False}, **block)
    args = ["--mode", "gather", "--seed", "1", "--ticks", str(ticks), "--snapshot-every", str(every),
            "--scenario", write_json(w.path("sc.json"), {"gather": block}), "--out", w.path(out)]
    if inputs:
        args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
    if inv:
        args += ["--inventory-out", inv]
    code, err = run_headless(*args)
    assert code == 0, err
    return read_jsonl(w.path(out))


def snaps(rows):
    return {r["tick"]: r for r in snapshots(rows)}


class Patrol(unittest.TestCase):
    def test_patrol_1ms_toi_waypoint_roi_doi_muc_tieu(self):
        with Workdir() as w:
            rows = run(w, {"monsters": [croc()]}, 300, every=60)
        s = snaps(rows)
        m = lambda k: s[k]["monsters"][0]
        self.assertTrue(close(m(60)["pos"][0], 61, 0.01), m(60))
        self.assertEqual((m(60)["state"], m(60)["target_idx"]), ("patrol", 1))
        self.assertEqual((m(240)["pos"], m(240)["target_idx"]), ([64, 24], 0), "tới waypoint thì đổi mục tiêu")
        self.assertTrue(close(m(300)["pos"][0], 63, 0.01), m(300))
        self.assertEqual(events(rows, "monster_hit"), [])

    def test_mac_dinh_ngay_1_tuan_tra_m1(self):
        with Workdir() as w:
            rows = run(w, {}, 60, every=60)
        self.assertEqual([(m["id"], m["state"]) for m in snaps(rows)[60]["monsters"]], [("M1", "patrol")])


class Chase(unittest.TestCase):
    def test_phat_hien_trong_10m_khi_d_ge_10_thi_chase_3ms(self):
        with Workdir() as w:
            rows = run(w, {"player": {"pos": [50, 20]}, "monsters": [croc(pos=(56, 20), wps=((56, 20), (60, 20)))]},
                       10, every=1)
        s = snaps(rows)
        self.assertEqual(s[1]["monsters"][0]["state"], "chase")
        self.assertTrue(close(s[10]["monsters"][0]["pos"][0], 56 - 10 * SP["chase_speed"] / 60, 0.001))

    def test_nguoi_choi_nong_hon_10m_khong_chase_khong_hit(self):
        with Workdir() as w:
            rows = run(w, {"player": {"pos": [50, 9]}, "monsters": [croc(pos=(50.5, 10), wps=((50.5, 10), (54, 10)))]},
                       30)
        self.assertEqual(events(rows, "monster_hit"), [])
        self.assertTrue(all(s["monsters"][0]["state"] == "patrol" for s in snapshots(rows)))

    def test_roi_chase_khi_xa_hon_16m(self):
        # Người chơi bơi ngang ra xa 4 m/s, sấu đuổi 3 m/s: khoảng cách tăng 1 m/s, quá 16 m thì về patrol.
        with Workdir() as w:
            rows = run(w, {"player": {"pos": [20, 20], "vel": [4, 0]},
                           "monsters": [croc(pos=(11, 20), wps=((11, 20), (15, 20)))]},
                       600, inputs=[{"tick": 0, "move": [1, 0]}], every=30)
        states = [(k, r["monsters"][0]["state"]) for k, r in sorted(snaps(rows).items())]
        self.assertEqual(states[1][1], "chase")
        self.assertEqual(states[-1][1], "patrol")


class Hit(unittest.TestCase):
    def test_cham_mat_mau_rot_nua_gio_lifo_bat_tu_va_recoil(self):
        hold = ["ca_loc", "bong_sung", "ca_linh", "keo_neo", "ca_keo"]
        with Workdir() as w:
            rows = run(w, {"player": {"pos": [50, 20]}, "hold": hold,
                           "monsters": [croc(pos=(51, 20), wps=((51, 20), (55, 20)))]}, 61)
        hits = events(rows, "monster_hit")
        self.assertEqual([h["tick"] for h in hits], [1])
        self.assertEqual(hits[0]["data"], {"monster_id": "M1", "hp": G["hp_max"] - 1,
                                           "lost": ["ca_keo", "keo_neo"], "pos": [50, 20]})
        s = snaps(rows)
        self.assertEqual(s[1]["hold"], ["ca_loc", "bong_sung", "ca_linh"])
        self.assertEqual(s[1]["player"]["invuln_ticks"], G["monsters"]["invuln_ticks"])
        m1 = s[1]["monsters"][0]
        self.assertEqual((m1["state"], m1["state_ticks_left"], m1["recoil_dir"]), ("recoil", SP["recoil_ticks"], [1, 0]))
        # recoil 60 bước từ bước sau, mỗi bước 2/60 m: tổng 2 m theo hướng xa người chơi, rồi về patrol
        m61 = s[61]["monsters"][0]
        self.assertTrue(close(m61["pos"][0], 50.95 + SP["recoil_dist"], 0.001), m61)
        self.assertEqual((m61["state"], m61["recoil_dir"]), ("patrol", None))
        self.assertEqual(s[60]["monsters"][0]["state"], "recoil")

    def test_bat_tu_khong_hit_va_hit_lai_sau_khi_het(self):
        with Workdir() as w:
            rows = run(w, {"player": {"pos": [50, 20]}, "monsters": [croc(pos=(51, 20), wps=((51, 20), (55, 20)))]},
                       200, every=50)
        ticks = [h["tick"] for h in events(rows, "monster_hit")]
        self.assertEqual(ticks[0], 1)
        self.assertGreaterEqual(ticks[1], 1 + G["monsters"]["invuln_ticks"], "không hit lại khi còn bất tử")

    def test_invuln_tu_scenario_chan_hit_toi_khi_het(self):
        with Workdir() as w:
            rows = run(w, {"player": {"pos": [50, 20], "invuln_ticks": 5},
                           "monsters": [croc(pos=(51, 20), wps=((51, 20), (55, 20)))]}, 10)
        self.assertEqual([h["tick"] for h in events(rows, "monster_hit")], [5])

    def test_trung_tam_thi_recoil_theo_x_duong(self):
        with Workdir() as w:
            rows = run(w, {"player": {"pos": [50, 20]}, "monsters": [croc(pos=(50, 20), wps=((50, 20), (54, 20)))]}, 2)
        self.assertEqual(snaps(rows)[1]["monsters"][0]["recoil_dir"], [1, 0])
        self.assertTrue(close(snaps(rows)[2]["monsters"][0]["pos"][0], 50 + SP["recoil_dist"] / SP["recoil_ticks"], 1e-3))

    def test_moi_buoc_toi_da_mot_hit_con_gan_nhat_hoa_theo_id(self):
        with Workdir() as w:
            rows = run(w, {"player": {"pos": [50, 20]},
                           "monsters": [croc("M2", pos=(49, 20), wps=((49, 20), (45, 20))),
                                        croc("M1", pos=(51, 20), wps=((51, 20), (55, 20)))]}, 3)
        hits = events(rows, "monster_hit")
        self.assertEqual([(h["tick"], h["data"]["monster_id"]) for h in hits], [(1, "M1")])
        st = {m["id"]: m["state"] for m in snaps(rows)[1]["monsters"]}
        self.assertEqual(st, {"M1": "recoil", "M2": "chase"}, "con không gây hit không vào recoil")

    def test_ngat_xuyen_bat_tu_va_khong_rot_hang(self):
        with Workdir() as w:
            rows = run(w, {"player": {"pos": [50, 20], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "invuln_ticks": 50},
                           "hold": ["ca_loc", "ca_linh"]}, 1)
        self.assertEqual(events(rows, "choke")[0]["data"], {"hp": G["hp_max"] - 1})
        self.assertEqual(snaps(rows)[1]["hold"], ["ca_loc", "ca_linh"])


class Faint(unittest.TestCase):
    def test_het_mau_do_ca_sau_faint_monster_kho_rong(self):
        with Workdir() as w:
            inv = w.path("kho.json")
            rows = run(w, {"player": {"pos": [50, 20], "hp": 1}, "hold": ["ca_loc", "bong_sung", "ca_linh"],
                           "monsters": [croc(pos=(51, 20), wps=((51, 20), (55, 20)))]}, 50, inv=inv)
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {}})
        names = [(e["tick"], e["name"]) for e in events(rows) if e["name"] in ("monster_hit", "faint", "gather_end")]
        self.assertEqual(names, [(1, "monster_hit"), (1, "faint"), (1, "gather_end")])
        self.assertEqual(events(rows, "monster_hit")[0]["data"]["lost"], ["ca_linh"])
        self.assertEqual(events(rows, "faint")[0]["data"], {"cause": "monster", "lost": ["bong_sung", "ca_loc"], "hp": 0})
        self.assertEqual(events(rows, "gather_end")[0]["data"], {"reason": "fainted", "inventory": {"items": {}}})
        self.assertEqual(rows[-1]["reason"], "fainted")

    def test_ngat_cung_tick_di_truoc_hit(self):
        # Máu 2: ngạt (-1) rồi bị cắn (-1) cùng tick -> faint do monster, choke đứng trước.
        with Workdir() as w:
            rows = run(w, {"player": {"pos": [50, 20], "hp": 2, "oxygen_ticks": 0, "zero_oxy_ticks": 59},
                           "monsters": [croc(pos=(51, 20), wps=((51, 20), (55, 20)))]}, 3)
        names = [e["name"] for e in events(rows) if e["name"] in ("choke", "monster_hit", "faint")]
        self.assertEqual(names, ["choke", "monster_hit", "faint"])
        self.assertEqual(events(rows, "faint")[0]["data"]["cause"], "monster")

    def test_tat_dinh(self):
        block = {"player": {"pos": [40, 20]}, "hold": ["ca_loc", "ca_linh", "bong_sung"],
                 "monsters": [croc(pos=(46, 22), wps=((46, 22), (50, 22)))]}
        with Workdir() as w:
            run(w, block, 900, inputs=[{"tick": 0, "move": [0.3, 0.2]}, {"tick": 300, "move": [-1, 0]}], every=7,
                out="a.jsonl")
            run(w, block, 900, inputs=[{"tick": 0, "move": [0.3, 0.2]}, {"tick": 300, "move": [-1, 0]}], every=7,
                out="b.jsonl")
            with open(w.path("a.jsonl"), "rb") as a, open(w.path("b.jsonl"), "rb") as b:
                self.assertEqual(a.read(), b.read())


if __name__ == "__main__":
    unittest.main()
