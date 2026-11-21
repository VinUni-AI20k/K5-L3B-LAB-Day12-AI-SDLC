"""Test lát Lặn & Hái (gather), kiểu HỘP ĐEN: chạy `headless_cmd` trong game.contract.json rồi đọc JSONL/file kho.

Đối chiếu DocsPhase.txt, PRD-0 Phase 1: mục D (scenario), E (payload event, snapshot), F (thứ tự một bước "Gather").
Số liệu đọc từ game.contract.json. Mọi fixture tắt cá mặc định (`random_fish: false`) và khai nút/đàn tường minh để
không phụ thuộc dữ liệu mặc định của phase sau.

Phase 2 (v1.1, lớp FishV11*): test mức sim gọi thẳng `Session` của starter Python, vì manifest trên main còn v1.0;
tuning chuẩn Ticket-02 nạp từ docs/contracts/phase-2.tuning.json cho tới khi game.contract.json lên v1.1.

Chạy: PYTHONPATH=tests:. python3 -m unittest discover -s tests -p 'test_gather.py' -v
"""

import json
import math
import os
import unittest

from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.runner import Session
from chonoi.sim.gather import GatherSim
from helpers import (ROOT, Workdir, events, frames, ingredient_fixture, item_schema_enabled,
                     read_jsonl, run_headless, snapshots, stock_counts, write_json)

TICK = 60

with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as _f:
    G = json.load(_f)["tuning"]["gather"]

SD = G["surface_depth"]
SPEED = G["swim_speed"]
STEP = SPEED / TICK  # quãng bơi mỗi tick ở vận tốc đích
OXY_MAX = int(round(G["oxygen_max_s"] * TICK))
REFILL = G["oxygen_refill_per_tick"]
CHOKE = G["choke_interval_ticks"]
HP = G["hp_max"]
UNDER = [20, 10]  # dưới nước, ngoài bến, quanh đó không có nút/đàn
R_INTERACT = G["interact_radius"]
R_CATCH = G["catch_radius"]
CAP = G["hold_capacity"]
NODE_YIELD = G["node_yield"]
FISH_YIELD = G["fish_yield"]
REGROW = int(round(G["regrow_s"] * TICK))
CATCH_CD = int(round(G["catch_cooldown_s"] * TICK))
DOCK = G["dock_pos"]
DOCK_R = G["dock_radius"]
TIE = 0.5  # độ lệch biểu diễn chính xác, nằm trong mọi bán kính hợp lệ (0.5–5 m) -> hòa khoảng cách thật
PRESS_E = [{"tick": 0, "interact": True}]
PRESS_SPACE = [{"tick": 0, "catch": True}]


def node(nid, x, kind="bong_sung", regrow=0):
    return {"id": nid, "kind": kind, "pos": [x, 0], "regrow_ticks": regrow}


def school(fid, pos, kind="ca_linh"):
    return {"id": fid, "kind": kind, "pos": pos}


def ev(rows, name):
    """[(tick, data)] của mọi event `name`, theo thứ tự ghi."""
    return [(r["tick"], r["data"]) for r in events(rows, name)]


def at(rows):
    """Snapshot theo tick."""
    return {s["tick"]: s for s in snapshots(rows)}


class GatherCase(unittest.TestCase):
    def play(self, block, inputs=(), ticks=1, every=1, inventory_out=False, existing=None):
        """Chạy gather với fixture `block` (mặc định không cá, không nút); trả các dòng JSONL.

        inventory_out=True: thêm --inventory-out, trả (rows, byte file kho hoặc None nếu file không tồn tại).
        existing: byte ghi sẵn vào file đích trước khi chạy (kiểm giữ nguyên đường dẫn đích).
        """
        scenario = {"gather": {"random_fish": False, "nodes": [], "fish": [], **block}}
        if "hold" in block:
            scenario["gather"]["hold"] = ingredient_fixture(block["hold"])
        with Workdir() as w:
            args = ["--mode", "gather", "--seed", "1", "--ticks", str(ticks), "--snapshot-every", str(every),
                    "--scenario", write_json(w.path("sc.json"), scenario), "--out", w.path("o.jsonl")]
            if inputs:
                args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
            inv = w.path("kho.json")
            if existing is not None:
                with open(inv, "wb") as f:
                    f.write(existing)
            if inventory_out:
                args += ["--inventory-out", inv]
            code, err = run_headless(*args)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            # Hồi quy luật P1 đối chiếu theo loại. Kiểm schema, ID và độ tươi riêng ở v1.2.
            if item_schema_enabled():
                for snapshot in snapshots(rows):
                    snapshot["hold"] = [item["kind"] for item in snapshot["hold"]]
                for row in events(rows):
                    data = row["data"]
                    if row["name"] == "gather_end":
                        data["inventory"]["items"] = stock_counts(data["inventory"]["items"])
                    if "lost" in data:
                        data["lost"] = [item["kind"] for item in data["lost"]]
            if not inventory_out:
                return rows
            if not os.path.exists(inv):
                return rows, None
            with open(inv, "rb") as f:
                stored = f.read()
            if item_schema_enabled() and existing is None:
                stored = json.dumps({"items": stock_counts(json.loads(stored)["items"])}).encode()
            return rows, stored


