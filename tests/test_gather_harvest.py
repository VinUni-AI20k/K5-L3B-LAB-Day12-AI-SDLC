"""Gather lát 2: hái nút (try_gather) và bắt cá (try_catch). Test hộp đen qua headless.

Mỗi test tự dựng scenario; số liệu (bán kính, hồi chiêu, mọc lại...) đọc từ game.contract.json.
Nhớ: input `interact`/`catch` tính theo CẠNH LÊN, nên giữa hai lần bấm phải có frame thả nút.
Sự kiện của bước k mang tick = k + 1.
"""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def tuning():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]["gather"]


G = tuning()
REGROW = int(round(G["regrow_s"] * 60))
CATCH_CD = int(round(G["catch_cooldown_s"] * 60))
CAP = G["hold_capacity"]


def run_gather(w, scenario, ticks, inputs, name="o.jsonl"):
    sc = write_json(w.path("sc.json"), {"gather": scenario})
    inp = write_json(w.path("in.json"), inputs)
    code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", str(ticks), "--scenario", sc,
                             "--inputs", inp, "--snapshot-every", "1", "--out", w.path(name))
    assert code == 0, err
    return read_jsonl(w.path(name))


def press(*ticks, button):
    """Bấm `button` ở các tick đã cho (bấm rồi thả ngay ở tick kế)."""
    fr = {}
    for t in ticks:
        fr[t] = {"tick": t, button: True}
        fr.setdefault(t + 1, {"tick": t + 1, button: False})
    return frames(*[fr[t] for t in sorted(fr)])


def node(nid, x, kind="bong_sung", regrow_ticks=0):
    return {"id": nid, "kind": kind, "pos": [x, 0], "regrow_ticks": regrow_ticks}


def fish(fid, pos, kind="ca_linh"):
    return {"id": fid, "kind": kind, "pos": pos, "heading_deg": 0}


def last(rows):
    return snapshots(rows)[-1]


