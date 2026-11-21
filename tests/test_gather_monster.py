"""Test Cá Sấu Năm Chèo + Máu/ngất do quái (hộp đen qua headless_cmd) — PRD v1.1 mục 1.2, D, E, 4.5.

Preset (tuning.monsters): patrol 1.0 m/s, chase 3.0 m/s, detect ≤ 10 m, exit > 16 m,
depths ca_sau [10,30], hit_radius 1.5, recoil 60 bước × recoil_dist/60 m, invuln 90,
loss_ratio 0.5. M1 [60,24]↔[64,24] từ Ngày 1; M2 (from_day 3) KHÔNG có ở gather độc lập.

Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_gather_monster -v
"""

import json
import unittest

from helpers import (Workdir, close, events, read_jsonl, run_headless,
                     snapshots, write_json)
from helpers import counts, items, kinds  # v1.2 kho cá thể


def contract_tuning():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]["gather"]


def sc(block):
    return {"gather": block}


class Patrol(unittest.TestCase):
    def test_bo_tri_ngay_1_chi_co_M1(self):
        """Gather độc lập dùng bố trí Ngày 1: chỉ M1 (M2 from_day 3 bị loại)."""
        with Workdir() as w:
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "0",
                                     "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            ms = snapshots(read_jsonl(w.path("o.jsonl")))[0]["monsters"]
            self.assertEqual([m["id"] for m in ms], ["M1"], ms)
            self.assertEqual(ms[0]["state"], "patrol")
            self.assertEqual(ms[0]["target_idx"], 1)
            self.assertEqual(ms[0]["waypoints"], [[60, 24], [64, 24]])

    def test_patrol_den_waypoint_roi_dao_muc_tieu(self):
        """1 m/s tới [64,24]: đến đúng tick 240 (4 m), snap waypoint, đổi target cho bước sau."""
        with Workdir() as w:
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "241",
                                     "--scenario", write_json(w.path("sc.json"), sc({
                                         "player": {"pos": [10, 0]}})),
                                     "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            s = {r["tick"]: r for r in snapshots(read_jsonl(w.path("o.jsonl")))}
            m240 = s[240]["monsters"][0]
            self.assertEqual(m240["pos"], [64, 24], m240)
            self.assertEqual(m240["target_idx"], 0, "đến waypoint thì đổi mục tiêu cho bước sau")
            m241 = s[241]["monsters"][0]
            self.assertTrue(close(m241["pos"][0], 64 - 1 / 60, 2e-3), m241)
            self.assertEqual(m241["target_idx"], 0)


class Chase(unittest.TestCase):
    def test_chase_3ms_khi_nguoi_choi_o_vung_sau(self):
        """Người chơi d ≥ 10 và cách ≤ 10 m: chuyển chase, bơi 3.0 m/s về phía người chơi."""
        with Workdir() as w:
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", write_json(w.path("sc.json"), sc({
                                         "player": {"pos": [66, 20]}})),
                                     "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            s = {r["tick"]: r for r in snapshots(read_jsonl(w.path("o.jsonl")))}
            m0, m1 = s[0]["monsters"][0]["pos"], s[1]["monsters"][0]["pos"]
            self.assertEqual(s[1]["monsters"][0]["state"], "chase", s[1]["monsters"])
            # JSONL làm tròn 3 chữ số thập phân -> dung sai 2e-3
            self.assertTrue(close(((m1[0] - m0[0]) ** 2 + (m1[1] - m0[1]) ** 2) ** 0.5, 0.05, 2e-3),
                            "di chuyển đúng chase_speed/60 mỗi bước")
            # quái ở d=24 bơi LÊN về phía người chơi d=20: d giảm 0.05 × 4/7.211
            self.assertTrue(close(m1[1], 24 - 0.05 * (4 / 7.211), 2e-3), m1)

    def test_noi_qua_khong_chase_va_khong_hit(self):
        """Người chơi d < 10 (vùng nông): quái không chase, không hit dù trong hit_radius."""
        with Workdir() as w:
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", write_json(w.path("sc.json"), sc({
                                         "player": {"pos": [60, 9.9]},
                                         "monsters": [{"id": "M9", "kind": "ca_sau",
                                                       "pos": [60, 10.4],
                                                       "waypoints": [[60, 10.4], [64, 24]]}]})),
                                     "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(events(rows, "monster_hit"), [], "d < 10 thì không bị chạm")
            last = snapshots(rows)[-1]
            self.assertEqual(last["player"]["hp"], 3)
            self.assertEqual(last["monsters"][0]["state"], "patrol", last["monsters"])