class SwimOxygenChoke(GatherCase):
    """AC-P1-01: dive/surface theo vị trí sau bước bơi, oxy theo d cuối bước, ngạt."""

    def test_dive_when_crossing_surface_after_move(self):
        d0 = 0.4
        k = next(k for k in range(1, TICK) if d0 + k * STEP > SD)  # vel = vận tốc đích nên d tăng đều STEP
        rows = self.play({"player": {"pos": [20, d0], "vel": [0, SPEED]}}, [{"tick": 0, "move": [0, 1]}], ticks=k + 2)
        dive = ev(rows, "dive")
        self.assertEqual([t for t, _ in dive], [k])
        self.assertGreater(dive[0][1]["pos"][1], SD)
        self.assertEqual(ev(rows, "surface"), [])

    def test_surface_when_crossing_surface_after_move(self):
        d0 = SD + STEP / 2  # nửa bước dưới biên: một bước bơi lên là qua biên
        rows = self.play({"player": {"pos": [20, d0], "vel": [0, -SPEED]}}, [{"tick": 0, "move": [0, -1]}], ticks=2)
        surface = ev(rows, "surface")
        self.assertEqual([t for t, _ in surface], [1])
        self.assertLessEqual(surface[0][1]["pos"][1], SD)
        self.assertEqual(ev(rows, "dive"), [])

    def test_no_dive_or_surface_without_crossing(self):
        for pos in ([20, 0], UNDER):  # bơi ngang trên mặt nước / dưới nước
            rows = self.play({"player": {"pos": pos}}, [{"tick": 0, "move": [1, 0]}], ticks=30)
            self.assertEqual(ev(rows, "dive") + ev(rows, "surface"), [], pos)

    def test_oxygen_minus_one_underwater_plus_refill_at_surface_clamped(self):
        n = 20
        s = at(self.play({"player": {"pos": UNDER}}, ticks=n))
        self.assertEqual([s[k]["player"]["oxygen_ticks"] for k in range(n + 1)], [OXY_MAX - k for k in range(n + 1)])
        start = max(0, OXY_MAX - 3 * REFILL - 1)  # chạm trần ở tick 4
        s = at(self.play({"player": {"pos": [20, 0], "oxygen_ticks": start}}, ticks=6))
        self.assertEqual([s[k]["player"]["oxygen_ticks"] for k in range(7)],
                         [min(OXY_MAX, start + REFILL * k) for k in range(7)])

    def test_oxygen_empty_once_when_reaching_zero(self):
        rows = self.play({"player": {"pos": UNDER, "oxygen_ticks": 3}}, ticks=10)
        self.assertEqual(ev(rows, "oxygen_empty"), [(3, {"oxygen_ticks": 0})])

    def test_first_choke_at_t_plus_59_counting_the_empty_step(self):
        """Mục F: chạm oxy 0 ở t, ở dưới nước liên tục -> ngạt lần đầu ở t+59, rồi mỗi choke_interval_ticks."""
        rows = self.play({"player": {"pos": UNDER, "oxygen_ticks": 1}}, ticks=1 + 2 * CHOKE)
        self.assertEqual(ev(rows, "oxygen_empty"), [(1, {"oxygen_ticks": 0})])
        t1 = 1 + CHOKE - 1
        self.assertEqual(ev(rows, "choke"), [(t1, {"hp": HP - 1}), (t1 + CHOKE, {"hp": HP - 2})])
        s = at(rows)
        self.assertEqual(s[t1 - 1]["player"]["zero_oxy_ticks"], CHOKE - 1)
        self.assertEqual((s[t1]["player"]["zero_oxy_ticks"], s[t1]["player"]["hp"]), (0, HP - 1))

    def test_choke_continues_counter_from_scenario(self):
        rows = self.play({"player": {"pos": UNDER, "oxygen_ticks": 0, "zero_oxy_ticks": CHOKE - 1}}, ticks=2)
        self.assertEqual(ev(rows, "choke"), [(1, {"hp": HP - 1})])
        self.assertEqual(ev(rows, "oxygen_empty"), [], "oxy đã 0 từ đầu: không phát lại oxygen_empty")

    def test_surfacing_on_the_choke_step_refills_without_choke(self):
        d0 = SD + STEP / 2
        player = {"pos": [20, d0], "vel": [0, -SPEED], "oxygen_ticks": 0, "zero_oxy_ticks": CHOKE - 1}
        rows = self.play({"player": player}, [{"tick": 0, "move": [0, -1]}], ticks=1)
        self.assertEqual([t for t, _ in ev(rows, "surface")], [1])
        self.assertEqual(ev(rows, "choke"), [])
        p = at(rows)[1]["player"]
        self.assertEqual((p["oxygen_ticks"], p["zero_oxy_ticks"], p["hp"]), (min(OXY_MAX, REFILL), 0, HP))

    def test_dive_then_oxygen_empty_in_processing_order(self):
        d0 = SD - STEP / 2  # nửa bước trên biên: một bước bơi xuống là qua biên
        rows = self.play({"player": {"pos": [20, d0], "vel": [0, SPEED], "oxygen_ticks": 1}},
                         [{"tick": 0, "move": [0, 1]}], ticks=1)
        self.assertEqual([r["name"] for r in events(rows) if r["tick"] == 1], ["dive", "oxygen_empty"])


