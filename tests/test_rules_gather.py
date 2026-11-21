"""Test luật `gather` (buổi sáng: lặn & hái) — Phase 1. Module: gather · Vai: QA.

Kiểu HỘP ĐEN: chạy `headless_cmd`, dựng tình huống bằng scenario, đọc JSONL / file kho.
Số liệu đọc từ game.contract.json. Căn cứ luật: PRD-0.md mục D (scenario), E (output), F (Gather), G (kho).
Quy ước bước: bước k đọc frame tick=k và ghi event ở tick k+1 (PRD-0 mục F).

Mã AC do nhóm tự đặt (PRD-0 chỉ gợi ý dạng `AC-P1-xx`); dùng để điền docs/verification/phase-1.md:

| AC        | Nhóm test | Luật được kiểm (PRD-0)                                              |
|-----------|-----------|---------------------------------------------------------------------|
| AC-P1-01  | Oxy       | F: oxy trừ/hồi theo d cuối bước, kẹp [0,max], dive/surface/oxygen_empty |
| AC-P1-02  | Ngat      | F: ngạt mỗi 60 tick, Máu 0 → faint (LIFO), kho rỗng                 |
| AC-P1-03  | Nut       | F: hái nút (gần nhất, hòa theo id), hold_full, mọc lại              |
| AC-P1-04  | Ca        | F: bắt cá (cả đàn, xóa đàn, hồi chiêu, hold_full không đổi đàn)     |
| AC-P1-05  | KetThuc   | F/G: cập bến, hết giờ, kho ghi một lần, hành động ở bước cuối       |

Test sẽ ĐỎ cho tới khi luật tương ứng được viết (TODO trong chonoi/sim/gather.py). Không sửa test cho xanh khi luật sai.
Chạy: PYTHONPATH=tests:. python3 -m unittest test_rules_gather -v
"""

import json
import unittest

from helpers import Workdir, events, frames
from rules_common import at, contract_tuning, run_mode


def run(w, block, **kw):
    return run_mode(w, "gather", block, **kw)


def tuning():
    return contract_tuning("gather")


def only(rows, name):
    """Event duy nhất tên `name` (kiểm đúng một sự kiện)."""
    ev = events(rows, name)
    assert len(ev) == 1, f"cần đúng 1 event {name}, có {len(ev)}"
    return ev[0]


class Oxy(unittest.TestCase):
    """AC-P1-01 — oxy, lặn / nổi."""

    def test_oxy_01_underwater_drops_one_per_tick(self):
        """Dưới nước (d > 0.5) oxy trừ đúng 1 mỗi tick."""
        with Workdir() as w:
            rows = run(w, {"player": {"pos": [50, 10]}}, ticks=10)
            p = at(rows, 10)["player"]
            self.assertEqual(p["oxygen_ticks"], p["oxygen_max_ticks"] - 10)

    def test_oxy_02_surface_refills_and_clamps(self):
        """Mặt nước (d ≤ 0.5): +oxygen_refill_per_tick mỗi tick, kẹp ở oxy tối đa."""
        t = tuning()
        with Workdir() as w:
            rows = run(w, {"player": {"pos": [50, 0], "oxygen_ticks": 100}}, ticks=10)
            self.assertEqual(at(rows, 10)["player"]["oxygen_ticks"], 100 + 10 * t["oxygen_refill_per_tick"])
            rows = run(w, {"player": {"pos": [50, 0], "oxygen_ticks": 100}}, ticks=400, every=400)
            p = at(rows, 400)["player"]
            self.assertEqual(p["oxygen_ticks"], p["oxygen_max_ticks"])

    def test_oxy_03_oxygen_empty_event(self):
        """`oxygen_empty` phát đúng 1 lần ở tick oxy từ dương xuống 0, data.oxygen_ticks = 0."""
        with Workdir() as w:
            rows = run(w, {"player": {"pos": [50, 10], "oxygen_ticks": 1}}, ticks=5)
            ev = only(rows, "oxygen_empty")
            self.assertEqual(ev["tick"], 1)
            self.assertEqual(ev["data"]["oxygen_ticks"], 0)

    def test_oxy_04_dive_and_surface_events(self):
        """Đổi phía biên mặt nước: `dive` khi xuống, `surface` khi nổi; data có `pos`; đúng thứ tự."""
        with Workdir() as w:
            inp = frames({"tick": 0, "move": [0, 1]}, {"tick": 120, "move": [0, -1]})
            rows = run(w, {"player": {"pos": [50, 0]}}, inp=inp, ticks=300, every=300)
            dive, surf = only(rows, "dive"), only(rows, "surface")
            self.assertIn("pos", dive["data"])
            self.assertIn("pos", surf["data"])
            self.assertLess(dive["tick"], surf["tick"])


