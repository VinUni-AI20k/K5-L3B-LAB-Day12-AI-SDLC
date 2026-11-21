"""Test lát 2 (B): hái nút, bắt cá, giỏ đầy, kho cuối buổi — PRD-0 mục F (Gather) và mục E (sự kiện).
Kiểu hộp đen: chỉ chạy headless_cmd và đọc JSONL/file kho, số liệu đọc từ game.contract.json.

Chạy: PYTHONPATH=tests:. python3 -m unittest discover -s tests -p "test_gather_lat2.py" -v
(PowerShell: `$env:PYTHONPATH = "tests;."` trước khi chạy; dạng `-m unittest tests.test_gather_lat2` không chạy được trên Windows.)
"""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def tuning_gather():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]["gather"]


G = tuning_gather()
CAP = G["hold_capacity"]
REGROW = int(round(G["regrow_s"] * 60))
CATCH_CD = int(round(G["catch_cooldown_s"] * 60))
YIELD = G["fish_yield"]
NODE_YIELD = G["node_yield"]
R_INT = G["interact_radius"]
R_CATCH = G["catch_radius"]


def run_gather(block, ticks, inputs=None, inventory_out=False, every=1):
    """Chạy gather với scenario `block` (cá và nút mặc định tắt). Trả (rows, kho hoặc None, bytes JSONL)."""
    block = {"random_fish": False, "nodes": [], **block}
    with Workdir() as w:
        sc = write_json(w.path("sc.json"), {"gather": block})
        args = ["--mode", "gather", "--seed", "1", "--ticks", str(ticks), "--scenario", sc,
                "--snapshot-every", str(every), "--out", w.path("o.jsonl")]
        if inputs is not None:
            args += ["--inputs", write_json(w.path("in.json"), inputs)]
        if inventory_out:
            args += ["--inventory-out", w.path("inv.json")]
        code, err = run_headless(*args)
        assert code == 0, err
        inv = None
        if inventory_out:
            with open(w.path("inv.json"), encoding="utf-8") as f:
                inv = json.load(f)
        with open(w.path("o.jsonl"), "rb") as f:
            raw = f.read()
        return read_jsonl(w.path("o.jsonl")), inv, raw


def snap_at(rows, tick):
    return {s["tick"]: s for s in snapshots(rows)}[tick]


def node(nid, x, kind="bong_sung", regrow=None):
    n = {"id": nid, "kind": kind, "pos": [x, 0]}
    if regrow is not None:
        n["regrow_ticks"] = regrow
    return n


def fish(fid, x, d, kind="ca_linh"):
    return {"id": fid, "kind": kind, "pos": [x, d]}


INTERACT0 = frames({"tick": 0, "interact": True})
CATCH0 = frames({"tick": 0, "catch": True})
SURF = [20, 0]      # mặt nước, xa bến (bến ở [2, 0], bán kính 3)
UNDER = [20, 5]     # dưới nước


