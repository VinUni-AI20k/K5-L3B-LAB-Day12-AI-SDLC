"""Test luật Phase 2 (hộp đen qua headless) theo Phase2.md mục 1, 2, 4. Vai: QA.

Chỉ chạy khi contract_version = "1.1" (xem rules_common.requires_v11). Căn cứ: Phase2.md 1.1 (cá bơi/sinh),
1.2 (Cá Sấu), 1.3 (quán 6 món), 2 (vòng ngày, Shop), 4.2 (pause), 4.4 (output), 4.5 (thứ tự).

| AC        | Nhóm test | Luật được kiểm                                                          |
|-----------|-----------|-------------------------------------------------------------------------|
| AC-P2-05  | Ca        | cá bơi 1.5 m/s, phản xạ mép, sinh đàn theo lịch 360·k, trần 12          |
| AC-P2-06  | Sau       | Cá Sấu tuần tra, chase, hit (Máu, bỏ giỏ LIFO, bất tử 90), ngất         |
| AC-P2-07  | Quan      | 4 bàn, khách lượt 120 + 900k, món mới (lẩu mắm) nấu và giá              |
| AC-P2-08  | Day       | --mode day: day_plan, đổi pha cùng tick, days_complete, cờ --days       |
| AC-P2-09  | Shop      | buy (đủ/đúng giá/thiếu tiền), shop_done, nâng cấp có hiệu lực Ngày sau  |
| AC-P2-10  | Pause     | pause/resume: tick ngoài chạy, sim_tick và timer đứng yên               |
| AC-P2-11  | Hieunang  | một Ngày headless không pause (≤ 22.200 tick) chạy ≤ 20 s              |

Chạy: PYTHONPATH=tests:. python3 -m unittest discover -s tests -p "test_p2_rules.py" -v
"""

import time
import unittest

from helpers import Workdir, events, frames, run_headless, snapshots, write_json
from rules_common import FRESH, H, Kitchen, at, counts, kinds, requires_v11, run_day, run_mode, settled_price

NORES = [] if FRESH else {}   # "không giữ gì" theo schema hiện hành

SPAWN_DEPTHS = {"ca_linh": (5, 10), "ca_loc": (10, 16), "ca_keo": (24, 27)}


def gather(w, block, **kw):
    return run_mode(w, "gather", block, **kw)


def only(rows, name):
    ev = events(rows, name)
    assert len(ev) == 1, f"cần đúng 1 event {name}, có {len(ev)}"
    return ev[0]


