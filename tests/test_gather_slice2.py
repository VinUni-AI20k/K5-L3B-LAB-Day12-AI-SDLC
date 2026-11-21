"""Test lát 2 (hộp đen qua headless_cmd): hái, bắt cá, cập bến, kho — PRD-0 mục E, F, G.

Preset: hold_capacity = 12, interact_radius = 2.0, catch_radius = 2.0, node_yield = 1,
regrow_s = 20 (= 1200 tick), catch_cooldown_s = 0.5 (= 30 tick), fish_yield {ca_linh: 3, ca_loc: 1},
dock_pos [2,0] bán kính 3, surface_depth = 0.5.

Ghi chú giả định (nên ghi docs/clarify.md): PRD "Thiếu chỗ phát hold_full, giữ đàn và cooldown"
được hiểu là GIỮ NGUYÊN cả đàn lẫn hồi chiêu (không đặt cooldown mới khi giỏ đầy).

Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_gather_slice2 -v
"""

import json
import unittest

from helpers import (Workdir, events, frames, read_jsonl, run_headless,
                     snapshots, write_json)
from helpers import counts, items, kinds  # v1.2 kho cá thể


def sc(block):
    """Fixture gather chuẩn: tắt cá mặc định để kiểm soát từng đàn."""
    block = dict(block)
    block.setdefault("fish", [])
    block.setdefault("random_fish", False)
    return {"gather": block}