class Harvest(unittest.TestCase):
    def test_hai_nut_gan_nhat_them_vao_cuoi_gio_va_dat_hoi_phuc(self):
        rows, _, _ = run_gather({"player": {"pos": SURF}, "hold": ["ca_loc"],
                                 "nodes": [node("N1", 21, "bong_dien_dien")]}, 1, INTERACT0)
        ev = events(rows, "gather")
        self.assertEqual(len(ev), 1)
        self.assertEqual(ev[0]["tick"], 1)
        self.assertEqual(ev[0]["data"], {"node_id": "N1", "kind": "bong_dien_dien", "amount": NODE_YIELD})
        s = snap_at(rows, 1)
        self.assertEqual(s["hold"], ["ca_loc"] + ["bong_dien_dien"] * NODE_YIELD)  # cuối mảng là mới nhất
        self.assertEqual(s["hold_count"], 1 + NODE_YIELD)
        n = s["nodes"][0]
        self.assertEqual((n["ready"], n["regrow_ticks"]), (False, REGROW))

    def test_dung_mep_ban_kinh_duoc_vuot_mep_khong(self):
        rows, _, _ = run_gather({"player": {"pos": SURF}, "nodes": [node("N1", 20 + R_INT)]}, 1, INTERACT0)
        self.assertEqual(len(events(rows, "gather")), 1)
        rows, _, _ = run_gather({"player": {"pos": SURF}, "nodes": [node("N1", 20 + R_INT + 0.01)]}, 1, INTERACT0)
        self.assertEqual(events(rows), [])
        self.assertEqual(snap_at(rows, 1)["hold"], [])

    def test_dang_lan_khong_hai_duoc(self):
        """Dưới nước dù nút trong bán kính (d = 1 so với nút ở d = 0) vẫn không hái."""
        rows, _, _ = run_gather({"player": {"pos": [20, 1]}, "nodes": [node("N1", 20)]}, 1, INTERACT0)
        self.assertEqual(events(rows), [])
        self.assertTrue(snap_at(rows, 1)["nodes"][0]["ready"])

    def test_nut_chua_moc_lai_bi_bo_qua(self):
        rows, _, _ = run_gather({"player": {"pos": SURF}, "nodes": [node("N1", 20, regrow=5)]}, 1, INTERACT0)
        self.assertEqual(events(rows, "gather"), [])
        self.assertEqual(snap_at(rows, 1)["hold"], [])

    def test_chon_nut_gan_nhat_chu_khong_phai_id_nho(self):
        rows, _, _ = run_gather({"player": {"pos": SURF}, "nodes": [node("N1", 21.5), node("N2", 19)]}, 1, INTERACT0)
        self.assertEqual(events(rows, "gather")[0]["data"]["node_id"], "N2")

    def test_hoa_khoang_cach_chon_id_nho_theo_so(self):
        """N2 đứng trước N10 (sắp theo hậu tố số, không theo chữ)."""
        rows, _, _ = run_gather({"player": {"pos": SURF}, "nodes": [node("N10", 19), node("N2", 21)]}, 1, INTERACT0)
        self.assertEqual(events(rows, "gather")[0]["data"]["node_id"], "N2")

    def test_nut_bi_bo_qua_thi_chon_nut_ke_tiep(self):
        rows, _, _ = run_gather({"player": {"pos": SURF}, "nodes": [node("N1", 20, regrow=50), node("N2", 21)]},
                                1, INTERACT0)
        self.assertEqual(events(rows, "gather")[0]["data"]["node_id"], "N2")

    def test_nut_moc_lai_sau_dung_regrow_s(self):
        rows, _, _ = run_gather({"player": {"pos": SURF}, "nodes": [node("N1", 20)]}, REGROW + 5,
                                INTERACT0, every=REGROW)
        regrown = events(rows, "node_regrown")
        self.assertEqual(len(regrown), 1)
        self.assertEqual(regrown[0]["data"], {"node_id": "N1"})
        self.assertEqual(regrown[0]["tick"], 1 + REGROW)  # hái ở bước 0, đếm ngược từ bước 1
        self.assertTrue(snap_at(rows, REGROW + 5)["nodes"][0]["ready"])

    def test_hai_tiep_tuc_duoc_sau_khi_moc_lai(self):
        inp = frames({"tick": 0, "interact": True}, {"tick": 1, "interact": False},
                     {"tick": 1 + REGROW, "interact": True})
        rows, _, _ = run_gather({"player": {"pos": SURF}, "nodes": [node("N1", 20)]}, REGROW + 5, inp, every=REGROW)
        self.assertEqual([e["tick"] for e in events(rows, "gather")], [1, 2 + REGROW])
        self.assertEqual(snap_at(rows, REGROW + 5)["hold_count"], 2 * NODE_YIELD)

    def test_khong_nhan_giu_nut_phai_nha_roi_bam_lai(self):
        """interact chỉ tính ở cạnh lên: giữ phím không hái thêm khi nút vừa mọc lại."""
        inp = frames({"tick": 0, "interact": True})  # giữ suốt
        rows, _, _ = run_gather({"player": {"pos": SURF}, "nodes": [node("N1", 20)]}, REGROW + 5, inp, every=REGROW)
        self.assertEqual(len(events(rows, "gather")), 1)