@requires_v11
class Ca(unittest.TestCase):
    """AC-P2-05 — cá bơi và sinh."""

    def test_ca_01_swims_at_1_5_mps(self):
        """Đàn bơi theo hướng ban đầu 1.5 m/s: 60 tick đi 1.5 m (chưa tới bước đổi hướng 120)."""
        with Workdir() as w:
            fish = [{"id": "F1", "kind": "ca_linh", "pos": [50, 5], "heading_deg": 0}]
            rows = gather(w, {"fish": fish}, ticks=60)
            x, d = at(rows, 60)["fish"][0]["pos"]
            self.assertAlmostEqual(x, 51.5, delta=0.1)
            self.assertAlmostEqual(d, 5, delta=0.1)

    def test_ca_02_reflects_off_x_edge_with_remaining_distance(self):
        """Chạm mép x = 96: phản xạ phần quãng đường còn lại, đảo hướng x. Từ 95.5, 60 tick = 1.5 m → x = 95.0."""
        with Workdir() as w:
            fish = [{"id": "F1", "kind": "ca_linh", "pos": [95.5, 5], "heading_deg": 0}]
            rows = gather(w, {"fish": fish}, ticks=60)
            f = at(rows, 60)["fish"][0]
            self.assertAlmostEqual(f["pos"][0], 95.0, delta=0.1)
            self.assertAlmostEqual(f["heading_deg"] % 360, 180, delta=1)

    def test_ca_03_reflects_off_depth_range(self):
        """Cá linh chỉ ở d ∈ [3,12]: từ d = 11.5 hướng xuống, 60 tick → phản xạ ở 12, d = 11.0."""
        with Workdir() as w:
            fish = [{"id": "F1", "kind": "ca_linh", "pos": [50, 11.5], "heading_deg": 90}]
            rows = gather(w, {"fish": fish}, ticks=60)
            self.assertAlmostEqual(at(rows, 60)["fish"][0]["pos"][1], 11.0, delta=0.1)

    def test_ca_04_random_fish_false_keeps_fish_still(self):
        """random_fish:false: cá fixture đứng yên, không sinh thêm."""
        with Workdir() as w:
            fish = [{"id": "F1", "kind": "ca_linh", "pos": [50, 5], "heading_deg": 0}]
            rows = gather(w, {"fish": fish, "random_fish": False}, ticks=400)
            s = at(rows, 400)
            self.assertEqual(s["fish"][0]["pos"], [50, 5])
            self.assertEqual(len(s["fish"]), 1)
            self.assertEqual(events(rows, "fish_spawned"), [])

    def test_ca_05_spawn_at_phase_tick_360(self):
        """Tại phase_tick 360: sinh tối đa một đàn, `fish_spawned` {id,kind,pos}; id nối sau hậu tố lớn nhất;
        x thuộc điểm sinh, d thuộc điểm sinh của loài."""
        with Workdir() as w:
            fish = [{"id": "F1", "kind": "ca_linh", "pos": [50, 5], "heading_deg": 0}]
            rows = gather(w, {"fish": fish}, ticks=361, every=1)
            ev = only(rows, "fish_spawned")
            self.assertEqual(ev["tick"], 360)
            d = ev["data"]
            self.assertEqual(d["id"], "F2")
            self.assertIn(d["pos"][0], (15, 30, 45, 60, 75, 90))
            self.assertIn(d["pos"][1], SPAWN_DEPTHS[d["kind"]])
            self.assertEqual(len(at(rows, 360)["fish"]), 2)
            self.assertEqual(len(at(rows, 359)["fish"]), 1)

    def test_ca_06_no_spawn_at_cap_12(self):
        """Đủ trần 12 đàn thì không sinh."""
        with Workdir() as w:
            fish = [{"id": f"F{i}", "kind": "ca_linh", "pos": [10 + i * 7, 5], "heading_deg": 0} for i in range(1, 13)]
            rows = gather(w, {"fish": fish}, ticks=361)
            self.assertEqual(events(rows, "fish_spawned"), [])
            self.assertEqual(len(at(rows, 361)["fish"]), 12)


