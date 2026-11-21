"""Lát 2 (BLong1501): hái, bắt cá, cập bến, hết giờ, file kho — AC-P1-20..23.

Test hộp đen qua headless_cmd (giống smoke test). Chạy:
    PYTHONPATH=tests:. python3 -m unittest tests.test_gather_slice2 -v
"""

import json
import os
import unittest

from helpers import hold_items, kinds_of, counts_of, Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def tuning_gather():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]["gather"]


def run_gather(w, block, inputs, ticks=1, inventory_out=None):
    sc = write_json(w.path("sc.json"), {"gather": block})
    inp = write_json(w.path("in.json"), frames(*inputs))
    args = ["--mode", "gather", "--seed", "1", "--ticks", str(ticks), "--scenario", sc, "--inputs", inp,
            "--out", w.path("g.jsonl")]
    if inventory_out:
        args += ["--inventory-out", inventory_out]
    code, err = run_headless(*args)
    return code, err, (read_jsonl(w.path("g.jsonl")) if code == 0 else [])


def names(rows):
    return [r["name"] for r in events(rows)]


class Harvest(unittest.TestCase):
    """AC-P1-20: interact ngoài bến chỉ hái ở mặt nước, nút ready gần nhất, hòa theo id."""

    def test_hai_dung_mep_ban_kinh(self):
        t = tuning_gather()
        with Workdir() as w:
            code, err, rows = run_gather(w, {
                "player": {"pos": [20, 0]}, "fish": [],
                "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [20 + t["interact_radius"], 0]}],
            }, [{"tick": 0, "interact": True}])
            self.assertEqual(code, 0, err)
            ev = events(rows, "gather")
            self.assertEqual(len(ev), 1)
            self.assertEqual(ev[0]["tick"], 1)
            self.assertEqual(ev[0]["data"], {"node_id": "N1", "kind": "bong_dien_dien", "amount": t["node_yield"]})
            s = snapshots(rows)[-1]
            self.assertEqual(kinds_of(s["hold"]), ["bong_dien_dien"] * t["node_yield"])  # v1.2: mảng cá thể
            self.assertEqual(s["nodes"][0]["regrow_ticks"], int(round(t["regrow_s"] * 60)))
            self.assertFalse(s["nodes"][0]["ready"])

    def test_gan_nhat_hoa_theo_id(self):
        with Workdir() as w:
            code, err, rows = run_gather(w, {
                "player": {"pos": [20, 0]}, "fish": [],
                "nodes": [{"id": "N10", "kind": "bong_sung", "pos": [21, 0]},
                          {"id": "N2", "kind": "bong_dien_dien", "pos": [19, 0]},
                          {"id": "N3", "kind": "bong_sung", "pos": [20.5, 0], "regrow_ticks": 50}],
            }, [{"tick": 0, "interact": True}])
            self.assertEqual(code, 0, err)
            ev = events(rows, "gather")
            self.assertEqual([e["data"]["node_id"] for e in ev], ["N2"])  # N3 gần hơn nhưng chưa ready

    def test_ngoai_tam_hoac_duoi_nuoc_khong_hai(self):
        t = tuning_gather()
        for pos, node_x in (([20, 0], 20 + t["interact_radius"] + 0.01), ([20, 1], 20)):
            with Workdir() as w:
                code, err, rows = run_gather(w, {
                    "player": {"pos": pos}, "fish": [],
                    "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [node_x, 0]}],
                }, [{"tick": 0, "interact": True}])
                self.assertEqual(code, 0, err)
                self.assertEqual(events(rows, "gather"), [], pos)
                self.assertEqual(snapshots(rows)[-1]["hold"], [])

    def test_hold_full_khi_hai(self):
        t = tuning_gather()
        cap = t["hold_capacity"]
        with Workdir() as w:
            code, err, rows = run_gather(w, {
                "player": {"pos": [20, 0]}, "fish": [], "hold": hold_items(*["ca_loc"] * cap),
                "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [21, 0]}],
            }, [{"tick": 0, "interact": True}])
            self.assertEqual(code, 0, err)
            self.assertEqual(names(rows), ["hold_full"])
            self.assertEqual(events(rows, "hold_full")[0]["data"],
                             {"action": "gather", "node_id": "N1", "required": t["node_yield"], "free": 0})
            s = snapshots(rows)[-1]
            self.assertEqual(s["nodes"][0]["regrow_ticks"], 0)  # nút giữ nguyên
            self.assertEqual(s["hold_count"], cap)

    def test_node_regrown_roi_hai_ngay(self):
        with Workdir() as w:
            code, err, rows = run_gather(w, {
                "player": {"pos": [20, 0]}, "fish": [],
                "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [21, 0], "regrow_ticks": 1}],
            }, [{"tick": 0, "interact": True}])
            self.assertEqual(code, 0, err)
            self.assertEqual(names(rows), ["node_regrown", "gather"])
            self.assertEqual(events(rows, "node_regrown")[0]["data"], {"node_id": "N1"})

    def test_ben_xet_truoc_hai(self):
        t = tuning_gather()
        dock = t["dock_pos"]
        with Workdir() as w:
            code, err, rows = run_gather(w, {
                "player": {"pos": [dock[0] + t["dock_radius"], 0]}, "fish": [],
                "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [dock[0] + t["dock_radius"], 0]}],
            }, [{"tick": 0, "interact": True}])
            self.assertEqual(code, 0, err)
            self.assertEqual(names(rows), ["gather_end"])
            self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "docked")