class GatherCatch(GatherCase):
    """AC-P1-02 (hái, bắt) và giỏ của AC-P1-01: chọn ứng viên, lấy đủ hoặc giữ nguyên, mọc lại, hồi chiêu."""

    def test_prd_example_gathers_node_at_interact_radius_edge(self):
        """Scenario mẫu mục D (nút đúng mép bán kính hái) và dòng event mẫu mục E."""
        block = {"player": {"pos": [20, 0], "heading_deg": 0}, "hold": ["ca_loc", "bong_sung"],
                 "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [20 + R_INTERACT, 0]}], "time_left_ticks": 120}
        rows = self.play(block, PRESS_E, ticks=1)
        self.assertEqual(events(rows, "gather"), [{"type": "event", "tick": 1, "phase": "gather", "name": "gather",
                                                    "data": {"node_id": "N1", "kind": "bong_dien_dien",
                                                             "amount": NODE_YIELD}}])
        s = at(rows)[1]
        self.assertEqual(s["hold"], ["ca_loc", "bong_sung"] + ["bong_dien_dien"] * NODE_YIELD)
        self.assertEqual(s["hold_count"], 2 + NODE_YIELD)
        self.assertEqual([(n["id"], n["ready"], n["regrow_ticks"]) for n in s["nodes"]], [("N1", False, REGROW)])

    def test_gather_tie_on_distance_prefers_smaller_numeric_id(self):
        block = {"player": {"pos": [20, 0]}, "nodes": [node("N10", 20 + TIE), node("N2", 20 - TIE)]}
        rows = self.play(block, PRESS_E, ticks=1)
        self.assertEqual([d["node_id"] for _, d in ev(rows, "gather")], ["N2"])

    def test_gather_skips_node_not_ready(self):
        block = {"player": {"pos": [20, 0]}, "nodes": [node("N1", 20 + TIE / 2, regrow=50), node("N2", 20 + TIE)]}
        rows = self.play(block, PRESS_E, ticks=1)
        self.assertEqual([d["node_id"] for _, d in ev(rows, "gather")], ["N2"])

    def test_node_regrown_after_regrow_ticks_and_gatherable_in_same_step(self):
        """Mục F: nút từ 1 về 0 phát node_regrown và hái được ngay trong bước đó."""
        inputs = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False}, {"tick": REGROW, "interact": True}]
        rows = self.play({"player": {"pos": [20, 0]}, "nodes": [node("N1", 20)]}, inputs,
                         ticks=REGROW + 1, every=REGROW + 1)
        self.assertEqual([t for t, _ in ev(rows, "gather")], [1, REGROW + 1])
        self.assertEqual(ev(rows, "node_regrown"), [(REGROW + 1, {"node_id": "N1"})])
        self.assertEqual([r["name"] for r in events(rows) if r["tick"] == REGROW + 1], ["node_regrown", "gather"])

    def test_interact_gathers_nothing_underwater_or_out_of_range(self):
        cases = {"mặt nước, nút ngoài tầm": [20 + R_INTERACT + 1, 0]}
        if R_INTERACT > SD:
            cases["dưới nước, nút trong tầm"] = [20, (SD + R_INTERACT) / 2]
        for label, pos in cases.items():
            rows = self.play({"player": {"pos": pos}, "nodes": [node("N1", 20)]}, PRESS_E, ticks=1)
            self.assertEqual(ev(rows, "gather") + ev(rows, "hold_full"), [], label)
            self.assertEqual(at(rows)[1]["hold"], [], label)

    def test_gather_hold_full_keeps_node_ready(self):
        block = {"player": {"pos": [20, 0]}, "hold": ["ca_loc"] * CAP, "nodes": [node("N1", 20)]}
        rows = self.play(block, PRESS_E, ticks=1)
        self.assertEqual(ev(rows, "hold_full"),
                         [(1, {"action": "gather", "node_id": "N1", "required": NODE_YIELD, "free": 0})])
        self.assertEqual(ev(rows, "gather"), [])
        s = at(rows)[1]
        self.assertEqual((s["hold_count"], s["nodes"][0]["ready"], s["nodes"][0]["regrow_ticks"]), (CAP, True, 0))

    def test_catch_at_radius_edge_takes_whole_yield_removes_school_sets_cooldown(self):
        rows = self.play({"player": {"pos": [30, 10 + R_CATCH]}, "fish": [school("F1", [30, 10])]}, PRESS_SPACE, ticks=1)
        y = FISH_YIELD["ca_linh"]
        self.assertEqual(ev(rows, "fish_caught"), [(1, {"fish_id": "F1", "kind": "ca_linh", "yield": y})])
        s = at(rows)[1]
        self.assertEqual((s["hold"], s["fish"], s["player"]["catch_cd_ticks"]), (["ca_linh"] * y, [], CATCH_CD))

    @unittest.skipIf(CATCH_CD < 3, "cần hồi chiêu >= 3 tick để dựng frame bấm lại")
    def test_catch_cooldown_set_at_t_reusable_from_t_plus_L(self):
        block = {"player": {"pos": [30, 12]}, "fish": [school("F1", [30, 12 - TIE]), school("F2", [30, 12 + 2 * TIE], "ca_loc")]}
        for press, caught in ((CATCH_CD - 1, ["F1"]), (CATCH_CD, ["F1", "F2"])):
            inputs = [{"tick": 0, "catch": True}, {"tick": 1, "catch": False}, {"tick": press, "catch": True}]
            rows = self.play(block, inputs, ticks=press + 1, every=press + 1)
            self.assertEqual([d["fish_id"] for _, d in ev(rows, "fish_caught")], caught, press)

    def test_catch_does_nothing_at_surface_or_without_school_in_range(self):
        cases = {"mặt nước, đàn trong tầm": ([30, 0], [30, 1]),
                 "dưới nước, không đàn trong tầm": ([30, 10], [30, 10 + R_CATCH + 1])}
        for label, (pos, fish_pos) in cases.items():
            rows = self.play({"player": {"pos": pos}, "fish": [school("F1", fish_pos)]}, PRESS_SPACE, ticks=1)
            self.assertEqual(ev(rows, "fish_caught") + ev(rows, "hold_full"), [], label)
            s = at(rows)[1]
            self.assertEqual((s["player"]["catch_cd_ticks"], [f["id"] for f in s["fish"]]), (0, ["F1"]), label)

    def test_catch_hold_full_keeps_school_and_cooldown_without_trying_other_school(self):
        y_linh, y_loc = FISH_YIELD["ca_linh"], FISH_YIELD["ca_loc"]
        free = y_linh - 1  # thiếu chỗ cho đàn linh gần nhất, nhưng đủ cho đàn lóc xa hơn
        self.assertLessEqual(y_loc, free, "fixture cần đàn xa hơn vừa chỗ để chứng minh không thử đàn khác")
        block = {"player": {"pos": [30, 12]}, "hold": ["bong_sung"] * (CAP - free),
                 "fish": [school("F1", [30, 12 - TIE]), school("F2", [30, 12 + 2 * TIE], "ca_loc")]}
        rows = self.play(block, PRESS_SPACE, ticks=1)
        self.assertEqual(ev(rows, "hold_full"),
                         [(1, {"action": "catch", "fish_id": "F1", "required": y_linh, "free": free})])
        self.assertEqual(ev(rows, "fish_caught"), [])
        s = at(rows)[1]
        self.assertEqual(([f["id"] for f in s["fish"]], s["player"]["catch_cd_ticks"], s["hold_count"]),
                         (["F1", "F2"], 0, CAP - free))

    def test_catch_tie_on_distance_prefers_smaller_numeric_id(self):
        block = {"player": {"pos": [30, 12]}, "fish": [school("F10", [30, 12 + TIE]), school("F2", [30, 12 - TIE])]}
        rows = self.play(block, PRESS_SPACE, ticks=1)
        self.assertEqual([d["fish_id"] for _, d in ev(rows, "fish_caught")], ["F2"])