@requires_v11
class Sau(unittest.TestCase):
    """AC-P2-06 — Cá Sấu Năm Chèo (kiểm bằng fixture `gather.monsters`)."""

    @staticmethod
    def croc(pos, wps, cid="M1"):
        return {"id": cid, "kind": "ca_sau", "pos": pos, "waypoints": wps}

    def test_sau_01_default_day1_layout_and_patrol(self):
        """Không khai monsters: Ngày 1 có M1 ở [60,24]; tuần tra 1.0 m/s về waypoint kia ([64,24])."""
        with Workdir() as w:
            rows = gather(w, {}, ticks=60)
            ms = at(rows, 0)["monsters"]
            self.assertEqual([m["id"] for m in ms], ["M1"])
            self.assertEqual(ms[0]["pos"], [60, 24])
            self.assertAlmostEqual(at(rows, 60)["monsters"][0]["pos"][0], 61.0, delta=0.05)

    def test_sau_02_chase_when_player_deep_and_near(self):
        """Người chơi ở d ≥ 10 và cách ≤ 10 m: chuyển chase."""
        with Workdir() as w:
            sc = {"player": {"pos": [60, 18]}, "monsters": [self.croc([60, 24], [[60, 24], [64, 24]])]}
            rows = gather(w, sc, ticks=2)
            self.assertEqual(at(rows, 2)["monsters"][0]["state"], "chase")

    def test_sau_03_no_chase_when_player_shallow(self):
        """Người chơi lên d < 10 thì không bị đuổi."""
        with Workdir() as w:
            sc = {"player": {"pos": [50, 9.5]}, "monsters": [self.croc([50, 14], [[50, 14], [54, 14]])]}
            rows = gather(w, sc, ticks=3)
            self.assertEqual(at(rows, 3)["monsters"][0]["state"], "patrol")

    def test_sau_04_hit_loses_hp_half_hold_lifo_and_invuln(self):
        """Chạm ≤ 1.5 m ở d ≥ 10: -1 Máu, bỏ floor(n/2) nguyên liệu LIFO, bất tử 90 tick, đúng một hit."""
        with Workdir() as w:
            hold = H("ca_loc", "ca_loc", "bong_sung", "bong_sung", "ca_loc")
            sc = {"player": {"pos": [50, 20]}, "hold": hold,
                  "monsters": [self.croc([50, 20], [[50, 20], [54, 20]])]}
            # Chỉ đo trong thời gian bất tử (90 tick): sau đó được phép chạm lại (lần chạm thứ 2 ở tick 91 là đúng luật).
            rows = gather(w, sc, ticks=60)
            hit = only(rows, "monster_hit")
            self.assertEqual(hit["tick"], 1)
            d = hit["data"]
            self.assertEqual((d["monster_id"], d["hp"]), ("M1", 2))
            self.assertEqual(kinds(d["lost"]), ["ca_loc", "bong_sung"])
            s = at(rows, 1)
            self.assertEqual(s["player"]["invuln_ticks"], 90)
            self.assertEqual(kinds(s["hold"]), ["ca_loc", "ca_loc", "bong_sung"])

    def test_sau_05_no_hit_when_player_shallow(self):
        with Workdir() as w:
            sc = {"player": {"pos": [50, 9.5]}, "monsters": [self.croc([50, 10], [[50, 10], [54, 10]])]}
            rows = gather(w, sc, ticks=10)
            self.assertEqual(events(rows, "monster_hit"), [])

    def test_sau_06_faint_by_monster(self):
        """Máu về 0 do chạm: monster_hit(hp 0), faint {cause:monster, lost: phần giỏ còn lại, hp:0}, gather_end fainted."""
        with Workdir() as w:
            sc = {"player": {"pos": [50, 20], "hp": 1}, "hold": H("ca_loc", "bong_sung"),
                  "monsters": [self.croc([50, 20], [[50, 20], [54, 20]])]}
            rows = gather(w, sc, ticks=20)
            self.assertEqual(only(rows, "monster_hit")["data"]["hp"], 0)
            faint = only(rows, "faint")["data"]
            self.assertEqual((faint["cause"], faint["hp"]), ("monster", 0))
            self.assertEqual(kinds(faint["lost"]), ["ca_loc"])
            self.assertEqual(only(rows, "gather_end")["data"]["reason"], "fainted")


