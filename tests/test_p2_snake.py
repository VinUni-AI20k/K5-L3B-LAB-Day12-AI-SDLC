"""Test mở rộng Rắn Hổ Mây (snake, LeBao403). Ticket-02 mục 3: M3 từ Ngày 1, [72,14] <-> [76,14], d ∈ [8,20],
patrol 1.0 m/s, chase 3.5 m/s, phát hiện <= 8 m, rời chase khi > 16 m hoặc người chơi lên d < 8; luật chạm và
recoil chung với Cá Sấu.

Chạy: PYTHONPATH=tests:. python3 -m unittest discover -s tests -p "test_p2_snake.py" -v
"""

import copy
import json
import math
import unittest

from chonoi.contract import validate_extensions
from chonoi.errors import BadInput
from helpers import Workdir, close, events, read_jsonl, run_headless, snapshots, write_json

with open("game.contract.json", encoding="utf-8") as _f:
    CONTRACT = json.load(_f)
T = CONTRACT["tuning"]
RAN = T["gather"]["monsters"]["species"]["ran"]

def items(*kinds, start=1):
    """Fixture v1.2: cá thể I<start>, I<start+1>, ... fresh 100 theo thứ tự vào giỏ."""
    return [{"id": f"I{start + i}", "kind": k, "fresh": 100} for i, k in enumerate(kinds)]


def ik(lst):
    """(id, kind) của danh sách cá thể public: so không phụ thuộc fresh (giỏ hao theo tick)."""
    return [(x["id"], x["kind"]) for x in lst]



def run(block, ticks):
    with Workdir() as w:
        sc = write_json(w.path("sc.json"), {"gather": {"random_fish": False, **block}})
        code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", str(ticks), "--scenario", sc,
                                 "--snapshot-every", "1", "--out", w.path("o.jsonl"))
        assert code == 0, err
        return read_jsonl(w.path("o.jsonl"))


def m_at(rows, tick, mid="M3"):
    return {m["id"]: m for m in {s["tick"]: s for s in snapshots(rows)}[tick]["monsters"]}[mid]


def m3_only():
    """M3 dạng fixture scenario (bỏ from_day, khóa chỉ có trong manifest)."""
    m3 = dict(next(s for s in T["gather"]["monsters"]["spawns"] if s["id"] == "M3"))
    m3.pop("from_day")
    return [m3]


class Manifest(unittest.TestCase):
    def test_khai_snake_va_du_lieu_khop(self):
        self.assertIn("snake", CONTRACT["extensions"])
        self.assertEqual((RAN["patrol_speed"], RAN["chase_speed"], RAN["detect_radius"], RAN["exit_radius"],
                          RAN["depths"]), (1.0, 3.5, 8, 16, [8, 20]))
        m3 = next(s for s in T["gather"]["monsters"]["spawns"] if s["id"] == "M3")
        self.assertEqual((m3["pos"], m3["waypoints"], m3["from_day"]), ([72, 14], [[72, 14], [76, 14]], 1))

    def test_khai_lech_bi_tu_choi(self):
        t = copy.deepcopy(T)
        with self.assertRaises(BadInput):
            validate_extensions([], t)  # có dữ liệu rắn nhưng không khai
        del t["gather"]["monsters"]["species"]["ran"]
        t["gather"]["monsters"]["spawns"] = [s for s in t["gather"]["monsters"]["spawns"] if s["kind"] != "ran"]
        with self.assertRaises(BadInput):
            validate_extensions(["snake"], t)  # khai nhưng thiếu dữ liệu
        validate_extensions([], t)


class Snake(unittest.TestCase):
    def test_m3_co_tu_ngay_1_trong_gather_doc_lap(self):
        rows = run({}, 0)
        self.assertEqual([m["id"] for m in snapshots(rows)[0]["monsters"]], ["M1", "M3"])

    def test_tuan_tra_72_76(self):
        rows = run({"monsters": m3_only()}, 240)
        self.assertTrue(close(m_at(rows, 120)["pos"][0], 74, 0.01))
        self.assertEqual((m_at(rows, 240)["pos"], m_at(rows, 240)["target_idx"]), ([76, 14], 0))

    def test_nguong_do_sau_8_va_ban_kinh_phat_hien_8(self):
        # d = 8.5 (>= 8), cách 6 m: phát hiện và đuổi 3.5 m/s
        rows = run({"player": {"pos": [66, 14]}, "monsters": m3_only()}, 1)
        self.assertEqual(m_at(rows, 1)["state"], "chase")
        self.assertTrue(close(math.dist(m_at(rows, 0)["pos"], m_at(rows, 1)["pos"]), RAN["chase_speed"] / 60, 0.001))
        # d = 7.5 (< 8): không phát hiện dù rất gần
        rows = run({"player": {"pos": [72, 7.5]}, "monsters": m3_only()}, 30)
        self.assertEqual(m_at(rows, 30)["state"], "patrol")
        self.assertEqual(events(rows, "monster_hit"), [])
        # ngoài 8 m (Cá Sấu 10 m sẽ phát hiện, rắn thì không)
        rows = run({"player": {"pos": [63, 14]}, "monsters": m3_only()}, 1)
        self.assertEqual(m_at(rows, 1)["state"], "patrol")

    def test_cham_va_recoil_dung_luat_chung(self):
        rows = run({"player": {"pos": [72, 9]}, "hold": items("ca_loc", "bong_sung"),
                    "monsters": [{"id": "M3", "kind": "ran", "pos": [73, 9], "waypoints": [[73, 9], [73, 9]]}]}, 2)
        hits = events(rows, "monster_hit")
        self.assertEqual([(h["tick"], h["data"]["monster_id"], ik(h["data"]["lost"])) for h in hits],
                         [(1, "M3", [("I2", "bong_sung")])])
        m = m_at(rows, 2)
        self.assertEqual((m["state"], m["recoil_dir"]), ("recoil", [1, 0]))


if __name__ == "__main__":
    unittest.main()