class Harvest(unittest.TestCase):
    def test_hai_dung_nut_gan_nhat_hoa_theo_id(self):
        """Hai nút cách đều: chọn id nhỏ hơn (N1 trước N2)."""
        with Workdir() as w:
            f = write_json(w.path("sc.json"), sc({
                "player": {"pos": [11, 0.2]},
                "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [10, 0]},
                          {"id": "N2", "kind": "bong_dien_dien", "pos": [12, 0]}]}))
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", f, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            g = events(rows, "gather")
            self.assertEqual(len(g), 1, g)
            self.assertEqual(g[0]["tick"], 1)
            self.assertEqual(g[0]["data"], {"node_id": "N1", "kind": "bong_sung", "amount": 1})
            s = snapshots(rows)[-1]
            self.assertEqual(kinds(s["hold"]), ["bong_sung"])
            self.assertEqual(s["hold_count"], 1)

    def test_hai_chi_khi_o_mat_nuoc(self):
        """Underwater trong bán kính: interact không hái, không hold_full, nút giữ nguyên."""
        with Workdir() as w:
            f = write_json(w.path("sc.json"), sc({
                "player": {"pos": [10, 1.0]},
                "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [10, 0]}]}))
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", f, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(events(rows, "gather"), [])
            self.assertEqual(events(rows, "hold_full"), [])
            self.assertEqual(events(rows, "gather_end"), [])
            self.assertEqual(kinds(snapshots(rows)[-1]["hold"]), [])

    def test_hold_full_hai_gio_day(self):
        """Giỏ đầy: hold_full (required, free = 0), không gather, nút vẫn ready không mọc lại."""
        with Workdir() as w:
            f = write_json(w.path("sc.json"), sc({
                "player": {"pos": [10, 0.3]},
                "hold": items(*["ca_loc"] * 12),
                "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [10, 0]}]}))
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", f, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(events(rows, "gather"), [])
            hf = events(rows, "hold_full")
            self.assertEqual(len(hf), 1, hf)
            self.assertEqual(hf[0]["data"], {"action": "gather", "node_id": "N1",
                                             "required": 1, "free": 0})
            s = snapshots(rows)[-1]
            self.assertEqual(s["hold_count"], 12)
            self.assertEqual([n for n in s["nodes"] if n["id"] == "N1"][0]["ready"], True,
                             "nút giữ nguyên, không đặt regrow")

    def test_nut_moc_lai_dung_tick_va_hai_duoc_ngay(self):
        """Hái tick 1 → regrow 1200 tick → node_regrown tick 1201 (= 1 + regrow_s × 60)."""
        with Workdir() as w:
            f = write_json(w.path("sc.json"), sc({
                "player": {"pos": [10, 0.3]},
                "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [10, 0]}]}))
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1203",
                                     "--scenario", f, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(events(rows, "gather")[0]["tick"], 1)
            rg = events(rows, "node_regrown")
            self.assertEqual(len(rg), 1, rg)
            self.assertEqual(rg[0]["tick"], 1201)
            s = {r["tick"]: r for r in snapshots(rows)}
            n10 = [n for n in s[10]["nodes"] if n["id"] == "N1"][0]
            self.assertEqual(n10["ready"], False)
            self.assertEqual(n10["regrow_ticks"], 1191)  # 1200 - 9 bước đã trừ
            n1203 = [n for n in s[1203]["nodes"] if n["id"] == "N1"][0]
            self.assertEqual(n1203["ready"], True)


class Catch(unittest.TestCase):
    def test_bat_ca_yield_huy_dan_va_hoi_chieu(self):
        """Bắt ca_linh: yield 3 vào giỏ, đàn biến mất, cooldown 30 tick chặn cú tiếp theo."""
        with Workdir() as w:
            f = write_json(w.path("sc.json"), sc({
                "player": {"pos": [15, 5.5]},
                "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15, 5]}]}))
            inp = write_json(w.path("in.json"), frames({"tick": 0, "catch": True},
                                                       {"tick": 1, "catch": False},
                                                       {"tick": 2, "catch": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "3",
                                     "--scenario", f, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            fc = events(rows, "fish_caught")
            self.assertEqual(len(fc), 1, fc)
            self.assertEqual(fc[0]["tick"], 1)
            self.assertEqual(fc[0]["data"], {"fish_id": "F1", "kind": "ca_linh", "yield": 3})
            s = snapshots(rows)[-1]
            self.assertEqual(kinds(s["hold"]), ["ca_linh"] * 3)
            self.assertEqual(s["fish"], [], "đàn bị xóa sau khi bắt")
            self.assertEqual(s["player"]["catch_cd_ticks"], 28)  # 30 - 2 bước đã trừ

    def test_bat_chi_khi_duoi_nuoc(self):
        """Đứng ở mặt nước (d ≤ 0.5): catch không bắt dù đàn trong bán kính, không hồi chiêu."""
        with Workdir() as w:
            f = write_json(w.path("sc.json"), sc({
                "player": {"pos": [15, 0.3]},
                "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15, 0.8]}]}))
            inp = write_json(w.path("in.json"), frames({"tick": 0, "catch": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", f, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(events(rows, "fish_caught"), [])
            self.assertEqual(events(rows, "hold_full"), [])
            s = snapshots(rows)[-1]
            self.assertEqual(len(s["fish"]), 1)
            self.assertEqual(s["player"]["catch_cd_ticks"], 0)

    def test_hold_full_catch_giu_dan_va_cooldown(self):
        """Giỏ thiếu chỗ cho yield: hold_full action catch, giữ đàn, giữ cooldown, KHÔNG thử đàn khác."""
        with Workdir() as w:
            f = write_json(w.path("sc.json"), sc({
                "player": {"pos": [15, 5]},
                "hold": items(*["ca_loc"] * 10),  # free = 2 < yield ca_linh = 3
                "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15, 5]},
                         {"id": "F2", "kind": "ca_loc", "pos": [18, 5]}]}))
            inp = write_json(w.path("in.json"), frames({"tick": 0, "catch": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", f, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(events(rows, "fish_caught"), [])
            hf = events(rows, "hold_full")
            self.assertEqual(len(hf), 1, hf)
            self.assertEqual(hf[0]["data"], {"action": "catch", "fish_id": "F1",
                                             "required": 3, "free": 2})
            s = snapshots(rows)[-1]
            self.assertEqual(sorted(x["id"] for x in s["fish"]), ["F1", "F2"],
                             "giữ đàn, không thử đàn khác")
            self.assertEqual(s["player"]["catch_cd_ticks"], 0, "cooldown giữ nguyên")

    def test_bat_dung_mep_ban_kinh(self):
        """Đúng mép catch_radius (dist = 2.0) vẫn bắt được."""
        with Workdir() as w:
            f = write_json(w.path("sc.json"), sc({
                "player": {"pos": [15, 5]},
                "fish": [{"id": "F1", "kind": "ca_loc", "pos": [17, 5]}]}))
            inp = write_json(w.path("in.json"), frames({"tick": 0, "catch": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", f, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            fc = events(read_jsonl(w.path("o.jsonl")), "fish_caught")
            self.assertEqual(len(fc), 1, fc)
            self.assertEqual(fc[0]["data"]["yield"], 1)


class Dock(unittest.TestCase):
    def test_ben_uu_tien_truoc_hai(self):
        """Nút nằm trong vùng bến: interact ưu tiên cập bến, không hái."""
        with Workdir() as w:
            f = write_json(w.path("sc.json"), sc({
                "player": {"pos": [3, 0]},
                "hold": items(*["ca_loc", "bong_sung", "bong_sung"]),
                "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [3, 0]}]}))
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", f, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(events(rows, "gather"), [])
            end = events(rows, "gather_end")
            self.assertEqual(len(end), 1)
            self.assertEqual(end[0]["data"]["reason"], "docked")
            self.assertEqual(counts(end[0]["data"]["inventory"]), {"items": {"bong_sung": 2, "ca_loc": 1}})

    def test_dung_mep_ben_van_docked(self):
        """Khoảng cách tới tâm bến đúng bằng dock_radius (3.0) vẫn docked."""
        with Workdir() as w:
            f = write_json(w.path("sc.json"), sc({"player": {"pos": [5, 0]}}))
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", f, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            end = events(read_jsonl(w.path("o.jsonl")), "gather_end")
            self.assertEqual(len(end), 1)
            self.assertEqual(end[0]["data"]["reason"], "docked")


class TimeEnd(unittest.TestCase):
    def test_het_gio_giu_gio_sau_hai_buoc_cuoi(self):
        """Hái hợp lệ ở bước cuối vẫn vào kho trước khi kết thúc time."""
        with Workdir() as w:
            f = write_json(w.path("sc.json"), sc({
                "player": {"pos": [10, 0.3]},
                "time_left_ticks": 1,
                "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [10, 0]}]}))
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "5",
                                     "--scenario", f, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(len(events(rows, "gather")), 1, "hái ở bước cuối vẫn hợp lệ")
            ends = events(rows, "gather_end")
            self.assertEqual(len(ends), 1)
            self.assertEqual({**ends[0]["data"], "inventory": counts(ends[0]["data"]["inventory"])}, {"reason": "time", "inventory": {"items": {"bong_sung": 1}}})
            self.assertEqual(rows[-1]["reason"], "time")


if __name__ == "__main__":
    unittest.main()
