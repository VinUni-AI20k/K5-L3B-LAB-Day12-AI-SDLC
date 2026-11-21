"""Lát 2 gather: hái, mọc lại, bắt cá, hồi chiêu, giỏ đầy, cập bến (PRD-0 mục F/E). Hộp đen qua headless."""

import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def run_g(w, scenario, fr, ticks):
    sc = write_json(w.path("sc.json"), {"gather": {"random_fish": False, "fish": [], **scenario}})
    inp = write_json(w.path("in.json"), frames(*fr))
    code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", str(ticks), "--scenario", sc,
                             "--inputs", inp, "--out", w.path("o.jsonl"), "--snapshot-every", "1")
    assert code == 0, err
    return read_jsonl(w.path("o.jsonl"))


N = lambda i, x, **kw: {"id": i, "kind": "bong_sung", "pos": [x, 0], **kw}
F = lambda i, kind, x, d: {"id": i, "kind": kind, "pos": [x, d]}
UNDER = {"pos": [20, 5]}


class Harvest(unittest.TestCase):
    def test_hai_o_mep_ban_kinh(self):
        with Workdir() as w:
            rows = run_g(w, {"player": {"pos": [20, 0]}, "nodes": [N("N1", 22)]}, [{"tick": 0, "interact": True}], 1)
            self.assertEqual(events(rows, "gather")[0]["data"], {"node_id": "N1", "kind": "bong_sung", "amount": 1})
            snap = snapshots(rows)[-1]
            self.assertEqual(snap["hold"], ["bong_sung"])
            self.assertEqual(snap["nodes"][0]["regrow_ticks"], 1200)
            self.assertFalse(snap["nodes"][0]["ready"])

    def test_hai_duoi_nuoc_khong_co_gi(self):
        with Workdir() as w:
            rows = run_g(w, {"player": UNDER, "nodes": [N("N1", 20)]}, [{"tick": 0, "interact": True}], 1)
            self.assertEqual(events(rows, "gather"), [])

    def test_hoa_khoang_cach_chon_id_nho_va_bo_nut_chua_moc(self):
        with Workdir() as w:
            nodes = [N("N10", 21), N("N2", 19), N("N1", 20, regrow_ticks=5)]
            rows = run_g(w, {"player": {"pos": [20, 0]}, "nodes": nodes}, [{"tick": 0, "interact": True}], 1)
            self.assertEqual(events(rows, "gather")[0]["data"]["node_id"], "N2")

    def test_moc_lai_roi_hai_duoc_ngay(self):
        with Workdir() as w:
            rows = run_g(w, {"player": {"pos": [20, 0]}, "nodes": [N("N1", 20, regrow_ticks=3)]},
                         [{"tick": 2, "interact": True}], 3)
            self.assertEqual([(e["tick"], e["name"]) for e in events(rows)], [(3, "node_regrown"), (3, "gather")])

    def test_gio_day_nut_giu_nguyen(self):
        with Workdir() as w:
            rows = run_g(w, {"player": {"pos": [20, 0]}, "hold": ["ca_loc"] * 12, "nodes": [N("N1", 20)]},
                         [{"tick": 0, "interact": True}], 1)
            self.assertEqual(events(rows, "hold_full")[0]["data"],
                             {"action": "gather", "node_id": "N1", "required": 1, "free": 0})
            self.assertTrue(snapshots(rows)[-1]["nodes"][0]["ready"])
            self.assertEqual(snapshots(rows)[-1]["hold_count"], 12)


class Catch(unittest.TestCase):
    def test_bat_ca_linh_yield_3_va_xoa_dan(self):
        with Workdir() as w:
            rows = run_g(w, {"player": UNDER, "hold": ["bong_sung"], "fish": [F("F1", "ca_linh", 22, 5)]},
                         [{"tick": 0, "catch": True}], 1)
            self.assertEqual(events(rows, "fish_caught")[0]["data"], {"fish_id": "F1", "kind": "ca_linh", "yield": 3})
            snap = snapshots(rows)[-1]
            self.assertEqual(snap["hold"], ["bong_sung", "ca_linh", "ca_linh", "ca_linh"])
            self.assertEqual(snap["fish"], [])
            self.assertEqual(snap["player"]["catch_cd_ticks"], 30)

    def test_bat_o_mat_nuoc_khong_co_gi(self):
        with Workdir() as w:
            rows = run_g(w, {"player": {"pos": [20, 0]}, "fish": [F("F1", "ca_loc", 20, 1)]},
                         [{"tick": 0, "catch": True}], 1)
            self.assertEqual(events(rows), [])

    def test_hoi_chieu_dung_lai_tu_t_cong_30(self):
        with Workdir() as w:
            fish = [F("F1", "ca_loc", 20, 5), F("F2", "ca_loc", 20, 5)]
            fr = [{"tick": 0, "catch": True}, {"tick": 1, "catch": False},
                  {"tick": 28, "catch": True}, {"tick": 29, "catch": False}, {"tick": 30, "catch": True}]
            rows = run_g(w, {"player": UNDER, "fish": fish}, fr, 31)
            self.assertEqual([(e["tick"], e["data"]["fish_id"]) for e in events(rows, "fish_caught")],
                             [(1, "F1"), (31, "F2")])

    def test_khong_co_dan_trong_tam_khong_hoi_chieu(self):
        with Workdir() as w:
            rows = run_g(w, {"player": UNDER, "fish": [F("F1", "ca_loc", 30, 5)]}, [{"tick": 0, "catch": True}], 1)
            self.assertEqual(events(rows), [])
            self.assertEqual(snapshots(rows)[-1]["player"]["catch_cd_ticks"], 0)

    def test_gio_thieu_cho_giu_dan_khong_thu_dan_khac(self):
        with Workdir() as w:
            fish = [F("F1", "ca_linh", 20, 5), F("F2", "ca_loc", 21, 5)]
            rows = run_g(w, {"player": UNDER, "hold": ["ca_loc"] * 10, "fish": fish}, [{"tick": 0, "catch": True}], 1)
            self.assertEqual(events(rows, "hold_full")[0]["data"],
                             {"action": "catch", "fish_id": "F1", "required": 3, "free": 2})
            self.assertEqual(events(rows, "fish_caught"), [])
            snap = snapshots(rows)[-1]
            self.assertEqual(len(snap["fish"]), 2)
            self.assertEqual(snap["player"]["catch_cd_ticks"], 0)


class DockAfterGather(unittest.TestCase):
    def test_hai_roi_cap_ben_ghi_kho(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"player": {"pos": [7, 0]},
                                                           "nodes": [N("N1", 8)], "random_fish": False}})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}, {"tick": 1, "interact": False},
                                                       {"tick": 2, "move": [-1, 0]}, {"tick": 40, "interact": True}))
            inv = w.path("kho.json")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "100", "--scenario", sc,
                                     "--inputs", inp, "--inventory-out", inv, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            end = events(read_jsonl(w.path("o.jsonl")), "gather_end")[0]["data"]
            self.assertEqual(end, {"reason": "docked", "inventory": {"items": {"bong_sung": 1}}})


if __name__ == "__main__":
    unittest.main()
