"""Test hộp đen cho luật `gather` Phase 1 (ticket 07).

Chỉ chạy `headless_cmd` + đọc JSONL/file kho — không import module nội bộ.
Mỗi test đỏ vì ĐÚNG lý do: luật chưa có, không phải fixture sai.

Nguồn: PRD-0 §E/§F + docs/plan/phase-1-conformance.md §6.
"""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

TICK = 60


def tuning():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]["gather"]


class Base(unittest.TestCase):
    def run_gather(self, w, scenario=None, inputs=None, ticks=30, every="1", name="o"):
        args = ["--mode", "gather", "--seed", "1", "--ticks", str(ticks),
                "--snapshot-every", every, "--out", w.path(name + ".jsonl")]
        if scenario is not None:
            # Hồi quy luật P1: fixture bắt cá giữ vị trí cũ; cá bơi có test P2 riêng.
            scenario = {**scenario, "gather": {"random_fish": False, **scenario.get("gather", {})}}
            args += ["--scenario", write_json(w.path("sc.json"), scenario)]
        if inputs is not None:
            args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
        code, err = run_headless(*args)
        self.assertEqual(code, 0, err)
        return read_jsonl(w.path(name + ".jsonl"))

    def snaps(self, rows):
        return {r["tick"]: r for r in snapshots(rows)}


class Oxygen(Base):
    def test_oxy_mat_nuoc_khong_giam(self):
        """Ở d = 0 suốt 10 giây: oxy giữ nguyên tối đa."""
        with Workdir() as w:
            rows = self.run_gather(w, {"gather": {"player": {"pos": [20, 0]}}}, ticks=600)
            s = self.snaps(rows)
            self.assertEqual(s[600]["player"]["oxygen_ticks"], s[0]["player"]["oxygen_max_ticks"])
            self.assertEqual(events(rows, "oxygen_empty"), [])

    def test_oxy_duoi_nuoc_ve_0_dung_tick_1800(self):
        """Ở d = 10: mỗi tick -1, chạm 0 ở tick 1800 và phát oxygen_empty."""
        with Workdir() as w:
            rows = self.run_gather(w, {"gather": {"player": {"pos": [50, 10]}}}, ticks=1800, every="300")
            s = self.snaps(rows)
            self.assertEqual(s[0]["player"]["oxygen_ticks"], 1800)
            self.assertEqual(s[1800]["player"]["oxygen_ticks"], 0)
            ev = events(rows, "oxygen_empty")
            self.assertEqual(len(ev), 1, [e["name"] for e in events(rows)])
            self.assertEqual(ev[0]["tick"], 1800)