@requires_v11
class Quan(unittest.TestCase):
    """AC-P2-07 — quán 4 bàn, món mới."""

    def test_quan_01_four_tables_two_stoves_in_snapshot(self):
        with Workdir() as w:
            rows = run_mode(w, "quan", {}, ticks=0)
            s = snapshots(rows)[0]
            self.assertEqual([t["id"] for t in s["tables"]], ["T1", "T2", "T3", "T4"])
            self.assertEqual([b["id"] for b in s["stoves"]], ["B1", "B2"])

    def test_quan_02_second_customer_at_1020_sits_at_t2(self):
        """Lượt khách 120 + 900k: khách thứ hai tick 1020 ngồi ghế trống id nhỏ nhất (T2)."""
        with Workdir() as w:
            rows = run_mode(w, "quan", {"stock": Kitchen({"ca_loc": 5, "bong_sung": 5}).stock}, ticks=1020, every=1020)
            arr = events(rows, "customer_arrived")
            self.assertEqual([e["tick"] for e in arr], [120, 1020])
            self.assertEqual([e["data"]["table_id"] for e in arr], ["T1", "T2"])

    def test_quan_03_lau_mam_reserves_and_cooks(self):
        """Kho chỉ đủ lẩu mắm: khách gọi lau_mam, giữ đủ 5 nguyên liệu; nấu 12 s giá 200, items theo kind."""
        counts_ = {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1}
        k = Kitchen(counts_)
        with Workdir() as w:
            sc = {"stock": k.stock, "random_customers": False, "player": {"pos": [2, 7.5]},
                  "customers": [{"id": "C1", "table_id": "T1", "dish_id": "lau_mam", "order_tick": 0,
                                 "state": "waiting", "order_status": "reserved", "reserved": k.reserve(counts_)}]}
            rows = run_mode(w, "quan", sc, inp=frames({"tick": 0, "interact": True}), ticks=1)
            d = only(rows, "cook_started")["data"]
            self.assertEqual(d["dish_id"], "lau_mam")
            self.assertEqual(d["base_price"], settled_price(200, 1))   # v1.2: giá theo độ tươi
            self.assertEqual(kinds(d["items"]), ["bong_dien_dien", "ca_keo", "ca_linh", "ca_linh", "keo_neo"])
            b = next(x for x in at(rows, 1)["stoves"] if x["id"] == "B1")
            self.assertEqual(b["cook_ticks_left"], 12 * 60)

    def test_quan_04_tip_on_200(self):
        """Giá 200 còn ≥ 50% kiên nhẫn: boa floor(200 × 0.2) = 40."""
        dish = {"order_id": "C1", "dish_id": "lau_mam", "base_price": 200}
        with Workdir() as w:
            sc = {"random_customers": False, "player": {"pos": [9, 2.5]}, "hand": dish,
                  "customers": [{"id": "C1", "table_id": "T1", "dish_id": "lau_mam", "order_tick": 0,
                                 "state": "waiting", "order_status": "assigned", "reserved": NORES}]}
            rows = run_mode(w, "quan", sc, inp=frames({"tick": 0, "interact": True}), ticks=1)
            self.assertEqual(only(rows, "served")["data"]["tip"], 40)


DAY_SC = {"gather": {"time_left_ticks": 3}, "quan": {"time_left_ticks": 3}}