class HarvestFullHold(unittest.TestCase):
    def test_gio_day_hold_full_nut_giu_nguyen(self):
        hold = ["ca_loc"] * CAP
        rows, _, _ = run_gather({"player": {"pos": SURF}, "hold": hold, "nodes": [node("N1", 20)]}, 1, INTERACT0)
        self.assertEqual([r["name"] for r in events(rows)], ["hold_full"])
        self.assertEqual(events(rows)[0]["data"], {"action": "gather", "node_id": "N1",
                                                   "required": NODE_YIELD, "free": 0})
        s = snap_at(rows, 1)
        self.assertEqual(s["hold"], hold)
        self.assertEqual((s["nodes"][0]["ready"], s["nodes"][0]["regrow_ticks"]), (True, 0))

    def test_con_dung_mot_cho_van_hai_duoc(self):
        rows, _, _ = run_gather({"player": {"pos": SURF}, "hold": ["ca_loc"] * (CAP - NODE_YIELD),
                                 "nodes": [node("N1", 20)]}, 1, INTERACT0)
        self.assertEqual([r["name"] for r in events(rows)], ["gather"])
        self.assertEqual(snap_at(rows, 1)["hold_count"], CAP)


class Catch(unittest.TestCase):
    def test_ca_linh_cho_3_xoa_dan_dat_hoi_chieu(self):
        rows, _, _ = run_gather({"player": {"pos": UNDER}, "fish": [fish("F1", 20, 6)]}, 1, CATCH0)
        ev = events(rows, "fish_caught")
        self.assertEqual(len(ev), 1)
        self.assertEqual(ev[0]["tick"], 1)
        self.assertEqual(ev[0]["data"], {"fish_id": "F1", "kind": "ca_linh", "yield": YIELD["ca_linh"]})
        s = snap_at(rows, 1)
        self.assertEqual(s["hold"], ["ca_linh"] * YIELD["ca_linh"])
        self.assertEqual(s["fish"], [])
        self.assertEqual(s["player"]["catch_cd_ticks"], CATCH_CD)

    def test_ca_loc_cho_1(self):
        rows, _, _ = run_gather({"player": {"pos": UNDER}, "fish": [fish("F1", 20, 6, "ca_loc")]}, 1, CATCH0)
        self.assertEqual(events(rows, "fish_caught")[0]["data"]["yield"], YIELD["ca_loc"])
        self.assertEqual(snap_at(rows, 1)["hold"], ["ca_loc"] * YIELD["ca_loc"])

    def test_o_mat_nuoc_khong_bat_duoc(self):
        rows, _, _ = run_gather({"player": {"pos": SURF}, "fish": [fish("F1", 20, 1)]}, 1, CATCH0)
        self.assertEqual(events(rows), [])
        s = snap_at(rows, 1)
        self.assertEqual((len(s["fish"]), s["hold"], s["player"]["catch_cd_ticks"]), (1, [], 0))

    def test_khong_co_dan_trong_tam_khong_hoi_chieu(self):
        rows, _, _ = run_gather({"player": {"pos": UNDER}, "fish": [fish("F1", 20, 5 + R_CATCH + 0.01)]}, 1, CATCH0)
        self.assertEqual(events(rows), [])
        s = snap_at(rows, 1)
        self.assertEqual((len(s["fish"]), s["player"]["catch_cd_ticks"]), (1, 0))

    def test_dung_mep_ban_kinh_bat_duoc(self):
        rows, _, _ = run_gather({"player": {"pos": UNDER}, "fish": [fish("F1", 20, 5 + R_CATCH)]}, 1, CATCH0)
        self.assertEqual(len(events(rows, "fish_caught")), 1)

    def test_chon_dan_gan_nhat(self):
        rows, _, _ = run_gather({"player": {"pos": UNDER}, "fish": [fish("F1", 20, 6.8), fish("F2", 20, 6)]}, 1, CATCH0)
        self.assertEqual(events(rows, "fish_caught")[0]["data"]["fish_id"], "F2")
        self.assertEqual([f["id"] for f in snap_at(rows, 1)["fish"]], ["F1"])

    def test_hoa_khoang_cach_chon_id_nho_theo_so(self):
        rows, _, _ = run_gather({"player": {"pos": UNDER}, "fish": [fish("F10", 19, 5), fish("F2", 21, 5)]}, 1, CATCH0)
        self.assertEqual(events(rows, "fish_caught")[0]["data"]["fish_id"], "F2")

    def _hai_dan(self, press_tick):
        inp = frames({"tick": 0, "catch": True}, {"tick": 1, "catch": False}, {"tick": press_tick, "catch": True})
        rows, _, _ = run_gather({"player": {"pos": [20, 6.5]},
                                 "fish": [fish("F1", 20, 6, "ca_loc"), fish("F2", 20, 7, "ca_loc")]},
                                press_tick + 2, inp)
        return [e["tick"] for e in events(rows, "fish_caught")]

    def test_hoi_chieu_chan_bam_lai_truoc_30_tick(self):
        self.assertEqual(self._hai_dan(CATCH_CD - 1), [1])

    def test_het_hoi_chieu_bat_tiep_duoc(self):
        self.assertEqual(self._hai_dan(CATCH_CD), [1, CATCH_CD + 1])

    def test_hoi_chieu_dem_nguoc_trong_snapshot(self):
        rows, _, _ = run_gather({"player": {"pos": UNDER}, "fish": [fish("F1", 20, 6)]}, CATCH_CD + 1, CATCH0)
        self.assertEqual(snap_at(rows, 1)["player"]["catch_cd_ticks"], CATCH_CD)
        self.assertEqual(snap_at(rows, 11)["player"]["catch_cd_ticks"], CATCH_CD - 10)
        self.assertEqual(snap_at(rows, CATCH_CD + 1)["player"]["catch_cd_ticks"], 0)


