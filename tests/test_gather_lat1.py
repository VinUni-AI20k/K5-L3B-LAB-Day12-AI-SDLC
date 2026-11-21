"""Test lát 1 (A): dive/surface, oxy, ngạt, Máu, ngất — PRD-0 mục F (Gather bước 2) và mục E (sự kiện).
Kiểu hộp đen: chỉ chạy headless_cmd và đọc JSONL/file kho, số liệu đọc từ game.contract.json.

Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_gather_lat1 -v
"""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def tuning_gather():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]["gather"]


G = tuning_gather()
OXY_MAX = int(round(G["oxygen_max_s"] * 60))
REFILL = G["oxygen_refill_per_tick"]
CHOKE = G["choke_interval_ticks"]
DEEP = [50, 10]  # chắc chắn dưới nước, không có cá/nút gần

def items(*kinds, start=1):
    """Fixture v1.2: cá thể I<start>, I<start+1>, ... fresh 100 theo thứ tự vào giỏ."""
    return [{"id": f"I{start + i}", "kind": k, "fresh": 100} for i, k in enumerate(kinds)]


def ik(lst):
    """(id, kind) của danh sách cá thể public: so không phụ thuộc fresh (giỏ hao theo tick)."""
    return [(x["id"], x["kind"]) for x in lst]



def run_gather(block, ticks, inputs=None, inventory_out=False, every=1):
    """Chạy gather với scenario `block` (cá mặc định tắt). Trả (rows, nội dung file kho hoặc None, bytes JSONL)."""
    with Workdir() as w:
        sc = write_json(w.path("sc.json"), {"gather": {"random_fish": False, **block}})
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


class Oxygen(unittest.TestCase):
    def test_duoi_nuoc_tru_1_moi_tick(self):
        rows, _, _ = run_gather({"player": {"pos": DEEP}}, 10)
        self.assertEqual(snap_at(rows, 10)["player"]["oxygen_ticks"], OXY_MAX - 10)
        self.assertFalse(snap_at(rows, 10)["player"]["at_surface"])

    def test_mat_nuoc_hoi_oxy_va_kep_toi_da(self):
        rows, _, _ = run_gather({"player": {"pos": [20, 0], "oxygen_ticks": 100}}, 10)
        self.assertEqual(snap_at(rows, 10)["player"]["oxygen_ticks"], 100 + 10 * REFILL)
        rows, _, _ = run_gather({"player": {"pos": [20, 0], "oxygen_ticks": OXY_MAX - 1}}, 1)
        self.assertEqual(snap_at(rows, 1)["player"]["oxygen_ticks"], OXY_MAX)

    def test_oxygen_empty_dung_tick_va_mot_lan(self):
        rows, _, _ = run_gather({"player": {"pos": DEEP, "oxygen_ticks": 3}}, 20)
        ev = events(rows, "oxygen_empty")
        self.assertEqual([e["tick"] for e in ev], [3])
        self.assertEqual(ev[0]["data"], {"oxygen_ticks": 0})
        self.assertEqual(snap_at(rows, 20)["player"]["oxygen_ticks"], 0)

    def test_bat_dau_oxy_0_khong_phat_oxygen_empty(self):
        rows, _, _ = run_gather({"player": {"pos": DEEP, "oxygen_ticks": 0}}, 5)
        self.assertEqual(events(rows, "oxygen_empty"), [])


class Choke(unittest.TestCase):
    def test_ngat_lan_dau_o_t_cong_59_roi_moi_60_tick(self):
        """Chạm oxy 0 ở t = 1 (bắt đầu với 1 tick oxy), dưới nước liên tục -> choke ở 60 và 120."""
        rows, _, _ = run_gather({"player": {"pos": DEEP, "oxygen_ticks": 1}}, 130)
        self.assertEqual(events(rows, "oxygen_empty")[0]["tick"], 1)
        ch = events(rows, "choke")
        self.assertEqual([e["tick"] for e in ch], [1 + CHOKE - 1, 1 + 2 * CHOKE - 1])
        self.assertEqual([e["data"]["hp"] for e in ch], [G["hp_max"] - 1, G["hp_max"] - 2])
        self.assertEqual(snap_at(rows, 130)["player"]["hp"], G["hp_max"] - 2)

    def test_dem_ngat_tang_tung_tick_va_reset_sau_choke(self):
        rows, _, _ = run_gather({"player": {"pos": DEEP, "oxygen_ticks": 1}}, 62)
        self.assertEqual(snap_at(rows, 1)["player"]["zero_oxy_ticks"], 1)
        self.assertEqual(snap_at(rows, 59)["player"]["zero_oxy_ticks"], CHOKE - 1)
        self.assertEqual(snap_at(rows, 60)["player"]["zero_oxy_ticks"], 0)
        self.assertEqual(snap_at(rows, 62)["player"]["zero_oxy_ticks"], 2)

    def test_noi_len_dung_buoc_dang_le_ngat_thi_khong_ngat(self):
        start = {"pos": [20, 0.55], "oxygen_ticks": 0, "zero_oxy_ticks": CHOKE - 1}
        # đối chứng: đứng yên dưới nước -> ngạt ngay bước 1
        rows, _, _ = run_gather({"player": start}, 1)
        self.assertEqual([e["tick"] for e in events(rows, "choke")], [1])
        # bơi lên với vận tốc sẵn có: cuối bước 1 đã ở mặt nước -> hồi oxy, không ngạt
        rows, _, _ = run_gather({"player": {**start, "vel": [0, -G["swim_speed"]]}}, 1,
                                inputs=frames({"tick": 0, "move": [0, -1]}))
        self.assertEqual(events(rows, "choke"), [])
        self.assertEqual([e["tick"] for e in events(rows, "surface")], [1])
        p = snap_at(rows, 1)["player"]
        self.assertTrue(p["at_surface"])
        self.assertEqual(p["oxygen_ticks"], REFILL)
        self.assertEqual(p["zero_oxy_ticks"], 0)
        self.assertEqual(p["hp"], G["hp_max"])