class Ngat(unittest.TestCase):
    """AC-P1-02 — ngạt, Máu, ngất."""

    def test_ngat_01_choke_every_interval(self):
        """Oxy 0 dưới nước liên tục: ngạt lần đầu ở tick 60 (= t+59 với t = tick chạm 0), -1 Máu, `choke.hp`."""
        t = tuning()
        n = t["choke_interval_ticks"]
        with Workdir() as w:
            rows = run(w, {"player": {"pos": [50, 10], "oxygen_ticks": 1}}, ticks=n)
            self.assertEqual(only(rows, "oxygen_empty")["tick"], 1)
            ev = only(rows, "choke")
            self.assertEqual(ev["tick"], n)
            self.assertEqual(ev["data"]["hp"], t["hp_max"] - 1)
            self.assertEqual(at(rows, n - 1)["player"]["hp"], t["hp_max"])
            self.assertEqual(at(rows, n)["player"]["hp"], t["hp_max"] - 1)
            self.assertEqual(at(rows, n)["player"]["zero_oxy_ticks"], 0, "đủ 60 thì đếm về 0")

    def test_ngat_02_no_choke_at_surface(self):
        """Oxy 0 nhưng ở mặt nước: không ngạt, oxy hồi."""
        with Workdir() as w:
            rows = run(w, {"player": {"pos": [50, 0], "oxygen_ticks": 0}}, ticks=200, every=200)
            self.assertEqual(events(rows, "choke"), [])
            self.assertEqual(at(rows, 200)["player"]["hp"], tuning()["hp_max"])

    def test_ngat_03_surfacing_on_choke_step_saves_player(self):
        """Nổi lên đúng bước đáng lẽ ngạt (đếm 59): hồi oxy, không ngạt."""
        with Workdir() as w:
            sc = {"player": {"pos": [50, 0.505], "oxygen_ticks": 0, "zero_oxy_ticks": 59}}
            rows = run(w, sc, inp=frames({"tick": 0, "move": [0, -1]}), ticks=1)
            self.assertEqual(events(rows, "choke"), [])
            p = at(rows, 1)["player"]
            self.assertEqual(p["hp"], tuning()["hp_max"])
            self.assertEqual(p["oxygen_ticks"], tuning()["oxygen_refill_per_tick"])

    def test_ngat_04_faint_lifo_and_empty_inventory(self):
        """Máu về 0: choke(hp 0) → faint{cause:choke, lost theo LIFO, hp:0} → gather_end fainted, kho rỗng."""
        with Workdir() as w:
            inv = w.path("inv.json")
            sc = {"player": {"pos": [50, 10], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 1},
                  "hold": ["ca_loc", "bong_sung"]}
            rows = run(w, sc, ticks=100, every=100, inv_out=inv)
            self.assertEqual(only(rows, "choke")["data"]["hp"], 0)
            faint = only(rows, "faint")
            self.assertEqual(faint["data"], {"cause": "choke", "lost": ["bong_sung", "ca_loc"], "hp": 0})
            end = only(rows, "gather_end")
            self.assertEqual(end["data"], {"reason": "fainted", "inventory": {"items": {}}})
            names = [r["name"] for r in rows if r["type"] == "event"]
            self.assertLess(names.index("faint"), names.index("gather_end"))
            self.assertEqual(rows[-1]["reason"], "fainted")
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {}})


