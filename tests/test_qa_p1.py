"""Test QA Phase 1, kiểu HỘP ĐEN: chỉ chạy `headless_cmd` và đọc JSONL / file kho.

Mỗi test gắn mã AC trong docs/verification/phase-1.md (tên test chứa `ac_p1_xx`).
Số kỳ vọng suy từ preset trong game.contract.json (đọc qua `G`), quy đổi 60 tick = 1 s.
Quy ước tick (PRD-0 mục F): bước k đọc frame tick = k và ghi event ở tick k + 1.

Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_qa_p1 -v
"""

import json
import math
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

with open("game.contract.json", encoding="utf-8") as _f:
    TUNING = json.load(_f)["tuning"]
G = TUNING["gather"]
OXY_MAX = int(round(G["oxygen_max_s"] * 60))          # 1800
REGROW = int(round(G["regrow_s"] * 60))               # 1200
CATCH_CD = int(round(G["catch_cooldown_s"] * 60))     # 30
CHOKE = G["choke_interval_ticks"]                     # 60
REFILL = G["oxygen_refill_per_tick"]                  # 6
CAP = G["hold_capacity"]                              # 12


def run_gather(w, scenario, inputs=None, ticks=1, seed=1, inv_out=None, snapshot_every=None):
    """Chạy gather với khối scenario `gather`; trả list dòng JSONL. Fail ngay nếu mã thoát khác 0."""
    args = ["--mode", "gather", "--seed", str(seed), "--ticks", str(ticks), "--out", w.path("g.jsonl"),
            "--scenario", write_json(w.path("sc.json"), {"gather": scenario})]
    if inputs is not None:
        args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
    if inv_out:
        args += ["--inventory-out", inv_out]
    if snapshot_every:
        args += ["--snapshot-every", str(snapshot_every)]
    code, err = run_headless(*args)
    if code != 0:
        raise AssertionError(f"headless thoát mã {code}: {err}")
    return read_jsonl(w.path("g.jsonl"))


def last_snap(rows):
    return snapshots(rows)[-1]


def names(rows):
    return [r["name"] for r in rows if r["type"] == "event"]


def press(btn, tick):
    """Cạnh lên ở `tick`, nhả ở tick sau."""
    return [{"tick": tick, btn: True}, {"tick": tick + 1, btn: False}]


UNDER = [20, 5]       # chắc chắn dưới nước
SURF = [20, 0]        # mặt nước
NO_FISH = {"fish": [], "random_fish": False}