class EndOfShift(GatherCase):
    """AC-P1-01 (ngất) và AC-P1-02 (cập bến, bàn giao kho): lý do kết thúc, thứ tự ưu tiên, file kho."""

    def names(self, rows):
        return [(r["tick"], r["name"]) for r in events(rows)]

    def test_faint_drops_hold_lifo_and_hands_over_empty_inventory(self):
        player = {"pos": UNDER, "hp": 1, "oxygen_ticks": 0, "zero_oxy_ticks": CHOKE - 1}
        rows, inv = self.play({"player": player, "hold": ["ca_loc", "bong_sung", "ca_linh"]}, ticks=5,
                              inventory_out=True)
        self.assertEqual([(r["tick"], r["name"], r["data"]) for r in events(rows)], [
            (1, "choke", {"hp": 0}),
            (1, "faint", {"cause": "choke", "lost": ["ca_linh", "bong_sung", "ca_loc"], "hp": 0}),
            (1, "gather_end", {"reason": "fainted", "inventory": {"items": {}}})])
        self.assertEqual(json.loads(inv), {"items": {}})
        last = snapshots(rows)[-1]
        self.assertEqual((last["tick"], last["state"], last["hold"], last["hold_count"], last["player"]["hp"]),
                         (1, "finished", [], 0, 0))
        self.assertEqual((rows[-1]["type"], rows[-1]["reason"], rows[-1]["ticks"]), ("end", "fainted", 1))

    @unittest.skipIf(DOCK_R <= SD, "cần vùng bến chạm xuống dưới mặt nước")
    def test_faint_goes_before_dock_and_time_on_the_same_step(self):
        """Mục F: E ở bến bước cuối chỉ cho docked nếu còn Máu."""
        player = {"pos": [DOCK[0], (SD + DOCK_R) / 2], "hp": 1, "oxygen_ticks": 0, "zero_oxy_ticks": CHOKE - 1}
        rows, inv = self.play({"player": player, "hold": ["ca_loc"], "time_left_ticks": 1}, PRESS_E, ticks=5,
                              inventory_out=True)
        self.assertEqual(self.names(rows), [(1, "choke"), (1, "faint"), (1, "gather_end")])
        self.assertEqual((ev(rows, "gather_end")[0][1]["reason"], rows[-1]["reason"]), ("fainted", "fainted"))
        self.assertEqual(json.loads(inv), {"items": {}})

    def test_dock_goes_before_gather_and_catch(self):
        cases = {"mặt nước, nút trong tầm": ({"pos": list(DOCK)}, {"nodes": [node("N1", DOCK[0] + TIE)]}, PRESS_E)}
        if DOCK_R > SD:
            d = (SD + DOCK_R) / 2
            cases["dưới nước, đàn trong tầm, E + Space cùng tick"] = (
                {"pos": [DOCK[0], d]}, {"fish": [school("F1", [DOCK[0], d + TIE])]},
                [{"tick": 0, "interact": True, "catch": True}])
        for label, (player, extra, inputs) in cases.items():
            rows, inv = self.play({"player": player, "hold": ["ca_loc"], **extra}, inputs, ticks=5, inventory_out=True)
            self.assertEqual(self.names(rows), [(1, "gather_end")], label)
            self.assertEqual(ev(rows, "gather_end")[0][1], {"reason": "docked", "inventory": {"items": {"ca_loc": 1}}},
                             label)
            self.assertEqual(json.loads(inv), {"items": {"ca_loc": 1}}, label)

    def test_interact_at_exact_dock_edge_on_last_step_docks(self):
        """Mục F: E đúng mép bến ở bước cuối vẫn cho docked (cập bến xét trước hết giờ)."""
        block = {"player": {"pos": [DOCK[0] + DOCK_R, 0]}, "hold": ["bong_sung"], "time_left_ticks": 1}
        rows, inv = self.play(block, PRESS_E, ticks=5, inventory_out=True)
        self.assertEqual(ev(rows, "gather_end"), [(1, {"reason": "docked", "inventory": {"items": {"bong_sung": 1}}})])
        self.assertEqual(rows[-1]["reason"], "docked")
        self.assertEqual(json.loads(inv), {"items": {"bong_sung": 1}})

    def test_valid_gather_or_catch_on_last_step_is_handed_over(self):
        y = FISH_YIELD["ca_linh"]
        cases = {"hái": ({"player": {"pos": [20, 0]}, "nodes": [node("N1", 20 + TIE)]}, PRESS_E, "gather",
                         {"bong_sung": NODE_YIELD}),
                 "bắt": ({"player": {"pos": [30, 12]}, "fish": [school("F1", [30, 12 - TIE])]}, PRESS_SPACE,
                         "fish_caught", {"ca_linh": y})}
        for label, (block, inputs, action, items) in cases.items():
            rows, inv = self.play({**block, "time_left_ticks": 1}, inputs, ticks=5, inventory_out=True)
            self.assertEqual(self.names(rows), [(1, action), (1, "gather_end")], label)
            self.assertEqual(ev(rows, "gather_end")[0][1], {"reason": "time", "inventory": {"items": items}}, label)
            self.assertEqual(json.loads(inv), {"items": items}, label)

    def test_tick_limit_before_gather_end_keeps_existing_file_bytes(self):
        before = b'{"items":{"ca_loc":9}}\n'
        rows, inv = self.play({"player": {"pos": UNDER}, "hold": ["ca_linh"]}, ticks=5, inventory_out=True,
                              existing=before)
        self.assertEqual(rows[-1]["reason"], "tick_limit")
        self.assertEqual(inv, before)

    def test_same_seed_same_inputs_give_identical_bytes(self):
        """Mục E: cùng seed, tham số, đầu vào -> JSONL và file kho giống từng byte; kịch bản có đủ hành động."""
        block = {"random_fish": False, "player": {"pos": [20, 0]}, "nodes": [node("N1", 20 + TIE)],
                 "fish": [school("F1", [20, 3])]}
        inputs = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False, "move": [0, 1]},
                  {"tick": 45, "move": [0, 0], "catch": True}, {"tick": 46, "catch": False, "move": [-0.986, -0.164]},
                  {"tick": 400, "move": [0, 0], "interact": True}]
        outs = []
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": block})
            inp = write_json(w.path("in.json"), frames(*inputs))
            for i in (1, 2):
                code, err = run_headless("--mode", "gather", "--seed", "7", "--ticks", "600", "--scenario", sc,
                                         "--inputs", inp, "--snapshot-every", "1", "--inventory-out", w.path(f"k{i}.json"),
                                         "--out", w.path(f"o{i}.jsonl"))
                self.assertEqual(code, 0, err)
                with open(w.path(f"o{i}.jsonl"), "rb") as a, open(w.path(f"k{i}.json"), "rb") as b:
                    outs.append((a.read(), b.read()))
            rows = read_jsonl(w.path("o1.jsonl"))
        self.assertEqual(outs[0], outs[1])
        self.assertEqual([n for _, n in self.names(rows)], ["gather", "dive", "fish_caught", "surface", "gather_end"])
        self.assertEqual(rows[-1]["reason"], "docked")