class Choke(Base):
    def test_choke_lan_dau_o_t_plus_59(self):
        """Oxy chạm 0 ở tick 1800 ⇒ ngạt lần đầu ở 1859, không phải 1860."""
        with Workdir() as w:
            rows = self.run_gather(w, {"gather": {"player": {"pos": [50, 10]}}}, ticks=1900, every="300")
            choke = events(rows, "choke")
            self.assertEqual([e["tick"] for e in choke], [1859], [e["tick"] for e in choke])
            self.assertEqual(choke[0]["data"], {"hp": 2})
            self.assertEqual(self.snaps(rows)[1900]["player"]["hp"], 2)

    def test_faint_bo_gio_lifo_va_kho_rong(self):
        """Máu 1 + đang ngạt: ngất ở tick 59, giỏ mất theo LIFO, kho rỗng."""
        sc = {"gather": {"player": {"pos": [50, 10], "hp": 1, "oxygen_ticks": 0, "zero_oxy_ticks": 0},
                         "hold": ["bong_sung", "ca_loc", "ca_linh"]}}
        with Workdir() as w:
            inv = w.path("inv.json")
            args = ["--mode", "gather", "--seed", "1", "--ticks", "80",
                    "--scenario", write_json(w.path("sc.json"), sc),
                    "--snapshot-every", "1", "--out", w.path("o.jsonl"), "--inventory-out", inv]
            code, err = run_headless(*args)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            names = [(e["tick"], e["name"]) for e in events(rows)]
            # Scenario đặt sẵn oxy = 0 ⇒ bước đầu tiên có oxy 0 là t = 1, nên ngạt đầu ở t+59 = 60.
            # (Ca ngập từ oxy đầy: chạm 0 ở t = 1800 ⇒ ngạt ở 1859 — xem test_choke_lan_dau_o_t_plus_59.)
            self.assertIn((60, "faint"), names, names)
            faint = events(rows, "faint")[0]["data"]
            self.assertEqual(faint["cause"], "choke")
            self.assertEqual(faint["hp"], 0)
            self.assertEqual(faint["lost"], ["ca_linh", "ca_loc", "bong_sung"])
            end = events(rows, "gather_end")[0]
            self.assertEqual(end["data"]["reason"], "fainted")
            self.assertEqual(end["data"]["inventory"]["items"], {})
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {}})

    def test_noi_len_dung_tick_dang_le_ngat_thi_khong_ngat(self):
        """Oxy 0, tick 1 nổi lên mặt: hồi oxy, bộ đếm ngạt về 0, không có choke."""
        sc = {"gather": {"player": {"pos": [50, 1], "oxygen_ticks": 0, "zero_oxy_ticks": 0}}}
        with Workdir() as w:
            rows = self.run_gather(w, sc, [{"tick": 0, "move": [0, -1]}], ticks=40)
            self.assertEqual(events(rows, "choke"), [])
            self.assertGreater(self.snaps(rows)[40]["player"]["oxygen_ticks"], 0)