# ---------------------------------------------------------------- Lát 1: oxy, ngạt, Máu, giỏ (TV1)
class Oxygen(unittest.TestCase):
    def test_ac_p1_08_oxy_giam_1_moi_tick_duoi_nuoc(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": UNDER}, **NO_FISH}, ticks=10)
            self.assertEqual(last_snap(rows)["player"]["oxygen_ticks"], OXY_MAX - 10)

    def test_ac_p1_08_oxy_hoi_o_mat_nuoc(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": SURF, "oxygen_ticks": 100}, **NO_FISH}, ticks=1)
            self.assertEqual(last_snap(rows)["player"]["oxygen_ticks"], 100 + REFILL)

    def test_ac_p1_08_oxy_hoi_kep_toi_da(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": SURF, "oxygen_ticks": OXY_MAX - 2}, **NO_FISH}, ticks=1)
            self.assertEqual(last_snap(rows)["player"]["oxygen_ticks"], OXY_MAX)

    def test_ac_p1_08_oxygen_empty_khi_cham_0(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": UNDER, "oxygen_ticks": 1}, **NO_FISH}, ticks=3)
            ev = events(rows, "oxygen_empty")
            self.assertEqual(len(ev), 1, "chỉ phát khi từ dương xuống 0, không lặp lại")
            self.assertEqual(ev[0]["tick"], 1)
            self.assertEqual(ev[0]["data"], {"oxygen_ticks": 0})
            p = last_snap(rows)["player"]
            self.assertEqual(p["oxygen_ticks"], 0)
            self.assertEqual(p["zero_oxy_ticks"], 3, "bước vừa chạm 0 cũng đếm ngạt")

    def test_ac_p1_08_noi_len_reset_dem_ngat(self):
        with Workdir() as w:
            sc = {"player": {"pos": [20, 0.52], "vel": [0, -4], "oxygen_ticks": 0, "zero_oxy_ticks": 30}, **NO_FISH}
            rows = run_gather(w, sc, inputs=[{"tick": 0, "move": [0, -1]}], ticks=1)
            p = last_snap(rows)["player"]
            self.assertTrue(p["at_surface"])
            self.assertEqual(p["zero_oxy_ticks"], 0)
            self.assertEqual(p["oxygen_ticks"], REFILL)


class DiveSurface(unittest.TestCase):
    def test_ac_p1_09_dive_va_surface_moi_lan_doi_phia_mot_event(self):
        with Workdir() as w:
            inputs = [{"tick": 0, "move": [0, 1]}, {"tick": 40, "move": [0, -1]}, {"tick": 120, "move": [0, 0]}]
            rows = run_gather(w, {"player": {"pos": SURF}, **NO_FISH}, inputs=inputs, ticks=150)
            dive, surf = events(rows, "dive"), events(rows, "surface")
            self.assertEqual(len(dive), 1)
            self.assertEqual(len(surf), 1)
            self.assertGreater(dive[0]["data"]["pos"][1], G["surface_depth"])
            self.assertLessEqual(surf[0]["data"]["pos"][1], G["surface_depth"])
            self.assertLess(dive[0]["tick"], surf[0]["tick"])

    def test_ac_p1_09_dung_yen_khong_co_dive_surface(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": UNDER}, **NO_FISH}, ticks=20)
            self.assertEqual(events(rows, "dive") + events(rows, "surface"), [])


class Choke(unittest.TestCase):
    def test_ac_p1_10_ngat_lan_dau_o_t_cong_59(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": UNDER, "oxygen_ticks": 1}, **NO_FISH}, ticks=70)
            empty = events(rows, "oxygen_empty")
            self.assertEqual(len(empty), 1, "thiếu oxygen_empty")
            t = empty[0]["tick"]
            ch = events(rows, "choke")
            self.assertEqual(len(ch), 1)
            self.assertEqual(ch[0]["tick"], t + CHOKE - 1)
            self.assertEqual(ch[0]["data"], {"hp": G["hp_max"] - 1})
            self.assertEqual(last_snap(rows)["player"]["hp"], G["hp_max"] - 1)

    def test_ac_p1_10_ngat_lap_lai_moi_60_tick(self):
        with Workdir() as w:
            sc = {"player": {"pos": UNDER, "oxygen_ticks": 0, "zero_oxy_ticks": 59}, **NO_FISH}
            rows = run_gather(w, sc, ticks=61)
            self.assertEqual([e["tick"] for e in events(rows, "choke")], [1, 61])

    def test_ac_p1_10_noi_len_dung_buoc_ngat_thi_khong_ngat(self):
        with Workdir() as w:
            sc = {"player": {"pos": [20, 0.52], "vel": [0, -4], "oxygen_ticks": 0, "zero_oxy_ticks": 59}, **NO_FISH}
            rows = run_gather(w, sc, inputs=[{"tick": 0, "move": [0, -1]}], ticks=1)
            self.assertEqual(events(rows, "choke"), [])
            self.assertEqual(len(events(rows, "surface")), 1)
            p = last_snap(rows)["player"]
            self.assertEqual(p["hp"], G["hp_max"])
            self.assertEqual(p["oxygen_ticks"], REFILL)

    def test_ac_p1_10_doi_chung_o_duoi_thi_ngat(self):
        with Workdir() as w:
            sc = {"player": {"pos": UNDER, "oxygen_ticks": 0, "zero_oxy_ticks": 59}, **NO_FISH}
            rows = run_gather(w, sc, ticks=1)
            self.assertEqual(len(events(rows, "choke")), 1)


class Faint(unittest.TestCase):
    SC = {"player": {"pos": UNDER, "hp": 1, "oxygen_ticks": 0, "zero_oxy_ticks": 59},
          "hold": ["ca_loc", "bong_sung", "ca_linh"], **NO_FISH}

    def test_ac_p1_11_ngat_xiu_bo_gio_lifo_va_ket_thuc(self):
        with Workdir() as w:
            inv = w.path("inv.json")
            rows = run_gather(w, self.SC, ticks=50, inv_out=inv)
            self.assertEqual(names(rows), ["choke", "faint", "gather_end"])
            self.assertEqual(events(rows, "choke")[0]["data"], {"hp": 0})
            self.assertEqual(events(rows, "faint")[0]["data"],
                             {"cause": "choke", "lost": ["ca_linh", "bong_sung", "ca_loc"], "hp": 0})
            end_ev = events(rows, "gather_end")[0]
            self.assertEqual(end_ev["tick"], 1)
            self.assertEqual(end_ev["data"], {"reason": "fainted", "inventory": {"items": {}}})
            self.assertEqual(rows[-1]["type"], "end")
            self.assertEqual(rows[-1]["reason"], "fainted")
            self.assertEqual(rows[-1]["sim_tick"], 1, "dừng sớm khi gameplay kết thúc")
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {}})


# ---------------------------------------------------------------- Lát 2: hái, bắt cá, cập bến, kho (TV2)
def node(nid, kind, x, regrow=0):
    return {"id": nid, "kind": kind, "pos": [x, 0], "regrow_ticks": regrow}


def fish(fid, kind, x, d):
    return {"id": fid, "kind": kind, "pos": [x, d]}


class GatherNode(unittest.TestCase):
    def test_ac_p1_14_hai_dung_mep_ban_kinh(self):
        with Workdir() as w:
            sc = {"player": {"pos": SURF}, "hold": ["ca_loc"], "nodes": [node("N1", "bong_dien_dien", 22)], **NO_FISH}
            rows = run_gather(w, sc, inputs=press("interact", 0), ticks=2)
            ev = events(rows, "gather")
            self.assertEqual(len(ev), 1)
            self.assertEqual(ev[0]["tick"], 1)
            self.assertEqual(ev[0]["data"], {"node_id": "N1", "kind": "bong_dien_dien", "amount": G["node_yield"]})
            s = last_snap(rows)
            self.assertEqual(s["hold"], ["ca_loc", "bong_dien_dien"], "giỏ theo thứ tự nhặt, mới nhất cuối")
            n1 = s["nodes"][0]
            self.assertFalse(n1["ready"])
            self.assertEqual(n1["regrow_ticks"], REGROW - 1)

    def test_ac_p1_14_ngoai_ban_kinh_khong_hai(self):
        with Workdir() as w:
            sc = {"player": {"pos": SURF}, "nodes": [node("N1", "bong_sung", 22.01)], **NO_FISH}
            rows = run_gather(w, sc, inputs=press("interact", 0), ticks=2)
            self.assertEqual(events(rows, "gather"), [])

    def test_ac_p1_14_chon_nut_gan_nhat(self):
        with Workdir() as w:
            sc = {"player": {"pos": SURF},
                  "nodes": [node("N1", "bong_sung", 21.5), node("N2", "bong_dien_dien", 20.5)], **NO_FISH}
            rows = run_gather(w, sc, inputs=press("interact", 0), ticks=1)
            self.assertEqual([e["data"]["node_id"] for e in events(rows, "gather")], ["N2"])

    def test_ac_p1_14_hoa_khoang_cach_chon_id_nho(self):
        with Workdir() as w:
            sc = {"player": {"pos": SURF},
                  "nodes": [node("N2", "bong_sung", 19), node("N1", "bong_dien_dien", 21)], **NO_FISH}
            rows = run_gather(w, sc, inputs=press("interact", 0), ticks=1)
            self.assertEqual([e["data"]["node_id"] for e in events(rows, "gather")], ["N1"])

    def test_ac_p1_14_bo_qua_nut_chua_ready(self):
        with Workdir() as w:
            sc = {"player": {"pos": SURF},
                  "nodes": [node("N1", "bong_sung", 20.5, regrow=500), node("N2", "bong_dien_dien", 21.5)], **NO_FISH}
            rows = run_gather(w, sc, inputs=press("interact", 0), ticks=1)
            self.assertEqual([e["data"]["node_id"] for e in events(rows, "gather")], ["N2"])

    def test_ac_p1_14_duoi_nuoc_khong_hai(self):
        with Workdir() as w:
            sc = {"player": {"pos": [20, 1]}, "nodes": [node("N1", "bong_sung", 20)], **NO_FISH}
            rows = run_gather(w, sc, inputs=press("interact", 0), ticks=2)
            self.assertEqual(events(rows, "gather") + events(rows, "hold_full"), [])

    def test_ac_p1_12_ac_p1_14_gio_day_hold_full_nut_giu_nguyen(self):
        with Workdir() as w:
            sc = {"player": {"pos": SURF}, "hold": ["bong_sung"] * CAP,
                  "nodes": [node("N1", "bong_dien_dien", 21)], **NO_FISH}
            rows = run_gather(w, sc, inputs=press("interact", 0), ticks=1)
            self.assertEqual(events(rows, "gather"), [])
            hf = events(rows, "hold_full")
            self.assertEqual(len(hf), 1)
            self.assertEqual(hf[0]["data"], {"action": "gather", "node_id": "N1", "required": 1, "free": 0})
            s = last_snap(rows)
            self.assertEqual(s["hold_count"], CAP)
            self.assertTrue(s["nodes"][0]["ready"])

    def test_ac_p1_04_giu_nut_khong_hai_lap(self):
        with Workdir() as w:
            sc = {"player": {"pos": SURF},
                  "nodes": [node("N1", "bong_sung", 20.5), node("N2", "bong_sung", 21)], **NO_FISH}
            rows = run_gather(w, sc, inputs=[{"tick": 0, "interact": True}], ticks=5)
            self.assertEqual(len(events(rows, "gather")), 1, "chỉ tác động ở cạnh lên")


class Regrow(unittest.TestCase):
    def test_ac_p1_15_node_regrown_va_hai_ngay_cung_buoc(self):
        with Workdir() as w:
            sc = {"player": {"pos": SURF}, "nodes": [node("N1", "bong_sung", 21, regrow=1)], **NO_FISH}
            rows = run_gather(w, sc, inputs=press("interact", 0), ticks=1)
            self.assertEqual(names(rows), ["node_regrown", "gather"])
            self.assertEqual(events(rows, "node_regrown")[0]["data"], {"node_id": "N1"})


class Catch(unittest.TestCase):
    def test_ac_p1_16_bat_ca_linh_du_yield(self):
        with Workdir() as w:
            sc = {"player": {"pos": UNDER}, "fish": [fish("F1", "ca_linh", 21, 5)], "random_fish": False}
            rows = run_gather(w, sc, inputs=press("catch", 0), ticks=1)
            ev = events(rows, "fish_caught")
            self.assertEqual(len(ev), 1)
            self.assertEqual(ev[0]["tick"], 1)
            self.assertEqual(ev[0]["data"], {"fish_id": "F1", "kind": "ca_linh", "yield": G["fish_yield"]["ca_linh"]})
            s = last_snap(rows)
            self.assertEqual(s["hold"], ["ca_linh"] * G["fish_yield"]["ca_linh"])
            self.assertEqual(s["fish"], [])

    def test_ac_p1_16_chon_dan_gan_nhat_hoa_theo_id(self):
        with Workdir() as w:
            sc = {"player": {"pos": UNDER},
                  "fish": [fish("F2", "ca_linh", 19, 5), fish("F1", "ca_loc", 21, 5)], "random_fish": False}
            rows = run_gather(w, sc, inputs=press("catch", 0), ticks=1)
            self.assertEqual([e["data"]["fish_id"] for e in events(rows, "fish_caught")], ["F1"])

    def test_ac_p1_16_hoi_chieu_30_tick(self):
        sc = {"player": {"pos": UNDER},
              "fish": [fish("F1", "ca_loc", 21, 5), fish("F2", "ca_loc", 21.5, 5)], "random_fish": False}
        with Workdir() as w:
            rows = run_gather(w, sc, inputs=press("catch", 0) + press("catch", CATCH_CD - 1), ticks=CATCH_CD + 1)
            self.assertEqual(len(events(rows, "fish_caught")), 1, "còn hồi chiêu ở tick L-1")
        with Workdir() as w:
            rows = run_gather(w, sc, inputs=press("catch", 0) + press("catch", CATCH_CD), ticks=CATCH_CD + 2)
            self.assertEqual([e["tick"] for e in events(rows, "fish_caught")], [1, CATCH_CD + 1], "dùng lại từ t+L")

    def test_ac_p1_16_o_mat_nuoc_khong_bat(self):
        with Workdir() as w:
            sc = {"player": {"pos": SURF}, "fish": [fish("F1", "ca_loc", 20, 1.5)], "random_fish": False}
            rows = run_gather(w, sc, inputs=press("catch", 0), ticks=1)
            self.assertEqual(events(rows, "fish_caught") + events(rows, "hold_full"), [])

    def test_ac_p1_16_thieu_cho_hold_full_khong_thu_dan_khac_khong_hoi_chieu(self):
        with Workdir() as w:
            sc = {"player": {"pos": UNDER}, "hold": ["bong_sung"] * (CAP - 2),
                  "fish": [fish("F1", "ca_linh", 21, 5), fish("F2", "ca_loc", 21.5, 5)], "random_fish": False}
            rows = run_gather(w, sc, inputs=press("catch", 0) + press("catch", 2), ticks=3)
            self.assertEqual(events(rows, "fish_caught"), [])
            hf = events(rows, "hold_full")
            self.assertEqual([e["tick"] for e in hf], [1, 3], "không đặt hồi chiêu khi hold_full")
            self.assertEqual(hf[0]["data"], {"action": "catch", "fish_id": "F1",
                                             "required": G["fish_yield"]["ca_linh"], "free": 2})
            self.assertEqual([f["id"] for f in last_snap(rows)["fish"]], ["F1", "F2"])

    def test_ac_p1_16_khong_co_dan_trong_tam_khong_su_kien(self):
        with Workdir() as w:
            sc = {"player": {"pos": UNDER}, "fish": [fish("F1", "ca_loc", 30, 5)], "random_fish": False}
            rows = run_gather(w, sc, inputs=press("catch", 0) + press("catch", 2), ticks=3)
            self.assertEqual(events(rows, "fish_caught") + events(rows, "hold_full"), [])


class Dock(unittest.TestCase):
    def test_ac_p1_13_dung_mep_ben_la_docked(self):
        with Workdir() as w:
            x = G["dock_pos"][0] + G["dock_radius"]
            rows = run_gather(w, {"player": {"pos": [x, 0]}, "nodes": [], **NO_FISH},
                              inputs=press("interact", 0), ticks=5)
            self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "docked")
            self.assertEqual(rows[-1]["reason"], "docked")

    def test_ac_p1_13_ngoai_ben_khong_ket_thuc(self):
        with Workdir() as w:
            x = G["dock_pos"][0] + G["dock_radius"] + 0.01
            rows = run_gather(w, {"player": {"pos": [x, 0]}, "nodes": [], **NO_FISH},
                              inputs=press("interact", 0), ticks=5)
            self.assertEqual(events(rows, "gather_end"), [])
            self.assertEqual(rows[-1]["reason"], "tick_limit")

    def test_ac_p1_13_ben_xet_truoc_hai(self):
        with Workdir() as w:
            sc = {"player": {"pos": [4, 0]}, "nodes": [node("N1", "bong_sung", 5)], **NO_FISH}
            rows = run_gather(w, sc, inputs=press("interact", 0), ticks=5)
            self.assertEqual(names(rows), ["gather_end"])
            self.assertEqual(events(rows, "gather_end")[0]["data"]["inventory"], {"items": {}})


class TimeEnd(unittest.TestCase):
    def test_ac_p1_17_hai_o_buoc_cuoi_van_vao_kho(self):
        with Workdir() as w:
            inv = w.path("inv.json")
            sc = {"player": {"pos": SURF}, "nodes": [node("N1", "bong_sung", 21)], "time_left_ticks": 1, **NO_FISH}
            rows = run_gather(w, sc, inputs=press("interact", 0), ticks=5, inv_out=inv)
            self.assertEqual(names(rows), ["gather", "gather_end"])
            self.assertEqual(events(rows, "gather_end")[0]["data"],
                             {"reason": "time", "inventory": {"items": {"bong_sung": 1}}})
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {"bong_sung": 1}})

    def test_ac_p1_17_ben_o_buoc_cuoi_uu_tien_docked(self):
        with Workdir() as w:
            sc = {"player": {"pos": G["dock_pos"]}, "time_left_ticks": 1, **NO_FISH}
            rows = run_gather(w, sc, inputs=press("interact", 0), ticks=5)
            self.assertEqual(rows[-1]["reason"], "docked")

    def test_ac_p1_17_het_gio_duoi_nuoc_giu_gio(self):
        with Workdir() as w:
            sc = {"player": {"pos": UNDER}, "hold": ["ca_loc", "ca_loc"], "time_left_ticks": 2, **NO_FISH}
            rows = run_gather(w, sc, ticks=5)
            self.assertEqual(events(rows, "gather_end")[0]["data"],
                             {"reason": "time", "inventory": {"items": {"ca_loc": 2}}})


# ---------------------------------------------------------------- Contract chung
class OutputFormat(unittest.TestCase):
    def test_ac_p1_06_score_moi_snapshot_va_end(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": UNDER}}, ticks=25)
            for r in snapshots(rows) + [rows[-1]]:
                self.assertEqual(r["score"], r["earned"] + 100 * math.floor(r["reputation"]), r["type"])

    def test_ac_p1_06_snapshot_tick_0_boi_so_va_tick_dung(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": UNDER}}, ticks=25, snapshot_every=10)
            self.assertEqual([s["tick"] for s in snapshots(rows)], [0, 10, 20, 25])

    def test_ac_p1_06_sap_id_F2_truoc_F10(self):
        with Workdir() as w:
            sc = {"fish": [fish("F10", "ca_loc", 50, 5), fish("F2", "ca_linh", 60, 5)], "random_fish": False}
            rows = run_gather(w, sc, ticks=0)
            self.assertEqual([f["id"] for f in last_snap(rows)["fish"]], ["F2", "F10"])

    def test_ac_p1_03_cung_seed_giong_tung_byte_ca_file_kho(self):
        sc = {"player": {"pos": [18, 0]}, "hold": ["ca_loc"]}
        inputs = [{"tick": 0, "move": [1, 1]}, {"tick": 40, "move": [-1, -1], "catch": True},
                  {"tick": 41, "catch": False}, {"tick": 90, "interact": True}, {"tick": 91, "interact": False},
                  {"tick": 200, "move": [-1, -1]}]
        outs = []
        for _ in range(2):
            with Workdir() as w:
                inv = w.path("inv.json")
                run_gather(w, {**sc, "time_left_ticks": 400}, inputs=inputs, ticks=500, seed=99, inv_out=inv)
                with open(w.path("g.jsonl"), "rb") as a, open(inv, "rb") as b:
                    outs.append((a.read(), b.read()))
        self.assertEqual(outs[0], outs[1])

    def test_ac_p1_03_quan_cung_seed_giong_tung_byte(self):
        outs = []
        for _ in range(2):
            with Workdir() as w:
                st = write_json(w.path("sc.json"), {"quan": {"stock": {"ca_loc": 2, "bong_sung": 4,
                                                                       "ca_linh": 3, "bong_dien_dien": 1}}})
                code, err = run_headless("--mode", "quan", "--seed", "5", "--ticks", "3000", "--scenario", st,
                                         "--out", w.path("q.jsonl"))
                self.assertEqual(code, 0, err)
                with open(w.path("q.jsonl"), "rb") as f:
                    outs.append(f.read())
        self.assertEqual(outs[0], outs[1])


if __name__ == "__main__":
    unittest.main()