@requires_v11
class Day(unittest.TestCase):
    """AC-P2-08 — vòng ngày."""

    def test_day_01_plan_announced_for_day_1(self):
        """Đầu Ngày: day_start → day_plan → phase_start(gather); day_plan khớp D1; snapshot có day, day_plan, upgrades."""
        with Workdir() as w:
            rows = run_day(w, DAY_SC, ticks=0)
            names = [e["name"] for e in events(rows)][:3]
            self.assertEqual(names, ["day_start", "day_plan", "phase_start"])
            self.assertEqual(events(rows, "day_plan")[0]["data"],
                             {"dishes": {"ca_loc_nuong_trui": 3, "goi_bong_sung": 3},
                              "ingredients": {"ca_loc": 3, "bong_sung": 6}})
            s = snapshots(rows)[0]
            for key in ("day", "day_plan", "upgrades", "active_upgrades"):
                self.assertIn(key, s)
            self.assertEqual((s["day"], s["phase"]), (1, "gather"))

    def test_day_02_phases_change_on_same_tick(self):
        """gather_end → phase_start(quan) cùng tick; quan_end → phase_start(shop) cùng tick."""
        with Workdir() as w:
            rows = run_day(w, DAY_SC, ticks=7)
            ge = only(rows, "gather_end")
            qe = only(rows, "quan_end")
            self.assertEqual(ge["tick"], 3)
            self.assertEqual(qe["tick"], 6)
            ph = {e["tick"]: e for e in events(rows, "phase_start")}
            self.assertIn(ge["tick"], ph)
            self.assertIn(qe["tick"], ph)
            self.assertEqual(snapshots(rows)[-1]["phase"], "shop")

    def test_day_03_faint_still_opens_quan_with_empty_stock(self):
        """Ngất vẫn mở quán tối với kho bàn giao rỗng."""
        with Workdir() as w:
            sc = {"gather": {"player": {"pos": [50, 10], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 1},
                             "hold": H("ca_loc")}, "quan": {"time_left_ticks": 3}}
            rows = run_day(w, sc, ticks=6, every=1)
            self.assertEqual(only(rows, "gather_end")["data"]["reason"], "fainted")
            self.assertEqual(events(rows, "phase_start")[-1]["data"], {})
            q = [s for s in snapshots(rows) if s["phase"] == "quan"][0]
            self.assertEqual(counts(q["stock"]), {})

    def test_day_04_days_flag_range(self):
        """--days chỉ từ 1 đến 5 và chỉ với mode day."""
        with Workdir() as w:
            out = w.path("o.jsonl")
            for bad in ("0", "6", "x"):
                self.assertEqual(run_headless("--mode", "day", "--days", bad, "--seed", "1", "--ticks", "0", "--out", out)[0],
                                 2, bad)
            self.assertEqual(run_headless("--mode", "gather", "--days", "2", "--seed", "1", "--ticks", "0", "--out", out)[0], 2)

    def test_day_05_forbids_quan_stock_and_reputation(self):
        """Cấm quan.stock và quan.reputation khi chạy day (mã 2)."""
        with Workdir() as w:
            for block in ({"stock": Kitchen({"ca_loc": 1}).stock}, {"reputation": 4}):
                sc = write_json(w.path("sc.json"), {"quan": block})
                code = run_headless("--mode", "day", "--seed", "1", "--ticks", "0", "--scenario", sc, "--out", w.path("o.jsonl"))[0]
                self.assertEqual(code, 2, block)

    def test_day_06_day_scenario_money_earned_rule(self):
        """day.money > day.earned là mâu thuẫn (mã 2)."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"day": {"money": 100, "earned": 50}})
            self.assertEqual(run_headless("--mode", "day", "--seed", "1", "--ticks", "0", "--scenario", sc,
                                          "--out", w.path("o.jsonl"))[0], 2)

    def test_day_07_days_complete_end_line(self):
        """Đóng Shop ở Ngày cuối: end.reason = days_complete, days_completed = 1."""
        with Workdir() as w:
            rows = run_day(w, DAY_SC, inp=frames({"tick": 6, "shop_done": True}), ticks=50)
            self.assertEqual(only(rows, "shop_end")["data"]["reason"], "done")
            end = rows[-1]
            self.assertEqual((end["type"], end["reason"], end["days_completed"]), ("end", "days_complete", 1))


@requires_v11
class Shop(unittest.TestCase):
    """AC-P2-09 — Shop và nâng cấp."""

    def shop_rows(self, money, buy, ticks=60):
        """Ngày 1 (gather 3 tick + quan 3 tick) rồi Shop mở ở tick 6; mua `buy` và đóng Shop trong cùng frame."""
        with Workdir() as w:
            sc = dict(DAY_SC, day={"money": money, "earned": money})
            inp = frames({"tick": 6, "buy": buy, "shop_done": True})
            return run_day(w, sc, inp=inp, ticks=ticks)

    def test_shop_01_exact_price_buys_and_keeps_earned(self):
        """Đủ đúng giá (200) vẫn mua được bình oxy cấp 1: `bought`, trừ money, giữ earned và điểm."""
        rows = self.shop_rows(200, "oxygen")
        d = only(rows, "bought")["data"]
        self.assertEqual(d, {"upgrade": "oxygen", "level": 1, "price": 200, "money": 0})
        names = [e["name"] for e in events(rows) if e["name"] in ("bought", "shop_end")]
        self.assertEqual(names, ["bought", "shop_end"], "buy xử lý trước shop_done kể cả bước cuối")
        # Lệnh mua được xử lý ở bước mà shop_done đóng Shop (tick 7); snapshot tick 6 còn là trạng thái trước khi mua.
        s = [x for x in snapshots(rows) if x["phase"] == "shop" and x["tick"] == 7][0]
        self.assertEqual((s["money"], s["earned"]), (0, 200))
        self.assertEqual(s["upgrades"], {"oxygen": 1})
        self.assertEqual(s["active_upgrades"], {}, "chưa có hiệu lực trong Ngày hiện tại")

    def test_shop_02_not_enough_funds(self):
        """Thiếu tiền: `buy_failed` reason funds, tiền và cấp giữ nguyên."""
        rows = self.shop_rows(199, "oxygen")
        d = only(rows, "buy_failed")["data"]
        self.assertEqual((d["action"], d["reason"]), ("oxygen", "funds"))
        self.assertEqual(events(rows, "bought"), [])

    def test_shop_03_unknown_item_fails(self):
        rows = self.shop_rows(500, "khong_co")
        self.assertEqual(only(rows, "buy_failed")["data"]["reason"], "unknown")

    def test_shop_04_upgrade_active_next_day(self):
        """Cấp đã mua có hiệu lực từ Ngày kế: Ngày 2 oxy tối đa 45 s = 2700 tick, active_upgrades {oxygen:1}."""
        with Workdir() as w:
            sc = dict(DAY_SC, day={"money": 200, "earned": 200})
            inp = frames({"tick": 6, "buy": "oxygen", "shop_done": True})
            rows = run_day(w, sc, inp=inp, days=2, ticks=30)
            d2 = [s for s in snapshots(rows) if s.get("day") == 2 and s["phase"] == "gather"][0]
            self.assertEqual(d2["active_upgrades"], {"oxygen": 1})
            self.assertEqual(d2["player"]["oxygen_max_ticks"], 2700)
            self.assertEqual(d2["player"]["oxygen_ticks"], 2700, "oxy hồi đầy theo cấp mới")

    def test_shop_05_auto_close_after_600_ticks(self):
        """Shop tự đóng sau 600 tick hoạt động: shop_end reason time."""
        with Workdir() as w:
            rows = run_day(w, DAY_SC, ticks=700, every=700)
            ev = only(rows, "shop_end")
            self.assertEqual(ev["data"]["reason"], "time")
            self.assertEqual(ev["tick"], 6 + 600)


@requires_v11
class Pause(unittest.TestCase):
    """AC-P2-10 — pause / resume."""

    def test_pause_01_freezes_sim_and_timers(self):
        """pause (cạnh lên): phát `paused`, tick ngoài chạy tiếp, sim_tick, phase_tick, time_left_ticks đứng yên,
        snapshot state "paused". Cạnh lên kế: `resumed` và gameplay chạy ngay bước đó."""
        with Workdir() as w:
            inp = frames({"tick": 5, "pause": True}, {"tick": 6, "pause": False}, {"tick": 10, "pause": True})
            rows = gather(w, {"player": {"pos": [50, 10]}}, inp=inp, ticks=12)
            self.assertEqual(only(rows, "paused")["tick"], 6)
            self.assertEqual(only(rows, "resumed")["tick"], 11)
            snaps = {s["tick"]: s for s in snapshots(rows)}
            for t in (6, 7, 8, 9, 10):
                self.assertEqual(snaps[t]["state"], "paused", t)
                self.assertEqual(snaps[t]["sim_tick"], 5, t)
                self.assertEqual(snaps[t]["time_left_ticks"], snaps[5]["time_left_ticks"], t)
            self.assertEqual(snaps[11]["sim_tick"], 6, "resume chạy gameplay ngay trong bước đó")
            self.assertEqual(snaps[11]["state"], "playing")

    def test_pause_02_actions_ignored_while_paused(self):
        """Đang pause: bỏ qua cạnh hành động (hái, bắt cá, mua)."""
        with Workdir() as w:
            inp = frames({"tick": 0, "pause": True}, {"tick": 2, "interact": True})
            rows = gather(w, {"player": {"pos": [12, 0]}}, inp=inp, ticks=5)
            self.assertEqual(events(rows, "gather"), [])


@requires_v11
class Hieunang(unittest.TestCase):
    """AC-P2-11 — hiệu năng headless."""

    def test_perf_01_one_day_under_20s(self):
        with Workdir() as w:
            t0 = time.time()
            code, err = run_headless("--mode", "day", "--days", "1", "--seed", "1", "--ticks", "22200",
                                     "--snapshot-every", "60", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            self.assertLessEqual(time.time() - t0, 20, "một Ngày không pause phải ≤ 20 s trên máy chấm")


if __name__ == "__main__":
    unittest.main()