class Gather(unittest.TestCase):
    def test_hai_nut_gan_nhat(self):
        with Workdir() as w:
            sc = {"player": {"pos": [10, 0]}, "nodes": [node("N1", 11.5), node("N2", 10.5)]}
            rows = run_gather(w, sc, 3, press(0, button="interact"))
            ev = events(rows, "gather")
            self.assertEqual(len(ev), 1)
            self.assertEqual(ev[0]["tick"], 1)
            self.assertEqual(ev[0]["data"]["node_id"], "N2")
            self.assertEqual(ev[0]["data"]["kind"], "bong_sung")
            self.assertEqual(last(rows)["hold"], ["bong_sung"] * G["node_yield"])

    def test_bang_khoang_cach_id_nho_hon_thang(self):
        # N10 và N2 cùng cách 1.0: id nhỏ theo thứ tự số là N2 (không phải N10 theo chuỗi).
        with Workdir() as w:
            sc = {"player": {"pos": [10, 0]}, "nodes": [node("N10", 11), node("N2", 9)]}
            rows = run_gather(w, sc, 3, press(0, button="interact"))
            self.assertEqual(events(rows, "gather")[0]["data"]["node_id"], "N2")

    def test_ngoai_ban_kinh_khong_hai(self):
        with Workdir() as w:
            far = 10 + G["interact_radius"] + 0.5
            rows = run_gather(w, {"player": {"pos": [10, 0]}, "nodes": [node("N1", far)]}, 3,
                              press(0, button="interact"))
            self.assertEqual(events(rows, "gather"), [])
            self.assertEqual(last(rows)["hold"], [])

    def test_duoi_nuoc_khong_hai(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [10, 1]}, "nodes": [node("N1", 10)]}, 3,
                              press(0, button="interact"))
            self.assertEqual(events(rows, "gather"), [])
            self.assertEqual(last(rows)["hold"], [])

    def test_nut_moc_lai_sau_regrow_s(self):
        with Workdir() as w:
            sc = {"player": {"pos": [10, 0]}, "nodes": [node("N1", 10)]}
            rows = run_gather(w, sc, REGROW + 5, press(0, button="interact"))
            g = events(rows, "gather")[0]["tick"]
            regrown = events(rows, "node_regrown")
            self.assertEqual(len(regrown), 1)
            self.assertEqual(regrown[0]["data"], {"node_id": "N1"})
            self.assertEqual(regrown[0]["tick"] - g, REGROW)
            by_tick = {s["tick"]: s for s in snapshots(rows)}
            self.assertFalse(by_tick[g]["nodes"][0]["ready"])
            self.assertFalse(by_tick[regrown[0]["tick"] - 1]["nodes"][0]["ready"])
            self.assertTrue(by_tick[regrown[0]["tick"]]["nodes"][0]["ready"])

    def test_nut_chua_moc_lai_thi_khong_hai_lan_hai(self):
        with Workdir() as w:
            sc = {"player": {"pos": [10, 0]}, "nodes": [node("N1", 10)]}
            rows = run_gather(w, sc, 20, press(0, 10, button="interact"))
            self.assertEqual(len(events(rows, "gather")), 1)
            self.assertEqual(len(last(rows)["hold"]), G["node_yield"])

    def test_hai_lai_sau_khi_moc_lai(self):
        with Workdir() as w:
            sc = {"player": {"pos": [10, 0]}, "nodes": [node("N1", 10)]}
            rows = run_gather(w, sc, REGROW + 10, press(0, REGROW + 2, button="interact"))
            self.assertEqual(len(events(rows, "gather")), 2)

    def test_gio_day_phat_hold_full_nut_van_ready(self):
        with Workdir() as w:
            sc = {"player": {"pos": [10, 0]}, "nodes": [node("N1", 10)], "hold": ["ca_loc"] * CAP}
            rows = run_gather(w, sc, 3, press(0, button="interact"))
            self.assertEqual(events(rows, "gather"), [])
            hf = events(rows, "hold_full")
            self.assertEqual(len(hf), 1)
            self.assertEqual(hf[0]["data"], {"action": "gather", "node_id": "N1",
                                             "required": G["node_yield"], "free": 0})
            s = last(rows)
            self.assertEqual(s["hold_count"], CAP)
            self.assertTrue(s["nodes"][0]["ready"])


