"""Test lát 1 P2 (hộp đen qua headless_cmd): cá bơi, phản xạ mép, đổi hướng, sinh đàn —
PRD v1.1 (TICKET-02) mục 1.1 và thứ tự xử lý mục 4.5.

Preset: fish_speed = 1.5 (0.025 m/tick), fish_x = [4, 96], fish_turn_ticks = 120,
fish_spawn_ticks = 360, fish_max = 12, fish_spawn_clearance = 1,
dải sâu: ca_linh [3,12], ca_loc [8,20], ca_keo [22,28].

Lưu ý fixture (v1.1 mục D): khai `fish` khi random_fish bật (mặc định) thì THAY đàn ban đầu
và VẪN bơi/sinh; random_fish:false tắt bơi + sinh, cá fixture đứng yên.

Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_gather_fish -v
"""

import json
import unittest

from helpers import (Workdir, close, events, frames, read_jsonl, run_headless,
                     snapshots, write_json)
from helpers import counts, items, kinds  # v1.2 kho cá thể


def contract_gather():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]["gather"]


def sc(block):
    return {"gather": block}


class Swim(unittest.TestCase):
    def test_ca_boi_dung_toc_do_va_huong(self):
        """Đàn heading 0 bơi +x đúng fish_speed: 60 tick đi được 1.5 m, độ sâu giữ nguyên."""
        with Workdir() as w:
            f = write_json(w.path("sc.json"), sc({
                "fish": [{"id": "F1", "kind": "ca_linh", "pos": [10, 10], "heading_deg": 0}]}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "60",
                                     "--scenario", f, "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            s = {r["tick"]: r for r in snapshots(read_jsonl(w.path("o.jsonl")))}
            self.assertTrue(close(s[60]["fish"][0]["pos"][0], 11.5, 0.01), s[60]["fish"])
            self.assertTrue(close(s[60]["fish"][0]["pos"][1], 10, 0.01))
            self.assertTrue(close(s[60]["fish"][0]["heading_deg"], 0, 0.01))

    def test_doi_huong_dung_buoc_boi_thu_120(self):
        """Bước bơi thứ 120 đổi hướng theo seed TRƯỚC khi di chuyển: tick 119 giữ hướng cũ."""
        with Workdir() as w:
            f = write_json(w.path("sc.json"), sc({
                "fish": [{"id": "F1", "kind": "ca_linh", "pos": [10, 10], "heading_deg": 0}]}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "121",
                                     "--scenario", f, "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            s = {r["tick"]: r for r in snapshots(read_jsonl(w.path("o.jsonl")))}
            self.assertTrue(close(s[119]["fish"][0]["heading_deg"], 0, 0.01), s[119]["fish"])
            self.assertTrue(close(s[119]["fish"][0]["pos"][0], 12.975, 0.01), s[119]["fish"])
            self.assertGreater(abs(s[120]["fish"][0]["heading_deg"]), 0.01, s[120]["fish"])

    def test_phan_xa_mep_x(self):
        """Bơi đụng mép x = 96: phản xạ phần còn lại, đảo thành phần ngang (heading ~180°)."""
        with Workdir() as w:
            f = write_json(w.path("sc.json"), sc({
                "fish": [{"id": "F1", "kind": "ca_linh", "pos": [95.5, 10], "heading_deg": 0}]}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "30",
                                     "--scenario", f, "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            s = {r["tick"]: r for r in snapshots(rows)}
            for snap in s.values():
                self.assertLessEqual(snap["fish"][0]["pos"][0], 96.000001, snap["tick"])
            self.assertTrue(close(s[30]["fish"][0]["heading_deg"], 180, 1.0), s[30]["fish"])
            self.assertLess(s[30]["fish"][0]["pos"][0], 96.0, "sau phản xạ bơi ngược vào trong")

    def test_phan_xa_dai_sau_theo_loai(self):
        """ca_linh (dải [3,12]) bơi xuống đụng d = 12: phản xạ, heading đảo ~270° (bơi lên)."""
        with Workdir() as w:
            f = write_json(w.path("sc.json"), sc({
                "fish": [{"id": "F1", "kind": "ca_linh", "pos": [10, 11.9], "heading_deg": 90}]}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "10",
                                     "--scenario", f, "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            s = {r["tick"]: r for r in snapshots(read_jsonl(w.path("o.jsonl")))}
            for snap in s.values():
                self.assertLessEqual(snap["fish"][0]["pos"][1], 12.000001, snap["tick"])
            self.assertTrue(close(s[10]["fish"][0]["heading_deg"], 270, 1.0), s[10]["fish"])


class Spawn(unittest.TestCase):
    def test_sinh_dung_lich_360_va_clearance(self):
        """phase_tick = 360: đúng 1 đàn sinh ra, id nối họ (F9), điểm thuộc preset và
        cách mọi đàn đang sống > 1 m."""
        with Workdir() as w:
            g = contract_gather()
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "361",
                                     "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            sp = events(rows, "fish_spawned")
            self.assertEqual(len(sp), 1, sp)
            self.assertEqual(sp[0]["tick"], 360, sp)
            data = sp[0]["data"]
            self.assertEqual(data["id"], "F9", "id nối sau hậu tố lớn nhất đã nạp")
            self.assertIn(data["kind"], g["fish_weights"])
            self.assertIn(data["pos"], [[float(sx), float(sd)]
                                        for sx in g["fish_spawn_x"]
                                        for sd in g["fish_spawn_depths"][data["kind"]]])
            s = {r["tick"]: r for r in snapshots(rows)}
            others = [x["pos"] for x in s[360]["fish"] if x["id"] != "F9"]
            for p in others:
                self.assertGreater(((data["pos"][0] - p[0]) ** 2 + (data["pos"][1] - p[1]) ** 2) ** 0.5, 1.0)

    def test_tran_12_dan_thi_khong_sinh_them(self):
        """Sinh đủ tới fish_max = 12 rồi dừng: tổng 4 lần sinh (360·k), tick 1800 không sinh."""
        with Workdir() as w:
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1802",
                                     "--snapshot-every", "360", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            sp = events(rows, "fish_spawned")
            self.assertEqual(len(sp), 4, [e["tick"] for e in sp])
            self.assertEqual([e["tick"] for e in sp], [360, 720, 1080, 1440])
            self.assertEqual(len(snapshots(rows)[-1]["fish"]), 12)

    def test_random_fish_false_dung_yen_va_khong_sinh(self):
        """random_fish:false: cá fixture đứng yên, KHÔNG sinh đàn (v1.1 mục D)."""
        with Workdir() as w:
            f = write_json(w.path("sc.json"), sc({
                "random_fish": False,
                "fish": [{"id": "F1", "kind": "ca_linh", "pos": [10, 10], "heading_deg": 0}]}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "400",
                                     "--scenario", f, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            last = snapshots(rows)[-1]
            self.assertEqual(last["fish"][0]["pos"], [10, 10])
            self.assertTrue(close(last["fish"][0]["heading_deg"], 0, 1e-9))
            self.assertEqual(len(events(rows, "fish_spawned")), 0)

    def test_tat_dinh_tung_byte(self):
        """Cùng seed + inputs: cá bơi/sinh vẫn tất định, JSONL giống nhau từng byte."""
        with Workdir() as w:
            for i in (1, 2):
                code, err = run_headless("--mode", "gather", "--seed", "9", "--ticks", "500",
                                         "--out", w.path(f"o{i}.jsonl"))
                self.assertEqual(code, 0, err)
            with open(w.path("o1.jsonl"), "rb") as a, open(w.path("o2.jsonl"), "rb") as b:
                self.assertEqual(a.read(), b.read())


class V11Kinds(unittest.TestCase):
    def test_bat_ca_keo_yield_2(self):
        """Loài mới ca_keo: bắt được đàn, yield = 2 vào giỏ."""
        with Workdir() as w:
            f = write_json(w.path("sc.json"), sc({
                "player": {"pos": [15, 5.5]},
                "random_fish": False,
                "fish": [{"id": "F1", "kind": "ca_keo", "pos": [15, 5]}]}))
            inp = write_json(w.path("in.json"), frames({"tick": 0, "catch": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", f, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            fc = events(rows, "fish_caught")
            self.assertEqual(len(fc), 1, fc)
            self.assertEqual(fc[0]["data"], {"fish_id": "F1", "kind": "ca_keo", "yield": 2})
            self.assertEqual(kinds(snapshots(rows)[-1]["hold"]), ["ca_keo", "ca_keo"])

    def test_hai_nut_keo_neo(self):
        """Nút mới keo_neo (N5): hái được ở mặt nước, vào giỏ đúng kind, nút bắt đầu mọc lại."""
        with Workdir() as w:
            f = write_json(w.path("sc.json"), sc({
                "player": {"pos": [76, 0.3]},
                "random_fish": False,
                "fish": []}))
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", f, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            g = events(rows, "gather")
            self.assertEqual(len(g), 1, g)
            self.assertEqual(g[0]["data"], {"node_id": "N5", "kind": "keo_neo", "amount": 1})
            s = snapshots(rows)[-1]
            self.assertEqual(kinds(s["hold"]), ["keo_neo"])
            n5 = [n for n in s["nodes"] if n["id"] == "N5"][0]
            self.assertEqual(n5["ready"], False, "hái xong nút bắt đầu mọc lại")


if __name__ == "__main__":
    unittest.main()
