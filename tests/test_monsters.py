"""Test hộp đen cho Cá Sấu (ticket 03 Phase 2): patrol, chase, hit, recoil, ngất."""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class Base(unittest.TestCase):
    def run_gather(self, w, scenario=None, inputs=None, ticks=30, every="1", name="o"):
        args = ["--mode", "gather", "--seed", "1", "--ticks", str(ticks),
                "--snapshot-every", every, "--out", w.path(name + ".jsonl")]
        if scenario is not None:
            args += ["--scenario", write_json(w.path("sc.json"), scenario)]
        if inputs is not None:
            args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
        code, err = run_headless(*args)
        self.assertEqual(code, 0, err)
        return read_jsonl(w.path(name + ".jsonl"))

    def snaps(self, rows):
        return {r["tick"]: r for r in snapshots(rows)}

    def m1(self, rows, tick):
        return [m for m in self.snaps(rows)[tick]["monsters"] if m["id"] == "M1"][0]


class Patrol(Base):
    def test_patrol_1m_s_va_doi_muc_tieu(self):
        """M1 đi 1.0 m/s từ [60,24] tới [64,24]: sau 60 tick ở 61.0; chạm nơi thì đổi waypoint."""
        with Workdir() as w:
            rows = self.run_gather(w, {"gather": {"player": {"pos": [20, 0]}}}, ticks=420, every="60")
            self.assertAlmostEqual(self.m1(rows, 60)["pos"][0], 61.0, places=2)
            self.assertAlmostEqual(self.m1(rows, 240)["pos"][0], 64.0, places=2)
            # chạm [64,24] rồi quay lại [60,24]
            self.assertLess(abs(self.m1(rows, 420)["pos"][0] - 61.0), 0.1)
            self.assertEqual(self.m1(rows, 420)["state"], "patrol")

    def test_chi_co_m1_ngay_1(self):
        with Workdir() as w:
            rows = self.run_gather(w, {"gather": {"player": {"pos": [20, 0]}}}, ticks=1)
            self.assertEqual([m["id"] for m in self.snaps(rows)[1]["monsters"]], ["M1"])


class Chase(Base):
    def test_chase_khi_nguoi_choi_xuong_sau_va_gan(self):
        """Người chơi ở d=20 cách 4.5 m: M1 chuyển chase và bơi nhanh hơn patrol."""
        with Workdir() as w:
            rows = self.run_gather(w, {"gather": {"player": {"pos": [62, 20]}}}, ticks=60, every="1")
            self.assertEqual(self.m1(rows, 1)["state"], "chase")
            self.assertGreater(self.m1(rows, 60)["pos"][0], 61.2)  # 3 m/s, đi chéo về phía người chơi

    def test_ve_patrol_khi_nguoi_choi_len_mat_nuoc(self):
        with Workdir() as w:
            rows = self.run_gather(w, {"gather": {"player": {"pos": [62, 20]}}}, ticks=90, every="1")
            self.assertEqual(self.m1(rows, 1)["state"], "chase")
            rows2 = self.run_gather(w, {"gather": {"player": {"pos": [62, 0]}}}, ticks=2, every="1", name="b")
            self.assertEqual(self.m1(rows2, 2)["state"], "patrol")


class Hit(Base):
    def test_hit_mat_mau_roi_nua_gio_va_bat_tu(self):
        """Đứng cùng chỗ với M1: mất 1 Máu, rơi floor(3/2)=1 món cuối, bất tử 90 tick."""
        sc = {"gather": {"player": {"pos": [60, 24]}, "hold": ["ca_loc", "bong_sung", "ca_linh"]}}
        with Workdir() as w:
            rows = self.run_gather(w, sc, ticks=3, every="1")
            hit = events(rows, "monster_hit")
            self.assertEqual(len(hit), 1, [(e["tick"], e["name"]) for e in events(rows)])
            data = hit[0]["data"]
            self.assertEqual(data["monster_id"], "M1")
            self.assertEqual(data["hp"], 2)
            self.assertEqual(data["lost"], ["ca_linh"])          # LIFO: món nhặt sau cùng
            snap = self.snaps(rows)[3]
            self.assertEqual(snap["player"]["hp"], 2)
            self.assertEqual(snap["player"]["invuln_ticks"], 88)  # 90 - 2 bước
            self.assertEqual(snap["hold"], ["ca_loc", "bong_sung"])

    def test_bat_tu_khong_bi_hit_lan_hai(self):
        """Sau hit đầu, đứng yên trong 90 tick: chỉ có một monster_hit."""
        sc = {"gather": {"player": {"pos": [60, 24]}}}
        with Workdir() as w:
            rows = self.run_gather(w, sc, ticks=90, every="10")
            self.assertEqual(len(events(rows, "monster_hit")), 1)

    def test_recoil_lui_ra_va_khong_hit(self):
        """Sau khi cắn, M1 vào recoil và lùi xa dần (hướng xa người chơi đã chốt)."""
        sc = {"gather": {"player": {"pos": [60, 24]}}}
        with Workdir() as w:
            rows = self.run_gather(w, sc, ticks=10, every="1")
            self.assertEqual(self.m1(rows, 1)["state"], "recoil")
            start = self.m1(rows, 2)["pos"][0]          # recoil bắt đầu từ bước sau
            self.assertGreater(start, 60.0)             # người chơi ở tâm ⇒ lùi +x
            self.assertGreater(self.m1(rows, 10)["pos"][0], start)

    def test_khong_hit_khi_nguoi_choi_o_mat_nuoc(self):
        with Workdir() as w:
            rows = self.run_gather(w, {"gather": {"player": {"pos": [60, 0]}}}, ticks=30)
            self.assertEqual(events(rows, "monster_hit"), [])


class Faint(Base):
    def test_ngat_do_quai_kho_rong_va_gather_end(self):
        sc = {"gather": {"player": {"pos": [60, 24], "hp": 1},
                         "hold": ["ca_loc", "bong_sung"]}}
        with Workdir() as w:
            inv = w.path("inv.json")
            args = ["--mode", "gather", "--seed", "1", "--ticks", "30", "--scenario",
                    write_json(w.path("sc.json"), sc), "--snapshot-every", "1",
                    "--out", w.path("o.jsonl"), "--inventory-out", inv]
            code, err = run_headless(*args)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            faint = events(rows, "faint")
            self.assertEqual(len(faint), 1)
            self.assertEqual(faint[0]["data"]["cause"], "monster")
            self.assertEqual(faint[0]["data"]["hp"], 0)
            end = events(rows, "gather_end")[0]
            self.assertEqual(end["data"]["reason"], "fainted")
            self.assertEqual(end["data"]["inventory"]["items"], {})
            self.assertEqual(snapshots(rows)[-1]["hold"], [])
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {}})


class ScenarioOverride(Base):
    def test_scenario_thay_danh_sach_quai(self):
        sc = {"gather": {"random_fish": False, "monsters": [
            {"id": "M9", "kind": "ca_sau", "pos": [30, 20], "waypoints": [[30, 20], [34, 20]]}]}}
        with Workdir() as w:
            rows = self.run_gather(w, sc, ticks=1)
            self.assertEqual([m["id"] for m in self.snaps(rows)[1]["monsters"]], ["M9"])


if __name__ == "__main__":
    unittest.main()