class Catch(unittest.TestCase):
    def test_bat_ca_linh_duoc_nhieu_mon_va_xoa_ca(self):
        with Workdir() as w:
            sc = {"player": {"pos": [15, 5]}, "nodes": [], "fish": [fish("F1", [15, 6])]}
            rows = run_gather(w, sc, 3, press(0, button="catch"))
            ev = events(rows, "fish_caught")
            self.assertEqual(len(ev), 1)
            self.assertEqual(ev[0]["tick"], 1)
            self.assertEqual(ev[0]["data"]["fish_id"], "F1")
            self.assertEqual(ev[0]["data"]["kind"], "ca_linh")
            s = last(rows)
            self.assertEqual(s["hold"], ["ca_linh"] * G["fish_yield"]["ca_linh"])
            self.assertEqual(s["fish"], [])

    def test_ca_loc_cho_dung_so_mon(self):
        with Workdir() as w:
            sc = {"player": {"pos": [15, 5]}, "nodes": [], "fish": [fish("F1", [15, 5], "ca_loc")]}
            rows = run_gather(w, sc, 3, press(0, button="catch"))
            self.assertEqual(last(rows)["hold"], ["ca_loc"] * G["fish_yield"]["ca_loc"])

    def test_ca_gan_nhat_va_bang_nhau_id_nho_thang(self):
        with Workdir() as w:
            sc = {"player": {"pos": [15, 5]}, "nodes": [], "fish": [fish("F10", [15, 6]), fish("F2", [15, 4])]}
            rows = run_gather(w, sc, 3, press(0, button="catch"))
            self.assertEqual(events(rows, "fish_caught")[0]["data"]["fish_id"], "F2")
        with Workdir() as w:
            sc = {"player": {"pos": [15, 5]}, "nodes": [], "fish": [fish("F1", [16, 5]), fish("F2", [15.5, 5])]}
            rows = run_gather(w, sc, 3, press(0, button="catch"))
            self.assertEqual(events(rows, "fish_caught")[0]["data"]["fish_id"], "F2")

    def test_ngoai_ban_kinh_khong_bat(self):
        with Workdir() as w:
            far = 5 + G["catch_radius"] + 0.5
            sc = {"player": {"pos": [15, 5]}, "nodes": [], "fish": [fish("F1", [15, far])]}
            rows = run_gather(w, sc, 3, press(0, button="catch"))
            self.assertEqual(events(rows, "fish_caught"), [])
            self.assertEqual(len(last(rows)["fish"]), 1)

    def test_o_mat_nuoc_khong_bat(self):
        with Workdir() as w:
            sc = {"player": {"pos": [15, 0]}, "nodes": [], "fish": [fish("F1", [15, 1])]}
            rows = run_gather(w, sc, 3, press(0, button="catch"))
            self.assertEqual(events(rows, "fish_caught"), [])
            self.assertEqual(last(rows)["hold"], [])

    def test_hoi_chieu_dat_dung_va_chan_dung(self):
        with Workdir() as w:
            sc = {"player": {"pos": [15, 5]}, "nodes": [],
                  "fish": [fish("F1", [15, 5], "ca_loc"), fish("F2", [15, 5], "ca_loc"),
                           fish("F3", [15, 5], "ca_loc")]}
            rows = run_gather(w, sc, CATCH_CD + 5, press(0, button="catch"))
            by_tick = {s["tick"]: s for s in snapshots(rows)}
            self.assertEqual(by_tick[1]["player"]["catch_cd_ticks"], CATCH_CD)
            # Bấm lần 2 ở bước CATCH_CD - 1: còn 1 tick hồi chiêu -> bị chặn.
            rows = run_gather(w, sc, CATCH_CD + 5, press(0, CATCH_CD - 1, button="catch"), name="a.jsonl")
            self.assertEqual([e["tick"] for e in events(rows, "fish_caught")], [1])
            # Bấm lần 2 ở bước CATCH_CD: vừa hết hồi chiêu -> bắt được (sự kiện tick CATCH_CD + 1).
            rows = run_gather(w, sc, CATCH_CD + 5, press(0, CATCH_CD, button="catch"), name="b.jsonl")
            self.assertEqual([e["tick"] for e in events(rows, "fish_caught")], [1, CATCH_CD + 1])

    def test_gio_thieu_cho_phat_hold_full_ca_o_lai_khong_hoi_chieu(self):
        with Workdir() as w:
            need = G["fish_yield"]["ca_linh"]
            sc = {"player": {"pos": [15, 5]}, "nodes": [], "fish": [fish("F1", [15, 5])],
                  "hold": ["ca_loc"] * (CAP - need + 1)}
            rows = run_gather(w, sc, 3, press(0, button="catch"))
            self.assertEqual(events(rows, "fish_caught"), [])
            self.assertEqual(len(events(rows, "hold_full")), 1)
            s = last(rows)
            self.assertEqual(len(s["fish"]), 1)
            self.assertEqual(s["hold_count"], CAP - need + 1)
            self.assertEqual(s["player"]["catch_cd_ticks"], 0)


class Determinism(unittest.TestCase):
    def test_cung_seed_cung_byte(self):
        sc = {"player": {"pos": [12, 0]}}
        inputs = frames({"tick": 0, "interact": True}, {"tick": 1, "interact": False},
                        {"tick": 2, "move": [0, 1]}, {"tick": 60, "move": [0, 0]},
                        {"tick": 61, "catch": True})
        with Workdir() as w:
            for i in (1, 2):
                run_gather(w, sc, 200, inputs, name=f"o{i}.jsonl")
            with open(w.path("o1.jsonl"), "rb") as a, open(w.path("o2.jsonl"), "rb") as b:
                self.assertEqual(a.read(), b.read())


if __name__ == "__main__":
    unittest.main()