class CatchFullHold(unittest.TestCase):
    def test_thieu_cho_cho_ca_linh_hold_full_giu_dan_khong_hoi_chieu(self):
        need, free = YIELD["ca_linh"], YIELD["ca_linh"] - 1
        hold = ["ca_loc"] * (CAP - free)
        rows, _, _ = run_gather({"player": {"pos": UNDER}, "hold": hold, "fish": [fish("F1", 20, 6)]}, 1, CATCH0)
        self.assertEqual([r["name"] for r in events(rows)], ["hold_full"])
        self.assertEqual(events(rows)[0]["data"], {"action": "catch", "fish_id": "F1", "required": need, "free": free})
        s = snap_at(rows, 1)
        self.assertEqual((s["hold"], len(s["fish"]), s["player"]["catch_cd_ticks"]), (hold, 1, 0))

    def test_khong_thu_dan_khac_khi_dan_gan_nhat_khong_vua(self):
        free = YIELD["ca_linh"] - 1  # ca_loc (cần 1) vừa nhưng không được thử
        hold = ["bong_sung"] * (CAP - free)
        rows, _, _ = run_gather({"player": {"pos": UNDER},
                                 "hold": hold,
                                 "fish": [fish("F1", 20, 6, "ca_linh"), fish("F2", 20, 6.8, "ca_loc")]}, 1, CATCH0)
        self.assertEqual([r["name"] for r in events(rows)], ["hold_full"])
        self.assertEqual(events(rows)[0]["data"]["fish_id"], "F1")
        self.assertEqual(len(snap_at(rows, 1)["fish"]), 2)

    def test_con_dung_du_cho_van_bat_duoc(self):
        hold = ["ca_loc"] * (CAP - YIELD["ca_linh"])
        rows, _, _ = run_gather({"player": {"pos": UNDER}, "hold": hold, "fish": [fish("F1", 20, 6)]}, 1, CATCH0)
        self.assertEqual([r["name"] for r in events(rows)], ["fish_caught"])
        self.assertEqual(snap_at(rows, 1)["hold_count"], CAP)

    def test_hold_full_khong_dat_hoi_chieu_nen_bam_lai_ngay_van_thu(self):
        hold = ["ca_loc"] * CAP
        inp = frames({"tick": 0, "catch": True}, {"tick": 1, "catch": False}, {"tick": 2, "catch": True})
        rows, _, _ = run_gather({"player": {"pos": UNDER}, "hold": hold, "fish": [fish("F1", 20, 6)]}, 3, inp)
        self.assertEqual([e["tick"] for e in events(rows, "hold_full")], [1, 3])