class Harvest(Base):
    def test_hai_nut_hoa_khoang_cach_thi_theo_id_key(self):
        """Player [12,0]; N2 ở 10 và N10 ở 14 cách đều ⇒ chọn N2 (id_key, không so chuỗi)."""
        sc = {"gather": {"player": {"pos": [12, 0]},
                         "nodes": [{"id": "N10", "kind": "bong_dien_dien", "pos": [14, 0]},
                                   {"id": "N2", "kind": "bong_sung", "pos": [10, 0]}]}}
        with Workdir() as w:
            rows = self.run_gather(w, sc, [{"tick": 0, "interact": True}], ticks=5)
            ev = events(rows, "gather")
            self.assertEqual(len(ev), 1, [(e["name"], e["data"]) for e in events(rows)])
            self.assertEqual(ev[0]["data"]["node_id"], "N2")
            self.assertEqual(ev[0]["data"], {"node_id": "N2", "kind": "bong_sung", "amount": 1})
            self.assertEqual(self.snaps(rows)[5]["hold"], ["bong_sung"])

    def test_gio_day_thi_hold_full_khong_dat_regrow(self):
        """Giỏ 12/12: hold_full có action/node_id/required/free, nút vẫn ready."""
        g = tuning()
        sc = {"gather": {"player": {"pos": [12, 0]},
                         "hold": ["ca_loc"] * g["hold_capacity"],
                         "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [12, 0]}]}}
        with Workdir() as w:
            rows = self.run_gather(w, sc, [{"tick": 0, "interact": True}], ticks=5)
            self.assertEqual(events(rows, "gather"), [])
            hf = events(rows, "hold_full")
            self.assertEqual(len(hf), 1, [(e["name"], e["data"]) for e in events(rows)])
            self.assertEqual(hf[0]["data"], {"action": "gather", "node_id": "N1", "required": 1, "free": 0})
            node = self.snaps(rows)[5]["nodes"][0]
            self.assertEqual(node["regrow_ticks"], 0)
            self.assertTrue(node["ready"])

    def test_moc_lai_sau_1200_tick(self):
        """Hái ở tick 0 ⇒ node_regrown ở tick 1200, regrow_ticks = 1200."""
        sc = {"gather": {"player": {"pos": [12, 0]},
                         "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [12, 0]}]}}
        with Workdir() as w:
            rows = self.run_gather(w, sc, [{"tick": 0, "interact": True}], ticks=1250, every="1")
            harvest_tick = events(rows, "gather")[0]["tick"]
            self.assertEqual(self.snaps(rows)[harvest_tick]["nodes"][0]["regrow_ticks"], 1200)
            regrow = events(rows, "node_regrown")
            self.assertEqual([e["tick"] for e in regrow], [harvest_tick + 1200])


class Catch(Base):
    def test_bat_ca_xoa_dan_va_hoi_chieu_30_tick(self):
        """Bắt F1 (ca_linh, yield 3) ⇒ mất F1; bấm lại ngay bị hồi chiêu; tick 33 bắt F2."""
        sc = {"gather": {"player": {"pos": [15, 5]},
                         "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15, 5]},
                                  {"id": "F2", "kind": "ca_loc", "pos": [16, 5]}]}}
        inputs = [{"tick": 1, "catch": True}, {"tick": 2, "catch": False},
                  {"tick": 3, "catch": True}, {"tick": 4, "catch": False},
                  {"tick": 33, "catch": True}]
        with Workdir() as w:
            rows = self.run_gather(w, sc, inputs, ticks=40)
            caught = events(rows, "fish_caught")
            self.assertEqual([e["data"] for e in caught],
                             [{"fish_id": "F1", "kind": "ca_linh", "yield": 3},
                              {"fish_id": "F2", "kind": "ca_loc", "yield": 1}],
                             [(e["tick"], e["data"]) for e in caught])
            self.assertEqual([e["tick"] for e in caught], [2, 34])
            self.assertEqual(self.snaps(rows)[0]["fish"][0]["id"], "F1")
            self.assertEqual([f["id"] for f in self.snaps(rows)[40]["fish"]], [])

    def test_khong_co_dan_trong_tam_thi_khong_hoi_chieu(self):
        """Bấm catch ở nơi không có cá: không event, không hồi chiêu."""
        sc = {"gather": {"player": {"pos": [50, 20]}, "fish": [
            {"id": "F1", "kind": "ca_linh", "pos": [15, 5]}]}}
        with Workdir() as w:
            rows = self.run_gather(w, sc, [{"tick": 0, "catch": True}], ticks=5)
            self.assertEqual(events(rows, "fish_caught"), [])
            self.assertEqual(self.snaps(rows)[5]["player"]["catch_cd_ticks"], 0)


class Dock(Base):
    def test_cap_ben_thang_hai_khi_dang_lan(self):
        """Đứng [2,2] (trong bán kính 3, d = 2): interact ⇒ docked, không cần ở mặt nước."""
        with Workdir() as w:
            inv = w.path("inv.json")
            sc = {"gather": {"player": {"pos": [2, 2]}, "hold": ["ca_loc"]}}
            args = ["--mode", "gather", "--seed", "1", "--ticks", "5",
                    "--scenario", write_json(w.path("sc.json"), sc),
                    "--inputs", write_json(w.path("in.json"), frames({"tick": 0, "interact": True})),
                    "--out", w.path("o.jsonl"), "--inventory-out", inv]
            code, err = run_headless(*args)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "docked")
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {"ca_loc": 1}})

    def test_het_gio_duoi_sau_van_giu_gio(self):
        """Hết giờ khi đang ở d = 20: gather_end 'time', kho vẫn có món."""
        with Workdir() as w:
            inv = w.path("inv.json")
            sc = {"gather": {"player": {"pos": [50, 20]}, "hold": ["ca_loc", "bong_sung"],
                             "time_left_ticks": 3}}
            args = ["--mode", "gather", "--seed", "1", "--ticks", "100",
                    "--scenario", write_json(w.path("sc.json"), sc),
                    "--out", w.path("o.jsonl"), "--inventory-out", inv]
            code, err = run_headless(*args)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            end = events(rows, "gather_end")
            self.assertEqual(len(end), 1)
            self.assertEqual((end[0]["tick"], end[0]["data"]["reason"]), (3, "time"))
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {"bong_sung": 1, "ca_loc": 1}})


if __name__ == "__main__":
    unittest.main()