class Catch(unittest.TestCase):
    """AC-P1-21: catch khi hết hồi và dưới nước, đúng một đàn gần nhất, hold_full không thử đàn khác."""

    def test_bat_ca_thanh_cong(self):
        t = tuning_gather()
        y = t["fish_yield"]["ca_linh"]
        with Workdir() as w:
            code, err, rows = run_gather(w, {
                "player": {"pos": [20, 5]}, "nodes": [],
                "fish": [{"id": "F1", "kind": "ca_linh", "pos": [20 + t["catch_radius"], 5]}],
            }, [{"tick": 0, "catch": True}])
            self.assertEqual(code, 0, err)
            ev = events(rows, "fish_caught")
            self.assertEqual([e["data"] for e in ev], [{"fish_id": "F1", "kind": "ca_linh", "yield": y}])
            s = snapshots(rows)[-1]
            self.assertEqual(kinds_of(s["hold"]), ["ca_linh"] * y)  # v1.2: mảng cá thể
            self.assertEqual(s["fish"], [])
            self.assertEqual(s["player"]["catch_cd_ticks"], int(round(t["catch_cooldown_s"] * 60)))

    def test_gan_nhat_hoa_theo_id(self):
        with Workdir() as w:
            code, err, rows = run_gather(w, {
                "player": {"pos": [20, 5]}, "nodes": [],
                "fish": [{"id": "F10", "kind": "ca_linh", "pos": [21, 5]},
                         {"id": "F2", "kind": "ca_loc", "pos": [19, 5]}],
            }, [{"tick": 0, "catch": True}])
            self.assertEqual(code, 0, err)
            self.assertEqual([e["data"]["fish_id"] for e in events(rows, "fish_caught")], ["F2"])
            self.assertEqual([f["id"] for f in snapshots(rows)[-1]["fish"]], ["F10"])

    def test_hoi_chieu(self):
        cd = int(round(tuning_gather()["catch_cooldown_s"] * 60))
        with Workdir() as w:
            code, err, rows = run_gather(w, {
                "player": {"pos": [20, 5]}, "nodes": [], "random_fish": False,  # v1.1 cá tự bơi: giữ đứng yên để test hồi chiêu
                "fish": [{"id": "F1", "kind": "ca_loc", "pos": [21, 5]},
                         {"id": "F2", "kind": "ca_loc", "pos": [19.5, 5]}],
            }, [{"tick": 0, "catch": True}, {"tick": 1, "catch": False},
                {"tick": cd - 1, "catch": True}, {"tick": cd, "catch": False},  # còn hồi: bỏ qua
                {"tick": cd + 1, "catch": True}], ticks=cd + 2)
            self.assertEqual(code, 0, err)
            ev = events(rows, "fish_caught")
            self.assertEqual([(e["tick"], e["data"]["fish_id"]) for e in ev], [(1, "F2"), (cd + 2, "F1")])

    def test_dung_luc_het_hoi_bat_duoc(self):
        """Cooldown L đặt ở tick t dùng lại từ t+L."""
        cd = int(round(tuning_gather()["catch_cooldown_s"] * 60))
        with Workdir() as w:
            code, err, rows = run_gather(w, {
                "player": {"pos": [20, 5]}, "nodes": [], "random_fish": False,  # v1.1 cá tự bơi: giữ đứng yên để test hồi chiêu
                "fish": [{"id": "F1", "kind": "ca_loc", "pos": [21, 5]},
                         {"id": "F2", "kind": "ca_loc", "pos": [19.5, 5]}],
            }, [{"tick": 0, "catch": True}, {"tick": 1, "catch": False}, {"tick": cd, "catch": True}], ticks=cd + 1)
            self.assertEqual(code, 0, err)
            self.assertEqual([e["tick"] for e in events(rows, "fish_caught")], [1, cd + 1])

    def test_hold_full_khong_thu_dan_khac(self):
        t = tuning_gather()
        cap, y = t["hold_capacity"], t["fish_yield"]["ca_linh"]
        free = y - 1
        with Workdir() as w:
            code, err, rows = run_gather(w, {
                "player": {"pos": [20, 5]}, "nodes": [], "hold": hold_items(*["bong_sung"] * (cap - free)),
                "fish": [{"id": "F1", "kind": "ca_linh", "pos": [20.5, 5]},
                         {"id": "F2", "kind": "ca_loc", "pos": [21.5, 5]}],
            }, [{"tick": 0, "catch": True}])
            self.assertEqual(code, 0, err)
            self.assertEqual(names(rows), ["hold_full"])
            self.assertEqual(events(rows, "hold_full")[0]["data"],
                             {"action": "catch", "fish_id": "F1", "required": y, "free": free})
            s = snapshots(rows)[-1]
            self.assertEqual([f["id"] for f in s["fish"]], ["F1", "F2"])
            self.assertEqual(s["player"]["catch_cd_ticks"], 0)

    def test_mat_nuoc_hoac_ngoai_tam_khong_bat(self):
        t = tuning_gather()
        cases = (([20, 0.5], [21, 1.5]),                     # ở mặt nước (d ≤ surface_depth), cá trong tầm
                 ([20, 5], [20 + t["catch_radius"] + 0.01, 5]))  # ngoài tầm
        for pos, fish_pos in cases:
            with Workdir() as w:
                code, err, rows = run_gather(w, {
                    "player": {"pos": pos}, "nodes": [],
                    "fish": [{"id": "F1", "kind": "ca_loc", "pos": fish_pos}],
                }, [{"tick": 0, "catch": True}])
                self.assertEqual(code, 0, err)
                self.assertEqual([n for n in names(rows) if n in ("fish_caught", "hold_full")], [], pos)
                self.assertEqual(snapshots(rows)[-1]["player"]["catch_cd_ticks"], 0)