class HarvestAndCatch(unittest.TestCase):
    def test_thu_tu_nhat_giu_nguyen_trong_hold(self):
        """Hái ở mặt nước, lặn bắt cá: hold giữ đúng thứ tự nhặt."""
        inp = frames({"tick": 0, "interact": True}, {"tick": 1, "interact": False, "move": [0, 1]},
                     {"tick": 40, "move": [0, 0]}, {"tick": 41, "catch": True})
        rows, _, _ = run_gather({"player": {"pos": SURF}, "nodes": [node("N1", 20, "bong_dien_dien")],
                                 "fish": [fish("F1", 20, 3, "ca_loc")]}, 45, inp)
        self.assertEqual(snap_at(rows, 45)["hold"], ["bong_dien_dien", "ca_loc"])


class Inventory(unittest.TestCase):
    def test_hai_o_buoc_cuoi_van_vao_kho(self):
        rows, inv, _ = run_gather({"player": {"pos": SURF}, "time_left_ticks": 1, "nodes": [node("N1", 20, "bong_dien_dien")]},
                                  5, INTERACT0, inventory_out=True)
        self.assertEqual([r["name"] for r in events(rows)], ["gather", "gather_end"])
        self.assertEqual(rows[-1]["reason"], "time")
        self.assertEqual(inv, {"items": {"bong_dien_dien": NODE_YIELD}})

    def test_bat_o_buoc_cuoi_van_vao_kho(self):
        rows, inv, _ = run_gather({"player": {"pos": UNDER}, "time_left_ticks": 1, "fish": [fish("F1", 20, 6)]},
                                  5, CATCH0, inventory_out=True)
        self.assertEqual([r["name"] for r in events(rows)], ["fish_caught", "gather_end"])
        self.assertEqual(inv, {"items": {"ca_linh": YIELD["ca_linh"]}})

    def test_cap_ben_ghi_dung_noi_dung_gio_va_quan_doc_duoc(self):
        """Bắt cá linh ở tick 0, bơi lên mặt nước rồi về bến, cập bến. Kho khớp gather_end và quán đọc được."""
        inp = frames({"tick": 0, "catch": True}, {"tick": 1, "catch": False, "move": [-1, -1]},
                     {"tick": 110, "move": [-1, 0]}, {"tick": 300, "interact": True})
        rows, inv, _ = run_gather({"player": {"pos": [15, 5]}, "fish": [fish("F1", 15, 5)]}, 400, inp,
                                  inventory_out=True)
        want = {"items": {"ca_linh": YIELD["ca_linh"]}}
        self.assertEqual(inv, want)
        end = events(rows, "gather_end")[0]
        self.assertEqual(end["data"], {"reason": "docked", "inventory": want})
        self.assertEqual(rows[-1]["reason"], "docked")
        with Workdir() as w:
            p = write_json(w.path("inv.json"), inv)
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", p,
                                     "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)
            self.assertEqual(snapshots(read_jsonl(w.path("q.jsonl")))[0]["stock"], want["items"])

    def test_tat_dinh_tung_byte_khi_hai_va_bat(self):
        inp = frames({"tick": 0, "interact": True}, {"tick": 1, "interact": False, "move": [0, 1]},
                     {"tick": 40, "move": [0, 0]}, {"tick": 41, "catch": True})
        block = {"player": {"pos": SURF}, "nodes": [node("N1", 20)], "fish": [fish("F1", 20, 3, "ca_loc")]}
        self.assertEqual(run_gather(block, 80, inp)[2], run_gather(block, 80, inp)[2])


class MacDinh(unittest.TestCase):
    def test_nut_va_dan_ca_mac_dinh_hoat_dong(self):
        """Không scenario: nút N1 ở [12, 0] (bong_dien_dien) hái được khi đứng ở mặt nước cạnh nó."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"player": {"pos": [12, 0]}}})
            inp = write_json(w.path("in.json"), INTERACT0)
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1", "--scenario", sc,
                                     "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            ev = events(read_jsonl(w.path("o.jsonl")), "gather")
            self.assertEqual(ev[0]["data"], {"node_id": "N1", "kind": "bong_dien_dien", "amount": NODE_YIELD})


if __name__ == "__main__":
    unittest.main()