class Faint(unittest.TestCase):
    def test_mau_ve_0_ngat_mat_gio_lifo_kho_rong(self):
        hold = items("ca_loc", "bong_sung", "ca_linh")  # v1.2: giỏ là cá thể
        rows, inv, _ = run_gather({"player": {"pos": DEEP, "hp": 1, "oxygen_ticks": 0, "zero_oxy_ticks": CHOKE - 1},
                                   "hold": hold}, 100, inventory_out=True)
        names = [r["name"] for r in events(rows)]
        self.assertEqual(names, ["choke", "faint", "gather_end"])
        self.assertTrue(all(e["tick"] == 1 for e in events(rows)))
        self.assertEqual(events(rows, "choke")[0]["data"], {"hp": 0})
        faint = events(rows, "faint")[0]["data"]
        self.assertEqual((faint["cause"], faint["hp"]), ("choke", 0))
        self.assertEqual(ik(faint["lost"]), ik(list(reversed(hold))))  # LIFO: I3, I2, I1
        end_ev = events(rows, "gather_end")[0]["data"]
        self.assertEqual(end_ev, {"reason": "fainted", "inventory": {"items": []}})
        last = snapshots(rows)[-1]
        self.assertEqual((last["tick"], last["state"], last["hold"], last["player"]["hp"]), (1, "finished", [], 0))
        self.assertEqual(rows[-1]["type"], "end")
        self.assertEqual((rows[-1]["reason"], rows[-1]["ticks"]), ("fainted", 1))
        self.assertEqual(inv, {"items": []})  # v1.2: kho rỗng là mảng rỗng

    def test_ngat_truoc_ca_cap_ben(self):
        """Ngất xét trước interact: E trong bến ở đúng bước ngất vẫn là fainted."""
        rows, _, _ = run_gather({"player": {"pos": [2, 1], "hp": 1, "oxygen_ticks": 0, "zero_oxy_ticks": CHOKE - 1},
                                 "hold": items("ca_loc")}, 5, inputs=frames({"tick": 0, "interact": True}))
        self.assertEqual(rows[-1]["reason"], "fainted")
        self.assertEqual(events(rows, "gather_end")[0]["data"]["inventory"], {"items": []})


class DiveSurface(unittest.TestCase):
    def test_dive_roi_surface_moi_lan_doi_phia_mot_su_kien(self):
        rows, _, _ = run_gather({"player": {"pos": [20, 0]}}, 120,
                                inputs=frames({"tick": 0, "move": [0, 1]}, {"tick": 30, "move": [0, -1]}))
        dives, surfs = events(rows, "dive"), events(rows, "surface")
        self.assertEqual(len(dives), 1)
        self.assertEqual(len(surfs), 1)
        self.assertGreater(dives[0]["data"]["pos"][1], G["surface_depth"])
        self.assertLessEqual(surfs[0]["data"]["pos"][1], G["surface_depth"])
        self.assertLess(dives[0]["tick"], surfs[0]["tick"])
        # pos trong event là vị trí sau di chuyển của đúng tick đó
        s = {r["tick"]: r for r in snapshots(rows)}
        self.assertEqual(dives[0]["data"]["pos"], s[dives[0]["tick"]]["player"]["pos"])

    def test_o_yen_mot_phia_khong_phat_su_kien(self):
        for pos in ([20, 0], DEEP):
            rows, _, _ = run_gather({"player": {"pos": pos}}, 30)
            self.assertEqual(events(rows, "dive") + events(rows, "surface"), [], pos)

    def test_tat_dinh_tung_byte_khi_co_ngat(self):
        outs = []
        for _ in range(2):
            _, _, raw = run_gather({"player": {"pos": DEEP, "oxygen_ticks": 5}}, 200, every=7)
            outs.append(raw)
        self.assertEqual(outs[0], outs[1])


if __name__ == "__main__":
    unittest.main()