class EndAndInventory(unittest.TestCase):
    """AC-P1-22/23: hết giờ ở mọi độ sâu, hành động ở bước cuối vẫn vào kho, file kho khớp gather_end."""

    def test_hai_o_buoc_cuoi_van_vao_kho(self):
        with Workdir() as w:
            inv = w.path("kho.json")
            code, err, rows = run_gather(w, {
                "player": {"pos": [20, 0]}, "fish": [], "hold": hold_items("ca_loc"), "time_left_ticks": 1,
                "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [21, 0]}],
            }, [{"tick": 0, "interact": True}], ticks=5, inventory_out=inv)
            self.assertEqual(code, 0, err)
            self.assertEqual(names(rows), ["gather", "gather_end"])
            end_ev = events(rows, "gather_end")[0]["data"]
            self.assertEqual(end_ev["reason"], "time")  # v1.2: kho cá thể, so theo kind
            self.assertEqual(counts_of(end_ev["inventory"]["items"]), {"bong_sung": 1, "ca_loc": 1})
            self.assertEqual(rows[-1]["reason"], "time")
            with open(inv, encoding="utf-8") as f:  # v1.2: file đủ chính xác, JSONL làm tròn 3 chữ số (±0.01)
                file_items = json.load(f)["items"]
            ev_items = end_ev["inventory"]["items"]
            self.assertEqual([(i["id"], i["kind"]) for i in file_items], [(i["id"], i["kind"]) for i in ev_items])
            for a, b in zip(file_items, ev_items):
                self.assertAlmostEqual(a["fresh"], b["fresh"], delta=0.01)

    def test_bat_ca_o_buoc_cuoi_duoi_nuoc_van_vao_kho(self):
        y = tuning_gather()["fish_yield"]["ca_loc"]
        with Workdir() as w:
            inv = w.path("kho.json")
            code, err, rows = run_gather(w, {
                "player": {"pos": [50, 10]}, "nodes": [], "time_left_ticks": 1,
                "fish": [{"id": "F1", "kind": "ca_loc", "pos": [51, 10]}],
            }, [{"tick": 0, "catch": True}], ticks=5, inventory_out=inv)
            self.assertEqual(code, 0, err)
            self.assertEqual(names(rows), ["fish_caught", "gather_end"])
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(counts_of(json.load(f)["items"]), {"ca_loc": y})  # v1.2: kho cá thể

    def test_docked_ghi_kho_dung_noi_dung(self):
        t = tuning_gather()
        with Workdir() as w:
            inv = w.path("kho.json")
            code, err, rows = run_gather(w, {"hold": hold_items("bong_sung", "ca_linh", "bong_sung")},
                                         [{"tick": 0, "interact": True}], ticks=10, inventory_out=inv)
            self.assertEqual(code, 0, err)
            self.assertEqual(rows[-1]["reason"], "docked")
            with open(inv, "rb") as f:  # v1.2: kho cá thể, sắp id, một dòng gọn
                raw = f.read()
            self.assertTrue(raw.startswith(b'{"items":[{"id":"I1","kind":"bong_sung","fresh":') and raw.endswith(b"]}\n"))
            items = json.loads(raw)["items"]
            self.assertEqual([(it["id"], it["kind"]) for it in items],
                             [("I1", "bong_sung"), ("I2", "ca_linh"), ("I3", "bong_sung")])
            self.assertEqual(t["start_pos"], snapshots(rows)[0]["player"]["pos"])

    def test_cham_ticks_truoc_khi_xong_khong_ghi(self):
        with Workdir() as w:
            inv = w.path("kho.json")
            code, err, rows = run_gather(w, {"player": {"pos": [50, 0]}}, [{"tick": 0, "move": [1, 0]}],
                                         ticks=5, inventory_out=inv)
            self.assertEqual(code, 0, err)
            self.assertEqual(rows[-1]["reason"], "tick_limit")
            self.assertFalse(os.path.exists(inv))


if __name__ == "__main__":
    unittest.main()