class Hit(unittest.TestCase):
    def test_hit_mat_1_mau_bo_nua_gio_bat_tu_90_recoil(self):
        """Chạm: -1 Máu, bỏ floor(giỏ × 0.5) theo LIFO, bất tử 90, quái recoil 60 bước
        lùi theo hướng xa người chơi chốt lúc chạm."""
        with Workdir() as w:
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", write_json(w.path("sc.json"), sc({
                                         "player": {"pos": [61, 24]},
                                         "hold": items(*["ca_loc", "bong_sung", "ca_linh", "ca_keo", "keo_neo"])})),
                                     "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            hit = events(rows, "monster_hit")
            self.assertEqual(len(hit), 1, hit)
            self.assertEqual(hit[0]["tick"], 1)
            # quái đã patrol 1/60 về phía [64,24] trước khi xét chạm -> cách 0.9833 m
            self.assertEqual(hit[0]["data"]["monster_id"], "M1")
            self.assertEqual(hit[0]["data"]["hp"], 2)
            self.assertEqual(kinds(hit[0]["data"]["lost"]), ["keo_neo", "ca_keo"],
                             "bỏ floor(5×0.5)=2 theo LIFO (nhặt sau mất trước)")
            self.assertEqual(hit[0]["data"]["pos"], [61, 24], "pos là vị trí người chơi")
            s = snapshots(rows)[-1]
            self.assertEqual(s["player"]["hp"], 2)
            self.assertEqual(s["player"]["invuln_ticks"], 90, "đặt bất tử 90 tick")
            self.assertEqual(kinds(s["hold"]), ["ca_loc", "bong_sung", "ca_linh"])
            m = s["monsters"][0]
            self.assertEqual(m["state"], "recoil")
            self.assertEqual(m["state_ticks_left"], 60, "recoil 60 bước tính từ bước sau")
            self.assertTrue(close(m["recoil_dir"][0], -1.0, 1e-9), m["recoil_dir"])
            self.assertTrue(close(m["recoil_dir"][1], 0.0, 1e-9))

    def test_dang_bat_tu_khong_hit_khong_recoil(self):
        """Còn bất tử: không monster_hit, quái không chuyển recoil, Máu giữ nguyên."""
        with Workdir() as w:
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", write_json(w.path("sc.json"), sc({
                                         "player": {"pos": [61, 24], "invuln_ticks": 10}})),
                                     "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(events(rows, "monster_hit"), [])
            s = snapshots(rows)[-1]
            self.assertEqual(s["player"]["hp"], 3)
            self.assertEqual(s["player"]["invuln_ticks"], 9, "giảm bất tử mỗi bước")
            # bất tử chỉ chặn hit/recoil; phát hiện vẫn chạy nên quái đã chase
            self.assertEqual(s["monsters"][0]["state"], "chase")

    def test_recoil_60_buoc_khong_hit_roi_ve_patrol(self):
        """Trong 60 bước recoil không gây hit; hết recoil về patrol, chạm xét từ bước kế."""
        with Workdir() as w:
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "65",
                                     "--scenario", write_json(w.path("sc.json"), sc({
                                         "player": {"pos": [61, 24]}})),
                                     "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(len(events(rows, "monster_hit")), 1, "trong 65 bước chỉ hit đúng 1 lần")
            s = {r["tick"]: r for r in snapshots(rows)}
            m61 = s[61]["monsters"][0]
            self.assertEqual(m61["state"], "patrol", "hết recoil đúng tick 61")
            self.assertEqual(m61["state_ticks_left"], 0)
            self.assertEqual(m61["recoil_dir"], None)
            # bước 1 quái đã chase 3/60 m về phía người chơi rồi mới chạm; JSONL làm tròn 3 số
            self.assertTrue(close(m61["pos"][0], 60 + 3 / 60 - 2.0, 2e-3),
                            "lùi 60 bước × 2/60 m = 2 m theo hướng xa người chơi")
            self.assertEqual(s[62]["monsters"][0]["state"], "chase",
                             "phát hiện xét từ bước kế -> tick 62 đã đuổi lại")

    def test_hai_quai_hit_con_gan_nhat(self):
        """Hai con cùng trong hit_radius: chỉ 1 hit cho con GẦN nhất; con kia giữ trạng thái."""
        with Workdir() as w:
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", write_json(w.path("sc.json"), sc({
                                         "player": {"pos": [61, 24]},
                                         "monsters": [
                                             {"id": "M1", "kind": "ca_sau", "pos": [62, 24],
                                              "waypoints": [[60, 24], [64, 24]]},
                                             {"id": "M2", "kind": "ca_sau", "pos": [61.5, 24],
                                              "waypoints": [[60, 24], [64, 24]]}]})),
                                     "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            hit = events(rows, "monster_hit")
            self.assertEqual(len(hit), 1, hit)
            self.assertEqual(hit[0]["data"]["monster_id"], "M2", "chọn con gần nhất")
            by_id = {m["id"]: m for m in snapshots(rows)[-1]["monsters"]}
            self.assertEqual(by_id["M2"]["state"], "recoil")
            self.assertEqual(by_id["M1"]["state"], "chase", "con không gây hit giữ nguyên")

    def test_hp_0_ngat_ngay_kho_rong_van_mo_quan(self):
        """Máu chạm 0: monster_hit -> faint cause monster (phần giỏ còn lại) -> gather_end
        kho rỗng ngay trong bước; file kho vẫn ghi rỗng cho buổi tối."""
        with Workdir() as w:
            inv = w.path("inv.json")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "5",
                                     "--scenario", write_json(w.path("sc.json"), sc({
                                         "player": {"pos": [61, 24], "hp": 1},
                                         "hold": items(*["ca_loc", "bong_sung", "ca_linh"])})),
                                     "--inventory-out", inv, "--snapshot-every", "1",
                                     "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            hit = events(rows, "monster_hit")[0]
            self.assertEqual(hit["data"]["hp"], 0)
            self.assertEqual(kinds(hit["data"]["lost"]), ["ca_linh"], "bỏ floor(3×0.5)=1 trước")
            faint = events(rows, "faint")
            self.assertEqual(len(faint), 1, faint)
            self.assertEqual(kinds(faint[0]["data"]["lost"]), ["bong_sung", "ca_loc"],
                             "faint mất phần giỏ còn lại theo LIFO")
            self.assertEqual([faint[0]["data"]["cause"], faint[0]["data"]["hp"]], ["monster", 0])
            ends = events(rows, "gather_end")
            self.assertEqual(len(ends), 1)
            self.assertEqual(ends[0]["tick"], 1, "ngất ngay trong bước bị chạm")
            self.assertEqual(ends[0]["data"], {"reason": "fainted", "inventory": {"items": []}})
            self.assertEqual(rows[-1]["reason"], "fainted")
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": []})


if __name__ == "__main__":
    unittest.main()