class Nut(unittest.TestCase):
    """AC-P1-03 — hái nút ở mặt nước."""

    def test_nut_01_gather_at_surface(self):
        """interact ở mặt nước trong tầm: +node_yield, event `gather`, nút regrow_s × 60 tick."""
        t = tuning()
        with Workdir() as w:
            rows = run(w, {"player": {"pos": [12, 0]}}, inp=frames({"tick": 0, "interact": True}), ticks=2)
            ev = only(rows, "gather")
            self.assertEqual(ev["tick"], 1)
            self.assertEqual(ev["data"], {"node_id": "N1", "kind": "bong_dien_dien", "amount": t["node_yield"]})
            s = at(rows, 1)
            self.assertEqual(s["hold"], ["bong_dien_dien"] * t["node_yield"])
            n1 = next(n for n in s["nodes"] if n["id"] == "N1")
            self.assertFalse(n1["ready"])
            self.assertEqual(n1["regrow_ticks"], t["regrow_s"] * 60)

    def test_nut_02_no_gather_underwater(self):
        """Dưới nước thì bỏ qua interact (không phải bến)."""
        with Workdir() as w:
            rows = run(w, {"player": {"pos": [12, 5]}}, inp=frames({"tick": 0, "interact": True}), ticks=2)
            self.assertEqual(events(rows, "gather"), [])
            self.assertEqual(at(rows, 2)["hold"], [])

    def test_nut_03_radius_is_inclusive(self):
        """Đúng mép interact_radius vẫn hái được; vượt mép thì không."""
        r = tuning()["interact_radius"]
        with Workdir() as w:
            sc = {"player": {"pos": [20, 0]}, "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [20 + r, 0]}]}
            rows = run(w, sc, inp=frames({"tick": 0, "interact": True}), ticks=1)
            self.assertEqual(len(events(rows, "gather")), 1)
            sc["nodes"][0]["pos"] = [20 + r + 0.5, 0]
            rows = run(w, sc, inp=frames({"tick": 0, "interact": True}), ticks=1)
            self.assertEqual(events(rows, "gather"), [])

    def test_nut_04_nearest_ready_node_ties_by_id(self):
        """Chọn nút ready gần nhất; bằng khoảng cách thì id nhỏ; nút chưa ready bị bỏ qua."""
        with Workdir() as w:
            sc = {"player": {"pos": [20, 0]}, "nodes": [
                {"id": "N2", "kind": "bong_sung", "pos": [21, 0]},
                {"id": "N1", "kind": "bong_dien_dien", "pos": [19, 0]},
                {"id": "N3", "kind": "bong_sung", "pos": [20.5, 0], "regrow_ticks": 500}]}
            rows = run(w, sc, inp=frames({"tick": 0, "interact": True}), ticks=1)
            self.assertEqual(only(rows, "gather")["data"]["node_id"], "N1")

    def test_nut_05_hold_full_keeps_node(self):
        """Giỏ đầy: `hold_full` {action:gather,node_id,required,free}; nút giữ nguyên."""
        cap = tuning()["hold_capacity"]
        with Workdir() as w:
            rows = run(w, {"player": {"pos": [12, 0]}, "hold": ["ca_loc"] * cap},
                       inp=frames({"tick": 0, "interact": True}), ticks=1)
            ev = only(rows, "hold_full")
            self.assertEqual(ev["data"], {"action": "gather", "node_id": "N1", "required": 1, "free": 0})
            self.assertEqual(events(rows, "gather"), [])
            n1 = next(n for n in at(rows, 1)["nodes"] if n["id"] == "N1")
            self.assertTrue(n1["ready"])

    def test_nut_06_regrow_event_and_gather_again(self):
        """Nút 1 → 0 phát `node_regrown` rồi hái lại được (kể cả ngay bước đó)."""
        with Workdir() as w:
            sc = {"player": {"pos": [12, 0]},
                  "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [12, 0], "regrow_ticks": 3}]}
            inp = frames({"tick": 0, "interact": True}, {"tick": 1, "interact": False},
                         {"tick": 10, "interact": True})
            rows = run(w, sc, inp=inp, ticks=12)
            self.assertEqual(only(rows, "node_regrown")["data"], {"node_id": "N1"})
            self.assertEqual(only(rows, "gather")["tick"], 11)
            self.assertEqual(at(rows, 12)["hold"], ["bong_sung"])


class Ca(unittest.TestCase):
    """AC-P1-04 — bắt đàn cá."""

    def test_ca_01_catch_takes_whole_school(self):
        """Dưới nước, trong tầm: +yield, đàn bị xóa, `fish_caught`, hồi chiêu catch_cooldown_s × 60."""
        t = tuning()
        with Workdir() as w:
            sc = {"player": {"pos": [50, 10]}, "random_fish": False,
                  "fish": [{"id": "F1", "kind": "ca_linh", "pos": [50, 10]}]}
            rows = run(w, sc, inp=frames({"tick": 0, "catch": True}), ticks=1)
            self.assertEqual(only(rows, "fish_caught")["data"],
                             {"fish_id": "F1", "kind": "ca_linh", "yield": t["fish_yield"]["ca_linh"]})
            s = at(rows, 1)
            self.assertEqual(s["hold"], ["ca_linh"] * t["fish_yield"]["ca_linh"])
            self.assertEqual(s["fish"], [])
            self.assertEqual(s["player"]["catch_cd_ticks"], round(t["catch_cooldown_s"] * 60))

    def test_ca_02_no_catch_at_surface(self):
        """Ở mặt nước thì không bắt, không hồi chiêu."""
        with Workdir() as w:
            sc = {"player": {"pos": [50, 0]}, "random_fish": False,
                  "fish": [{"id": "F1", "kind": "ca_loc", "pos": [50, 1]}]}
            rows = run(w, sc, inp=frames({"tick": 0, "catch": True}), ticks=1)
            self.assertEqual(events(rows, "fish_caught"), [])
            self.assertEqual(at(rows, 1)["player"]["catch_cd_ticks"], 0)

    def test_ca_03_cooldown_usable_again_after_L_ticks(self):
        """Hồi chiêu L đặt ở tick t dùng lại từ t+L: bấm ở bước 29 chưa được, bước 30 được (L = 30)."""
        for press, want in ((29, 1), (30, 2)):
            with Workdir() as w:
                sc = {"player": {"pos": [50, 10]}, "random_fish": False,
                      "fish": [{"id": "F1", "kind": "ca_loc", "pos": [50, 10]},
                               {"id": "F2", "kind": "ca_loc", "pos": [50, 11]}]}
                inp = frames({"tick": 0, "catch": True}, {"tick": 1, "catch": False}, {"tick": press, "catch": True})
                rows = run(w, sc, inp=inp, ticks=press + 1)
                self.assertEqual(len(events(rows, "fish_caught")), want, press)

    def test_ca_04_nearest_school_ties_by_id(self):
        """Chọn đúng một đàn gần nhất trong catch_radius; hòa khoảng cách thì id nhỏ; đàn khác còn nguyên."""
        with Workdir() as w:
            sc = {"player": {"pos": [50, 10]}, "random_fish": False,
                  "fish": [{"id": "F2", "kind": "ca_loc", "pos": [51, 10]},
                           {"id": "F1", "kind": "ca_loc", "pos": [49, 10]}]}
            rows = run(w, sc, inp=frames({"tick": 0, "catch": True}), ticks=1)
            self.assertEqual(only(rows, "fish_caught")["data"]["fish_id"], "F1")
            self.assertEqual([f["id"] for f in at(rows, 1)["fish"]], ["F2"])

    def test_ca_05_out_of_radius_no_event_no_cooldown(self):
        """Không có đàn trong tầm: không event, không hồi chiêu."""
        with Workdir() as w:
            sc = {"player": {"pos": [50, 10]}, "random_fish": False,
                  "fish": [{"id": "F1", "kind": "ca_loc", "pos": [80, 10]}]}
            rows = run(w, sc, inp=frames({"tick": 0, "catch": True}), ticks=1)
            self.assertEqual(events(rows, "fish_caught"), [])
            self.assertEqual(at(rows, 1)["player"]["catch_cd_ticks"], 0)

    def test_ca_06_not_enough_room_keeps_school_and_cooldown(self):
        """Thiếu chỗ (không bắt một phần): `hold_full` {action:catch,fish_id,required,free}; giữ đàn; không hồi chiêu."""
        cap = tuning()["hold_capacity"]
        with Workdir() as w:
            sc = {"player": {"pos": [50, 10]}, "random_fish": False, "hold": ["bong_sung"] * (cap - 2),
                  "fish": [{"id": "F1", "kind": "ca_linh", "pos": [50, 10]}]}
            rows = run(w, sc, inp=frames({"tick": 0, "catch": True}), ticks=1)
            self.assertEqual(only(rows, "hold_full")["data"],
                             {"action": "catch", "fish_id": "F1", "required": 3, "free": 2})
            self.assertEqual(events(rows, "fish_caught"), [])
            s = at(rows, 1)
            self.assertEqual([f["id"] for f in s["fish"]], ["F1"])
            self.assertEqual(s["player"]["catch_cd_ticks"], 0)
            self.assertEqual(s["hold_count"], cap - 2)


class KetThuc(unittest.TestCase):
    """AC-P1-05 — cập bến, hết giờ, kho (smoke test đã có test_inv_01 cho đường cơ bản)."""

    def test_ket_01_dock_radius_inclusive_beats_gather(self):
        """Đúng mép dock_radius vẫn `docked`; bến xét trước hái (nút nằm trong bến không bị hái)."""
        t = tuning()
        x = t["dock_pos"][0] + t["dock_radius"]
        with Workdir() as w:
            sc = {"player": {"pos": [x, 0]}, "hold": ["ca_loc"],
                  "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [x, 0]}]}
            rows = run(w, sc, inp=frames({"tick": 0, "interact": True}), ticks=5)
            self.assertEqual(events(rows, "gather"), [])
            self.assertEqual(only(rows, "gather_end")["data"], {"reason": "docked", "inventory": {"items": {"ca_loc": 1}}})
            self.assertEqual(rows[-1]["reason"], "docked")

    def test_ket_02_gather_on_last_step_still_counts(self):
        """Hết giờ ở bước cuối: hái hợp lệ ở bước đó vẫn vào kho; lý do `time`."""
        with Workdir() as w:
            inv = w.path("inv.json")
            sc = {"player": {"pos": [12, 0]}, "time_left_ticks": 1}
            rows = run(w, sc, inp=frames({"tick": 0, "interact": True}), ticks=5, inv_out=inv)
            self.assertEqual(only(rows, "gather")["tick"], 1)
            end = only(rows, "gather_end")
            self.assertEqual(end["data"], {"reason": "time", "inventory": {"items": {"bong_dien_dien": 1}}})
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {"bong_dien_dien": 1}})

    def test_ket_03_time_end_at_depth_keeps_hold(self):
        """Hết giờ khi đang ở dưới nước: kết thúc `time`, giữ nguyên giỏ (không ngất)."""
        with Workdir() as w:
            rows = run(w, {"player": {"pos": [50, 10]}, "hold": ["ca_loc"], "time_left_ticks": 3}, ticks=50)
            self.assertEqual(only(rows, "gather_end")["data"],
                             {"reason": "time", "inventory": {"items": {"ca_loc": 1}}})


if __name__ == "__main__":
    unittest.main()