# --- Phase 2 (Test Contract v1.1) --------------------------------------------------------------------------------

def _merge(base, delta):
    """Gộp delta tuning theo docs/contracts/phase-2.md: object gộp theo khóa, danh sách/giá trị đơn thay toàn bộ."""
    out = dict(base)
    for k, v in delta.items():
        out[k] = _merge(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return out


def tuning_v11():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        contract = json.load(f)
    if tuple(int(x) for x in contract["contract_version"].split(".")) >= (1, 1):
        return contract["tuning"]
    with open(os.path.join(ROOT, "docs", "contracts", "phase-2.tuning.json"), encoding="utf-8") as f:
        return _merge(contract["tuning"], json.load(f)["tuning"])


V11 = tuning_v11()
V11.pop("freshness", None)
GV = V11["gather"]
FSTEP = GV["fish_speed"] / TICK  # quãng cá bơi mỗi tick
IDLE = InputState((0.0, 0.0), {}, set())


def press(*names):
    return InputState((0.0, 0.0), {n: True for n in names}, set(names))


class FishV11Case(unittest.TestCase):
    def session(self, scenario=None, seed=42):
        return Session("gather", V11, scenario or {}, seed)

    @staticmethod
    def steps(s, n, inp=IDLE):
        """Chạy tối đa n bước như runner (dừng khi buổi kết thúc); bước đầu dùng `inp`, các bước sau không bấm gì.
        Trả [(tick, name, data)]."""
        out = []
        for i in range(n):
            if s.done:
                break
            out += [(r["tick"], r["name"], r["data"]) for r in s.step(inp if i == 0 else IDLE)]
        return out

    @staticmethod
    def fishmap(s):
        """Bản chép các đàn trong snapshot hiện tại, theo id."""
        return {f["id"]: {"kind": f["kind"], "pos": list(f["pos"]), "heading_deg": f["heading_deg"],
                          "age_ticks": f["age_ticks"]} for f in s.snapshot()["fish"]}


class FishV11SwimSpawn(FishV11Case):
    """AC-P2-01: 8 đàn đầu ca, bơi, đổi hướng 120, phản xạ, sinh mỗi 360, trần 12, random_fish:false, N5/N6."""

    def test_initial_schools_on_distinct_spawn_points_by_seed(self):
        fish = self.fishmap(self.session())
        self.assertEqual(set(fish), {f"F{i}" for i in range(1, GV["fish_initial"] + 1)})
        self.assertEqual(len({tuple(f["pos"]) for f in fish.values()}), GV["fish_initial"], "điểm khác nhau")
        for f in fish.values():
            self.assertIn(f["pos"][0], GV["fish_spawn_x"])
            self.assertIn(f["pos"][1], GV["fish_spawn_depths"][f["kind"]])
            self.assertEqual(f["age_ticks"], 0)
        self.assertEqual(self.fishmap(self.session()), fish, "cùng seed -> cùng bố trí")
        self.assertNotEqual(self.fishmap(self.session(seed=7)), fish, "seed khác -> bố trí khác")

    def test_schools_stay_in_x_domain_and_species_depth_band(self):
        s = self.session()
        lo_x, hi_x = GV["fish_x"]
        for _ in range(3000):
            s.step(IDLE)
            for f in s.snapshot()["fish"]:
                lo_d, hi_d = GV["fish_depths"][f["kind"]]
                self.assertTrue(lo_x <= f["pos"][0] <= hi_x and lo_d <= f["pos"][1] <= hi_d, f)

    def test_swim_speed_and_turn_at_swim_step_120_before_moving(self):
        turn = GV["fish_turn_ticks"]
        lo, hi = GV["fish_depths"]["ca_keo"]
        start = [50.0, (lo + hi) / 2]
        s = self.session({"fish": [{"id": "F1", "kind": "ca_keo", "pos": start, "heading_deg": 0}]})
        traj = []
        for _ in range(turn):
            s.step(IDLE)
            f = s.snapshot()["fish"][0]
            traj.append((list(f["pos"]), f["heading_deg"], f["age_ticks"]))
        for k, (pos, h, age) in enumerate(traj[:-1], start=1):  # bước bơi 1..119: giữ hướng 0, đi đúng FSTEP
            self.assertEqual((h, age), (0.0, k))
            self.assertAlmostEqual(pos[0], start[0] + k * FSTEP, places=9)
            self.assertEqual(pos[1], start[1])
        (pos, h, age), prev = traj[-1], traj[-2][0]  # bước bơi thứ 120: đổi hướng TRƯỚC khi đi
        self.assertEqual(age, turn)
        self.assertNotEqual(h, 0.0)
        self.assertAlmostEqual(pos[0] - prev[0], FSTEP * math.cos(math.radians(h)), places=9)
        self.assertAlmostEqual(pos[1] - prev[1], FSTEP * math.sin(math.radians(h)), places=9)
        s = self.session({"fish": [{"id": "F1", "kind": "ca_keo", "pos": start, "heading_deg": 0,
                                    "age_ticks": turn - 1}]})
        s.step(IDLE)
        f = s.snapshot()["fish"][0]
        self.assertEqual(f["age_ticks"], turn)
        self.assertNotEqual(f["heading_deg"], 0.0, "age_ticks từ fixture: bước bơi kế là bước thứ 120")

    def test_reflects_remaining_distance_and_flips_perpendicular_component(self):
        lo_x, hi_x = GV["fish_x"]
        lo, hi = GV["fish_depths"]["ca_keo"]
        mid, c = (lo + hi) / 2, FSTEP * math.cos(math.radians(45))
        cases = {  # nhãn: (vị trí đầu = vị trí sau một bước phản xạ, hướng đầu, hướng sau)
            "mép x phải": ([hi_x - FSTEP / 2, mid], 0, 180),
            "mép x trái": ([lo_x + FSTEP / 2, mid], 180, 0),
            "đáy dải độ sâu": ([50, hi - FSTEP / 2], 90, 270),
            "đỉnh dải độ sâu": ([50, lo + FSTEP / 2], 270, 90),
            "góc": ([hi_x - c / 2, hi - c / 2], 45, 225),
        }
        for label, (pos, h, want_h) in cases.items():
            s = self.session({"fish": [{"id": "F1", "kind": "ca_keo", "pos": pos, "heading_deg": h}]})
            s.step(IDLE)
            f = s.snapshot()["fish"][0]
            self.assertAlmostEqual(f["pos"][0], pos[0], places=9, msg=label)
            self.assertAlmostEqual(f["pos"][1], pos[1], places=9, msg=label)
            self.assertAlmostEqual(math.cos(math.radians(f["heading_deg"] - want_h)), 1.0, places=9, msg=label)

    def test_spawn_one_school_at_each_360_phase_ticks_after_swimming(self):
        every, n0 = GV["fish_spawn_ticks"], GV["fish_initial"]
        k_max = min(3, GV["fish_max"] - n0)
        s, log, snaps = self.session(), [], {}
        for t in range(1, every * k_max + 2):
            log += [(r["tick"], r["name"], r["data"]) for r in s.step(IDLE)]
            if t % every in (0, 1):
                snaps[t] = self.fishmap(s)
        spawned = [(t, d) for t, n, d in log if n == "fish_spawned"]
        self.assertEqual([t for t, _ in spawned], [every * k for k in range(1, k_max + 1)])
        self.assertEqual([d["id"] for _, d in spawned], [f"F{n0 + k}" for k in range(1, k_max + 1)])
        for t, d in spawned:
            fish = snaps[t]
            self.assertIn(d["pos"][0], GV["fish_spawn_x"])
            self.assertIn(d["pos"][1], GV["fish_spawn_depths"][d["kind"]])
            self.assertEqual((fish[d["id"]]["pos"], fish[d["id"]]["age_ticks"]), (d["pos"], 0), "chưa bơi ở bước sinh")
            others = [f["pos"] for i, f in fish.items() if i != d["id"]]
            self.assertTrue(all(math.dist(d["pos"], q) > GV["fish_spawn_clearance"] for q in others))
            self.assertEqual(snaps[t + 1][d["id"]]["age_ticks"], 1, "bơi từ bước sau")

    def test_no_spawn_at_fish_max_and_spawn_resumes_below_it(self):
        every, cap = GV["fish_spawn_ticks"], GV["fish_max"]
        lo, hi = GV["fish_depths"]["ca_keo"]

        def schools(n):
            return [{"id": f"F{i}", "kind": "ca_keo", "pos": [5 + 7 * i, (lo + hi) / 2], "heading_deg": 90}
                    for i in range(1, n + 1)]
        log = self.steps(self.session({"fish": schools(cap)}), every + 1)
        self.assertEqual([e for e in log if e[1] == "fish_spawned"], [])
        log = self.steps(self.session({"fish": schools(cap - 1)}), 2 * every + 1)
        self.assertEqual([(t, d["id"]) for t, n, d in log if n == "fish_spawned"], [(every, f"F{cap}")])

    def test_spawn_needs_clearance_renormalizes_species_and_skips_without_point(self):
        """Cá fixture đứng yên (delta fish_speed 0, trần nới rộng) chiếm sẵn điểm sinh để kiểm từng nhánh luật sinh."""
        still = _merge(V11, {"gather": {"fish_speed": 0.0, "fish_max": 64}})
        every = GV["fish_spawn_ticks"]
        depth_kind = {}  # độ sâu điểm sinh -> một loài sinh ở độ sâu đó (điểm hình học dùng chung giữa loài)
        for kind, depths in GV["fish_spawn_depths"].items():
            for d in depths:
                depth_kind.setdefault(d, kind)
        grid = sorted({(x, d) for x in GV["fish_spawn_x"] for d in depth_kind})

        def spawned(blocked, seed):
            fish = [{"id": f"F{i}", "kind": depth_kind[d], "pos": [x, d]} for i, (x, d) in enumerate(blocked, 1)]
            return [d for _, n, d in self.steps(Session("gather", still, {"fish": fish}, seed), every)
                    if n == "fish_spawned"]
        for seed in range(10):  # điểm đã có cá không được chọn lại (cách mọi đàn > clearance)
            got = spawned(grid[:11], seed)
            self.assertEqual(len(got), 1, seed)
            self.assertNotIn(tuple(got[0]["pos"]), set(grid[:11]), seed)
        keo = set(GV["fish_spawn_depths"]["ca_keo"])
        for seed in range(10):  # loài khác hết điểm -> trọng số chuẩn hóa chỉ còn cá kèo
            got = spawned([p for p in grid if p[1] not in keo], seed)
            self.assertEqual([d["kind"] for d in got], ["ca_keo"], seed)
        self.assertEqual(spawned(grid, 0), [], "hết điểm hình học -> bỏ lượt")

    def test_random_fish_false_keeps_fixture_static_without_turn_or_spawn(self):
        age = GV["fish_turn_ticks"] - 1
        s = self.session({"random_fish": False, "fish": [{"id": "F1", "kind": "ca_loc", "pos": [50, 10],
                                                          "heading_deg": 0, "age_ticks": age}]})
        log = self.steps(s, GV["fish_spawn_ticks"] + 1)
        self.assertEqual([e for e in log if e[1] == "fish_spawned"], [])
        self.assertEqual(self.fishmap(s), {"F1": {"kind": "ca_loc", "pos": [50.0, 10.0], "heading_deg": 0,
                                                  "age_ticks": age}})
        self.assertEqual(self.fishmap(self.session({"random_fish": False})), {}, "không fixture -> không cá")

    def test_catch_uses_school_position_before_it_swims(self):
        fish = [{"id": "F1", "kind": "ca_loc", "pos": [50, 12 + GV["catch_radius"]], "heading_deg": 90}]  # đúng mép,
        s = self.session({"player": {"pos": [50, 12]}, "fish": fish})                                       # bơi ra xa
        self.assertEqual([(n, d) for _, n, d in self.steps(s, 1, press("catch"))],
                         [("fish_caught", {"fish_id": "F1", "kind": "ca_loc", "yield": GV["fish_yield"]["ca_loc"]})])

    def test_two_keo_neo_nodes_n5_n6_are_gatherable(self):
        nodes = {n["id"]: n for n in GV["nodes"] if n["kind"] == "keo_neo"}
        self.assertEqual(sorted(nodes), ["N5", "N6"])
        s = self.session({"player": {"pos": list(nodes["N5"]["pos"])}, "random_fish": False})
        self.assertEqual([(n, d) for _, n, d in self.steps(s, 1, press("interact"))],
                         [("gather", {"node_id": "N5", "kind": "keo_neo", "amount": GV["node_yield"]})])

    def test_same_seed_same_timeline_and_different_seed_differs(self):
        def run(seed):
            s = self.session(seed=seed)
            return self.steps(s, 1500), self.fishmap(s)
        self.assertEqual(run(42), run(42))
        self.assertNotEqual(run(42), run(7))


MON = GV["monsters"]
SAU = MON["species"]["ca_sau"]
THR = SAU["depths"][0]  # ngưỡng độ sâu của loài: phát hiện và chạm chỉ khi người chơi ở d >= THR
INVULN = MON["invuln_ticks"]
RECOIL_STEP = SAU["recoil_dist"] / SAU["recoil_ticks"]
NEAR = SAU["chase_speed"] / TICK * 0.8  # gần hơn một bước chase: quái tới đúng vị trí người chơi, khoảng cách 0


def croc(mid, pos, waypoints=None, **extra):
    return {"id": mid, "kind": "ca_sau", "pos": pos, "waypoints": waypoints or [pos, [pos[0] + 4, pos[1]]], **extra}


class MonsterV11(FishV11Case):
    """AC-P2-02: Cá Sấu theo Ngày, patrol/chase, một hit mỗi bước, rơi LIFO, bất tử, recoil, ngất."""

    def play(self, monsters, player, ticks=1, **extra):
        s = self.session({"random_fish": False, "monsters": monsters, "player": player, **extra})
        return s, self.steps(s, ticks)

    @staticmethod
    def mon(s, mid):
        return next(m for m in s.snapshot()["monsters"] if m["id"] == mid)

    def test_default_layout_by_day_m1_from_day_1_m2_from_day_3(self):
        def ids_on(day):
            return [m["id"] for m in GatherSim(V11, {}, Streams(42), IdAllocator(), day=day).snapshot()["monsters"]]
        for day in range(1, 6):
            self.assertEqual(ids_on(day), [m["id"] for m in MON["spawns"] if m["from_day"] <= day], day)
        self.assertEqual((ids_on(2), ids_on(3)), (["M1"], ["M1", "M2"]))
        m1 = self.session().snapshot()["monsters"]  # gather độc lập = bố trí Ngày 1
        self.assertEqual([(m["id"], m["pos"], m["state"], m["target_idx"]) for m in m1],
                         [("M1", [float(c) for c in MON["spawns"][0]["pos"]], "patrol", 1)])
        self.assertEqual(self.play([], {"pos": [20, 0]})[0].snapshot()["monsters"], [], "monsters: [] thay bố trí")

    def test_patrol_speed_and_switch_waypoint_after_arriving(self):
        step, wp = SAU["patrol_speed"] / TICK, [[60.0, 24.0], [64.0, 24.0]]
        n = round(math.dist(*wp) / step)  # số bước tới waypoint kia
        s = self.session({"random_fish": False, "monsters": [croc("M1", wp[0], wp)]})
        xs, idx = [], []
        for _ in range(2 * n + 1):
            s.step(IDLE)
            m = self.mon(s, "M1")
            xs.append(m["pos"][0])
            idx.append(m["target_idx"])
        for k in (1, n // 2, n - 1):
            self.assertAlmostEqual(xs[k - 1], wp[0][0] + k * step, places=9)
        self.assertEqual((xs[n - 1], idx[n - 2], idx[n - 1]), (wp[1][0], 1, 0), "tới đúng bước thứ n rồi đổi đích")
        self.assertAlmostEqual(xs[n], wp[1][0] - step, places=9)
        self.assertEqual((xs[2 * n - 1], idx[2 * n - 1]), (wp[0][0], 1))

    def test_chase_detect_and_exit_rules(self):
        cases = {  # nhãn: (quái, vị trí người chơi, trạng thái sau một bước)
            "phát hiện trong detect_radius": (croc("M1", [60, 24]), [60 - SAU["detect_radius"] + 1, 24], "chase"),
            "phát hiện đúng mép detect_radius": (croc("M1", [60, 24]), [60 - SAU["detect_radius"], 24], "chase"),
            "người chơi trên ngưỡng độ sâu": (croc("M1", [60, THR + 2]), [60, THR - 0.5], "patrol"),
            "đang chase, người chơi lên trên ngưỡng": (croc("M1", [60, THR + 2], state="chase"), [60, THR - 0.5],
                                                       "patrol"),
            "đang chase, cách quá exit_radius": (croc("M1", [60, 24], state="chase"),
                                                 [60 - SAU["exit_radius"] - 4, 24], "patrol"),
            "đang chase, giữa detect và exit": (croc("M1", [60, 24], state="chase"),
                                                [60 - (SAU["detect_radius"] + SAU["exit_radius"]) / 2, 24], "chase"),
            "đang chase, đúng mép exit_radius": (croc("M1", [60, 24], state="chase"), [60 - SAU["exit_radius"], 24],
                                                 "chase"),
        }
        for label, (m, player, want) in cases.items():
            s, _ = self.play([m], {"pos": player})
            self.assertEqual(self.mon(s, "M1")["state"], want, label)
        s, _ = self.play([croc("M1", [60, 24])], {"pos": [51, 24]})  # chase đi chase_speed về phía người chơi
        self.assertAlmostEqual(self.mon(s, "M1")["pos"][0], 60 - SAU["chase_speed"] / TICK, places=9)

    def test_hit_drops_half_lifo_sets_invuln_and_recoil_away_from_player(self):
        hold = ["ca_loc", "bong_sung", "ca_linh", "keo_neo", "ca_keo"]
        n_lost = math.floor(len(hold) * MON["loss_ratio"])
        s, log = self.play([croc("M1", [60, 24])], {"pos": [61, 24]}, hold=hold)
        self.assertEqual(log, [(1, "monster_hit", {"monster_id": "M1", "hp": HP - 1, "lost": hold[::-1][:n_lost],
                                                   "pos": [61.0, 24.0]})])
        snap = s.snapshot()
        self.assertEqual((snap["hold"], snap["player"]["hp"], snap["player"]["invuln_ticks"]),
                         (hold[:len(hold) - n_lost], HP - 1, INVULN))
        m = self.mon(s, "M1")
        self.assertEqual((m["state"], m["state_ticks_left"], m["recoil_dir"]), ("recoil", SAU["recoil_ticks"], [-1.0, 0.0]))

    def test_recoil_from_next_step_then_patrol_and_next_hit_only_after_invuln(self):
        s, log = self.play([croc("M1", [60, 24])], {"pos": [61, 24]}, ticks=1)
        x_hit = self.mon(s, "M1")["pos"][0]
        for k in range(1, SAU["recoil_ticks"] + 1):  # recoil 60 bước tính từ bước sau, lùi RECOIL_STEP mỗi bước
            log += self.steps(s, 1)
            m = self.mon(s, "M1")
            self.assertAlmostEqual(m["pos"][0], x_hit - k * RECOIL_STEP, places=9)
            left = SAU["recoil_ticks"] - k
            self.assertEqual((m["state"], m["state_ticks_left"]), ("recoil", left) if left else ("patrol", 0), k)
        log += self.steps(s, INVULN + 30 - SAU["recoil_ticks"])
        hits = [t for t, n, _ in log if n == "monster_hit"]
        self.assertEqual(hits[0], 1)
        self.assertGreaterEqual(len(hits), 2, "quái quay lại đuổi và chạm lần nữa")
        self.assertGreaterEqual(hits[1], 1 + INVULN, "không chạm trong thời gian bất tử")

    def test_one_hit_per_step_nearest_then_smaller_numeric_id(self):
        s, log = self.play([croc("M10", [61 + NEAR, 24]), croc("M2", [61 - NEAR, 24])], {"pos": [61, 24]})
        self.assertEqual([(n, d["monster_id"]) for _, n, d in log], [("monster_hit", "M2")], "hòa khoảng cách -> id")
        self.assertEqual((self.mon(s, "M2")["state"], self.mon(s, "M10")["state"]), ("recoil", "chase"))
        s, log = self.play([croc("M1", [61 - 1.2, 24]), croc("M2", [61 + 0.8, 24])], {"pos": [61, 24]})
        self.assertEqual([(n, d["monster_id"]) for _, n, d in log], [("monster_hit", "M2")], "con gần nhất chạm")

    def test_no_hit_above_species_depth_or_while_invulnerable(self):
        _, log = self.play([croc("M1", [60, THR])], {"pos": [60, THR - 0.5]}, ticks=3)
        self.assertEqual(log, [], "người chơi trên ngưỡng độ sâu: không chạm")
        _, log = self.play([croc("M1", [61 - NEAR, 24])], {"pos": [61, 24], "invuln_ticks": 5}, ticks=6)
        self.assertEqual([t for t, n, _ in log if n == "monster_hit"], [5], "bất tử 5 tick: chạm được từ tick 5")

    def test_monster_hit_to_zero_hp_faints_with_remaining_hold_lifo(self):
        hold = ["ca_loc", "bong_sung", "ca_linh"]
        s, log = self.play([croc("M1", [61 - NEAR, 24])], {"pos": [61, 24], "hp": 1}, ticks=3, hold=hold)
        self.assertEqual(log, [
            (1, "monster_hit", {"monster_id": "M1", "hp": 0, "lost": ["ca_linh"], "pos": [61.0, 24.0]}),
            (1, "faint", {"cause": "monster", "lost": ["bong_sung", "ca_loc"], "hp": 0}),
            (1, "gather_end", {"reason": "fainted", "inventory": {"items": {}}})])
        self.assertEqual((s.done, s.end_row()["reason"], s.snapshot()["hold"]), (True, "fainted", []))

    def test_choke_goes_before_hit_and_ignores_invuln_without_dropping(self):
        player = {"pos": [61, 24], "hp": 2, "oxygen_ticks": 0, "zero_oxy_ticks": CHOKE - 1}
        _, log = self.play([croc("M1", [61 - NEAR, 24])], player, hold=["ca_loc"])
        self.assertEqual([(n, d.get("hp"), d.get("cause")) for _, n, d in log],
                         [("choke", 1, None), ("monster_hit", 0, None), ("faint", 0, "monster"),
                          ("gather_end", None, None)])
        s, log = self.play([], {**player, "hp": 3, "invuln_ticks": 50}, hold=["ca_loc", "bong_sung"])
        self.assertEqual(log, [(1, "choke", {"hp": 2})])
        self.assertEqual(s.snapshot()["hold"], ["ca_loc", "bong_sung"], "ngạt không làm rơi hàng")

    def test_detection_and_contact_resume_only_the_step_after_recoil_ends(self):
        m = croc("M1", [61, 24], state="recoil", state_ticks_left=1, recoil_dir=[1.0, 0.0])
        s, log = self.play([m], {"pos": [61, 24]}, ticks=2)
        self.assertEqual([t for t, n, _ in log if n == "monster_hit"], [2])

    def test_monsters_clamped_to_map_and_species_depth_band(self):
        bx = G["bounds"]["x"]
        cases = {"lùi lên quá ngưỡng dải độ sâu": ([60, THR + RECOIL_STEP / 2], [0.0, -1.0], [60, THR]),
                 "lùi qua mép x": ([bx[1] - RECOIL_STEP / 2, 24], [1.0, 0.0], [bx[1], 24])}
        for label, (pos, rdir, want) in cases.items():
            m = croc("M1", pos, state="recoil", state_ticks_left=5, recoil_dir=rdir)
            s, _ = self.play([m], {"pos": [20, 0]})
            self.assertEqual(self.mon(s, "M1")["pos"], [float(c) for c in want], label)
        s = self.session({"random_fish": False, "monsters": [croc("M1", [60, 24])], "player": {"pos": [20, 0]}})
        self.assertEqual(set(s.snapshot()["monsters"][0]),
                         {"id", "kind", "pos", "waypoints", "target_idx", "state", "state_ticks_left", "recoil_dir"})


if __name__ == "__main__":
    unittest.main()
