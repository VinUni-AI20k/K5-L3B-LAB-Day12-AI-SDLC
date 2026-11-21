"""Lát 4 — Quán: chọn interact, nấu, bưng, phục vụ, boa, trả tiền, cuối ca (AC-P1-09, AC-P1-10).

Số liệu đọc từ game.contract.json; kịch bản dựng bằng scenario để không phụ thuộc lịch khách của lát 3.
"""

import copy
import math
import os
import unittest

from helpers import ROOT, Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim

TUNING = load_contract()["tuning"]
Q = TUNING["quan"]
MENU = TUNING["menu"]
HZ = TUNING["tick_hz"]
PATIENCE_MAX = int(round(Q["patience_s"] * HZ))
EAT_TICKS = int(round(Q["eat_s"] * HZ))
STOVE = Q["stoves"][0]
TABLE = Q["tables"][0]
FIXTURE = os.path.join(ROOT, "tests", "fixtures", "quan_one_customer.json")

PRESS = InputState((0.0, 0.0), {"interact": True}, {"interact"})
IDLE = InputState((0.0, 0.0), {}, set())


def near(pos, dz=1.0):
    """Điểm cách `pos` đúng dz theo trục z (trong interact_radius)."""
    return [pos[0], pos[1] - dz if pos[1] - dz >= Q["bounds"]["z"][0] else pos[1] + dz]


def waiting(cid="C1", dish="goi_bong_sung", **kw):
    c = {"id": cid, "table_id": TABLE["id"], "dish_id": dish, "order_tick": 0, "state": "waiting",
         "order_status": "reserved", "reserved": dict(MENU[dish]["recipe"])}
    c.update(kw)
    return c


def carried(cid="C1", dish="goi_bong_sung", patience=PATIENCE_MAX):
    return {"id": cid, "table_id": TABLE["id"], "dish_id": dish, "order_tick": 0, "state": "waiting",
            "order_status": "carried", "patience_ticks_left": patience, "base_price": MENU[dish]["price"]}


def eating(cid="C1", dish="goi_bong_sung", eat=EAT_TICKS, tip=0):
    return {"id": cid, "table_id": TABLE["id"], "dish_id": dish, "order_tick": 0, "state": "eating",
            "order_status": "served", "eat_ticks_left": eat, "base_price": MENU[dish]["price"], "tip": tip}


def run_quan(block, frame_list=(), ticks=5):
    with Workdir() as w:
        sc = write_json(w.path("sc.json"), {"quan": dict({"random_customers": False}, **block)})
        inp = write_json(w.path("in.json"), frames(*frame_list))
        out = w.path("o.jsonl")
        code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", str(ticks), "--snapshot-every", "1",
                                 "--scenario", sc, "--inputs", inp, "--out", out)
        assert code == 0, err
        return read_jsonl(out)


def names(rows):
    return [r["name"] for r in events(rows)]


def snap_at(rows, tick):
    return {r["tick"]: r for r in snapshots(rows)}[tick]


def make_sim(block, tuning=TUNING):
    return QuanSim(tuning, dict({"random_customers": False}, **block), Streams(1), IdAllocator())


class TestInteractSelection(unittest.TestCase):
    def test_stove_before_table_at_equal_distance(self):
        """Hòa khoảng cách: bếp trước bàn."""
        block = {"player": {"pos": [5, 5]}, "stock": {"bong_sung": 2},
                 "stoves": [{"id": STOVE["id"], "pos": [5, 6]}], "tables": [{"id": TABLE["id"], "pos": [5, 4]}],
                 "customers": [waiting()]}
        rows = run_quan(block, [{"tick": 0, "interact": True}], ticks=2)
        self.assertEqual(names(rows), ["cook_started"])

    def test_chosen_object_not_interactable_skips_turn(self):
        """Đối tượng được chọn (bếp đang nấu) không tương tác được -> bỏ lượt, không thử bàn."""
        tuning = copy.deepcopy(TUNING)
        tuning["quan"]["stoves"] = [{"id": "B1", "pos": [5, 6]}]
        tuning["quan"]["tables"] = [{"id": "T1", "pos": [5, 4]}, {"id": "T2", "pos": [14, 2]}]
        cooking = dict(waiting("C2"), table_id="T2", order_status="cooking", reserved={}, base_price=40)
        sim = make_sim({"player": {"pos": [5, 5]}, "stock": {},
                        "stoves": [{"id": "B1", "state": "cooking", "cook_ticks_left": 100,
                                    "dish": {"order_id": "C2", "dish_id": "goi_bong_sung"}}],
                        "hand": {"order_id": "C1", "dish_id": "goi_bong_sung"},
                        "customers": [carried(), cooking]}, tuning)
        self.assertEqual(sim.step(PRESS), [])
        self.assertEqual(sim.hand, {"order_id": "C1", "dish_id": "goi_bong_sung"})
        self.assertEqual(sim.customers[0]["state"], "waiting")

    def test_radius_edge_inclusive(self):
        """Đúng mép interact_radius vẫn tương tác được."""
        r = Q["interact_radius"]
        block = {"player": {"pos": [STOVE["pos"][0], STOVE["pos"][1] - r]}, "stock": {"bong_sung": 2},
                 "customers": [waiting()]}
        rows = run_quan(block, [{"tick": 0, "interact": True}], ticks=1)
        self.assertEqual(names(rows), ["cook_started"])

    def test_out_of_radius_nothing(self):
        r = Q["interact_radius"]
        block = {"player": {"pos": [STOVE["pos"][0], STOVE["pos"][1] - r - 0.01]}, "stock": {"bong_sung": 2},
                 "customers": [waiting()]}
        rows = run_quan(block, [{"tick": 0, "interact": True}], ticks=1)
        self.assertEqual(names(rows), [])

    def test_only_rising_edge(self):
        """Giữ E không lặp tương tác: chỉ cạnh lên."""
        block = {"player": {"pos": near(STOVE["pos"])}, "stock": {"bong_sung": 4},
                 "customers": [waiting()]}
        rows = run_quan(block, [{"tick": 0, "interact": True}], ticks=5)
        self.assertEqual(names(rows), ["cook_started"])


class TestCooking(unittest.TestCase):
    def test_cook_started_and_dish_ready(self):
        dish = "goi_bong_sung"
        cook = int(round(MENU[dish]["cook_s"] * HZ))
        block = {"player": {"pos": near(STOVE["pos"])}, "stock": {"bong_sung": 3, "ca_loc": 1},
                 "customers": [waiting(dish=dish)]}
        rows = run_quan(block, [{"tick": 0, "interact": True}], ticks=cook + 2)
        ev = events(rows, "cook_started")[0]
        self.assertEqual(ev["tick"], 1)
        self.assertEqual(ev["data"], {"stove_id": STOVE["id"], "order_id": "C1", "dish_id": dish,
                                      "items": ["bong_sung", "bong_sung"], "base_price": MENU[dish]["price"]})
        s1 = snap_at(rows, 1)
        self.assertEqual(s1["stock"], {"bong_sung": 1, "ca_loc": 1})  # tiêu đúng phần giữ
        c = s1["customers"][0]
        self.assertEqual((c["order_status"], c["reserved"], c["base_price"]), ("cooking", {}, MENU[dish]["price"]))
        self.assertEqual(s1["stoves"][0]["state"], "cooking")
        self.assertEqual(s1["stoves"][0]["cook_ticks_left"], cook)
        ready = events(rows, "dish_ready")
        self.assertEqual(len(ready), 1)
        self.assertEqual(ready[0]["tick"], 1 + cook)
        self.assertEqual(ready[0]["data"], {"stove_id": STOVE["id"], "order_id": "C1", "dish_id": dish})
        st = snap_at(rows, 1 + cook)["stoves"][0]
        self.assertEqual((st["state"], st["ready_ticks"]), ("ready", 0))
        self.assertEqual(snap_at(rows, 2 + cook)["stoves"][0]["ready_ticks"], 1)

    def test_items_sorted_by_kind(self):
        dish = "lau_ca_linh_dien_dien"
        block = {"player": {"pos": near(STOVE["pos"])}, "stock": {"ca_linh": 3, "bong_dien_dien": 1},
                 "customers": [waiting(dish=dish)]}
        rows = run_quan(block, [{"tick": 0, "interact": True}], ticks=1)
        self.assertEqual(events(rows, "cook_started")[0]["data"]["items"],
                         ["bong_dien_dien", "ca_linh", "ca_linh", "ca_linh"])

    def test_idle_stove_no_reserved_order_skips(self):
        block = {"player": {"pos": near(STOVE["pos"])}, "stock": {"bong_sung": 2}}
        rows = run_quan(block, [{"tick": 0, "interact": True}], ticks=1)
        self.assertEqual(names(rows), [])

    def test_oldest_reserved_order_by_order_tick_then_table(self):
        tuning = copy.deepcopy(TUNING)
        tuning["quan"]["tables"] = [{"id": "T1", "pos": [9, 2]}, {"id": "T2", "pos": [12, 2]},
                                    {"id": "T3", "pos": [14, 2]}]
        sim = make_sim({"player": {"pos": near(STOVE["pos"])}, "stock": {"bong_sung": 2, "ca_loc": 2},
                        "customers": [
                            dict(waiting("C1", "ca_loc_nuong_trui", order_tick=5), table_id="T1"),
                            dict(waiting("C2", "ca_loc_nuong_trui", order_tick=3), table_id="T3"),
                            dict(waiting("C3", "goi_bong_sung", order_tick=3), table_id="T2"),
                        ]}, tuning)
        evs = sim.step(PRESS)
        self.assertEqual(evs[0][0], "cook_started")
        self.assertEqual(evs[0][1]["order_id"], "C3")  # order_tick 3, bàn T2 < T3

    def test_ready_ticks_only_for_dish_ready_at_step_start(self):
        sim = make_sim({"stock": {}, "customers": [dict(waiting(), order_status="ready", reserved={})],
                        "stoves": [{"id": STOVE["id"], "state": "ready", "ready_ticks": 5,
                                    "dish": {"order_id": "C1", "dish_id": "goi_bong_sung"}}]})
        sim.step(IDLE)
        self.assertEqual(sim.stoves[0]["ready_ticks"], 6)


class TestPickAndServe(unittest.TestCase):
    def ready_block(self, **kw):
        # Scenario ghi món trên bếp dạng dish (chuỗi) + order_id; sim chuẩn hóa về {"order_id","dish_id"}.
        b = {"player": {"pos": near(STOVE["pos"])}, "stock": {},
             "customers": [dict(waiting(), order_status="ready", reserved={}, base_price=40)],
             "stoves": [{"id": STOVE["id"], "state": "ready", "dish": "goi_bong_sung", "order_id": "C1"}]}
        b.update(kw)
        return b

    def test_dish_picked_to_empty_hand(self):
        rows = run_quan(self.ready_block(), [{"tick": 0, "interact": True}], ticks=1)
        ev = events(rows, "dish_picked")
        self.assertEqual(ev[0]["data"], {"stove_id": STOVE["id"], "order_id": "C1", "dish_id": "goi_bong_sung"})
        s = snap_at(rows, 1)
        self.assertEqual(s["hand"], {"order_id": "C1", "dish_id": "goi_bong_sung"})
        self.assertEqual((s["stoves"][0]["state"], s["stoves"][0]["dish"]), ("idle", None))
        self.assertEqual(s["customers"][0]["order_status"], "carried")

    def test_full_hand_cannot_pick(self):
        sim = make_sim(self.ready_block())
        sim.hand = {"order_id": "X9", "dish_id": "goi_bong_sung"}
        self.assertEqual(sim.step(PRESS), [])
        self.assertEqual(sim.stoves[0]["state"], "ready")

    def serve(self, patience):
        block = {"player": {"pos": near(TABLE["pos"])}, "stock": {},
                 "hand": {"order_id": "C1", "dish_id": "goi_bong_sung"},
                 "customers": [carried(patience=patience)]}
        return run_quan(block, [{"tick": 0, "interact": True}], ticks=EAT_TICKS + 2)

    def test_served_with_tip_at_ratio_threshold(self):
        """Kiên nhẫn còn lại sau bước 1 đúng tip_min_patience_ratio -> có boa floor(giá × tip_rate)."""
        threshold = int(math.ceil(PATIENCE_MAX * Q["tip_min_patience_ratio"]))
        rows = self.serve(threshold + 1)
        price = MENU["goi_bong_sung"]["price"]
        tip = math.floor(price * Q["tip_rate"])
        ev = events(rows, "served")[0]
        self.assertEqual(ev["tick"], 1)
        self.assertEqual(ev["data"], {"order_id": "C1", "table_id": TABLE["id"], "dish_id": "goi_bong_sung",
                                      "patience_ticks_left": threshold, "base_price": price, "tip": tip})
        s1 = snap_at(rows, 1)
        self.assertIsNone(s1["hand"])
        self.assertEqual((s1["customers"][0]["state"], s1["customers"][0]["eat_ticks_left"]), ("eating", EAT_TICKS))
        # ăn đủ eat_s × 60 tick -> paid
        paid = events(rows, "paid")
        self.assertEqual(len(paid), 1)
        self.assertEqual(paid[0]["tick"], 1 + EAT_TICKS)
        self.assertEqual(paid[0]["data"], {"order_id": "C1", "table_id": TABLE["id"], "base_price": price,
                                           "tip": tip, "amount": price + tip, "reason": "finished_eating"})
        after = snap_at(rows, 1 + EAT_TICKS)
        self.assertEqual(after["customers"], [])
        self.assertEqual((after["money"], after["earned"]), (price + tip, price + tip))
        rep = Q["reputation_initial"] + Q["tip_reputation"]
        self.assertAlmostEqual(after["reputation"], rep, delta=0.01)
        self.assertEqual(after["score"], price + tip + TUNING["score"]["reputation_multiplier"] * math.floor(rep))

    def test_served_below_ratio_no_tip_no_reputation(self):
        threshold = int(math.ceil(PATIENCE_MAX * Q["tip_min_patience_ratio"]))
        rows = self.serve(threshold)  # sau bước 1 còn threshold - 1 < ngưỡng
        self.assertEqual(events(rows, "served")[0]["data"]["tip"], 0)
        paid = events(rows, "paid")[0]["data"]
        self.assertEqual((paid["tip"], paid["amount"]), (0, MENU["goi_bong_sung"]["price"]))
        self.assertEqual(snapshots(rows)[-1]["reputation"], Q["reputation_initial"])

    def test_serve_on_tick_patience_reaches_zero_is_valid(self):
        rows = self.serve(1)
        self.assertEqual(names(rows)[0], "served")
        self.assertEqual(events(rows, "customer_left"), [])
        self.assertEqual(events(rows, "served")[0]["data"]["patience_ticks_left"], 0)

    def test_wrong_order_on_table_skips(self):
        block = {"player": {"pos": near(TABLE["pos"])}, "stock": {},
                 "customers": [carried()]}
        sim = make_sim(block)
        sim.hand = {"order_id": "C7", "dish_id": "goi_bong_sung"}
        self.assertEqual(sim.step(PRESS), [])
        self.assertEqual(sim.hand["order_id"], "C7")

    def test_tip_reputation_clamped_to_max(self):
        block = {"reputation": Q["reputation_max"] - 0.1, "stock": {},
                 "customers": [eating(eat=1, tip=8)]}
        rows = run_quan(block, ticks=1)
        self.assertEqual(events(rows, "paid")[0]["data"]["amount"], MENU["goi_bong_sung"]["price"] + 8)
        self.assertEqual(snap_at(rows, 1)["reputation"], Q["reputation_max"])


class TestLeavingDropsDish(unittest.TestCase):
    def test_patience_leave_drops_cooking_dish_no_refund(self):
        block = {"stock": {"bong_sung": 1}, "customers": [dict(waiting(), patience_ticks_left=1,
                                                                order_status="cooking", reserved={},
                                                                base_price=40)],
                 "stoves": [{"id": STOVE["id"], "state": "cooking", "cook_ticks_left": 100,
                             "dish": "goi_bong_sung", "order_id": "C1"}]}
        rows = run_quan(block, ticks=1)
        left = events(rows, "customer_left")[0]["data"]
        self.assertEqual((left["order_id"], left["table_id"], left["reason"]), ("C1", TABLE["id"], "patience"))
        self.assertAlmostEqual(left["reputation"], Q["reputation_initial"] + Q["left_reputation_delta"], delta=0.01)
        s = snap_at(rows, 1)
        self.assertEqual((s["stoves"][0]["state"], s["stoves"][0]["dish"]), ("idle", None))
        self.assertEqual(s["stock"], {"bong_sung": 1})

    def test_leave_drops_dish_in_hand(self):
        sim = make_sim({"stock": {}, "customers": [carried(patience=1)]})
        sim.hand = {"order_id": "C1", "dish_id": "goi_bong_sung"}
        evs = sim.step(IDLE)
        self.assertEqual([e[0] for e in evs], ["customer_left"])
        self.assertIsNone(sim.hand)


class TestClosing(unittest.TestCase):
    """AC-P1-10: hết ca — khách đang ăn trả closing, khách chờ rời closing không trừ uy tín, rồi quan_end."""

    def test_eating_customer_pays_closing_then_quan_end(self):
        price = MENU["goi_bong_sung"]["price"]
        rows = run_quan({"time_left_ticks": 3, "stock": {}, "customers": [eating(tip=8)]}, ticks=10)
        evs = events(rows)
        self.assertEqual([e["name"] for e in evs], ["paid", "quan_end"])
        self.assertTrue(all(e["tick"] == 3 for e in evs))
        self.assertEqual(evs[0]["data"]["reason"], "closing")
        self.assertEqual(evs[0]["data"]["amount"], price + 8)
        rep = Q["reputation_initial"] + Q["tip_reputation"]
        q = evs[1]["data"]
        self.assertEqual((q["reason"], q["money"], q["earned"], q["shift_earned"]), ("time", price + 8, price + 8, price + 8))
        self.assertAlmostEqual(q["reputation"], rep, delta=0.01)
        end = rows[-1]
        self.assertEqual((end["type"], end["reason"], end["state"], end["ticks"]), ("end", "time", "finished", 3))
        self.assertEqual(end["score"], price + 8 + TUNING["score"]["reputation_multiplier"] * math.floor(rep))
        self.assertEqual(snap_at(rows, 3)["customers"], [])

    def test_waiting_customer_leaves_closing_without_penalty(self):
        rows = run_quan({"time_left_ticks": 2, "stock": {"bong_sung": 2}, "customers": [waiting()]}, ticks=5)
        self.assertEqual(names(rows), ["customer_left", "quan_end"])
        left = events(rows, "customer_left")[0]["data"]
        self.assertEqual((left["reason"], left["reputation"]), ("closing", Q["reputation_initial"]))
        self.assertEqual(events(rows, "quan_end")[0]["data"]["reputation"], Q["reputation_initial"])

    def test_patience_zero_on_closing_tick_is_closing(self):
        """PRD-0 F4: chỉ 'nếu ca còn giờ' mới rời patience; đúng tick hết ca -> closing, không trừ uy tín."""
        rows = run_quan({"time_left_ticks": 1, "stock": {"bong_sung": 2},
                         "customers": [waiting(patience_ticks_left=1)]}, ticks=2)
        left = events(rows, "customer_left")[0]["data"]
        self.assertEqual(left["reason"], "closing")
        self.assertEqual(snapshots(rows)[-1]["reputation"], Q["reputation_initial"])

    def test_served_on_last_tick_pays_closing(self):
        """Phục vụ đúng tick hết ca vẫn hợp lệ, rồi khách trả ngay với closing."""
        rows = run_quan({"time_left_ticks": 1, "player": {"pos": near(TABLE["pos"])}, "stock": {},
                         "hand": {"order_id": "C1", "dish_id": "goi_bong_sung"}, "customers": [carried()]},
                        [{"tick": 0, "interact": True}], ticks=3)
        self.assertEqual(names(rows), ["served", "paid", "quan_end"])
        self.assertEqual(events(rows, "paid")[0]["data"]["reason"], "closing")

    def test_no_new_customer_after_closing(self):
        """Hết ca thì không xét lượt khách (bước 5 chỉ khi còn giờ)."""
        first = Q["first_customer_tick"]
        sim = QuanSim(TUNING, {"time_left_ticks": first, "stock": {"bong_sung": 2}}, Streams(1), IdAllocator())
        evs = []
        while not sim.done:
            evs += sim.step(IDLE)
        self.assertEqual([e[0] for e in evs], ["quan_end"])


class TestFullLoopFixture(unittest.TestCase):
    """AC-P1-09: fixture quan_one_customer — nấu → bưng → đi tới bàn → phục vụ → ăn → paid."""

    def test_cook_carry_serve_pay(self):
        dish = "goi_bong_sung"
        cook = int(round(MENU[dish]["cook_s"] * HZ))
        price = MENU[dish]["price"]
        pick = cook + 1
        fr = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False},
              {"tick": pick, "interact": True}, {"tick": pick + 1, "interact": False},
              {"tick": 250, "move": [1, 0]}, {"tick": 355, "move": [0, 0]},
              {"tick": 365, "move": [0, -1]}, {"tick": 430, "move": [0, 0]},
              {"tick": 440, "interact": True}, {"tick": 441, "interact": False}]
        with Workdir() as w:
            inp = write_json(w.path("in.json"), frames(*fr))
            out = w.path("o.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", str(441 + EAT_TICKS + 5),
                                     "--scenario", FIXTURE, "--inputs", inp, "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
        seq = [(e["tick"], e["name"]) for e in events(rows)]
        self.assertEqual(seq, [(1, "cook_started"), (1 + cook, "dish_ready"), (pick + 1, "dish_picked"),
                               (441, "served"), (441 + EAT_TICKS, "paid")])
        served = events(rows, "served")[0]["data"]
        self.assertEqual(served["patience_ticks_left"], PATIENCE_MAX - 441)
        tip = math.floor(price * Q["tip_rate"])
        self.assertEqual(served["tip"], tip)
        end = rows[-1]
        rep = Q["reputation_initial"] + Q["tip_reputation"]
        self.assertEqual((end["money"], end["earned"]), (price + tip, price + tip))
        self.assertAlmostEqual(end["reputation"], rep, delta=0.01)
        self.assertEqual(end["score"], price + tip + TUNING["score"]["reputation_multiplier"] * math.floor(rep))

    def test_same_seed_byte_identical(self):
        outs = []
        with Workdir() as w:
            for i in range(2):
                out = w.path(f"o{i}.jsonl")
                code, err = run_headless("--mode", "quan", "--seed", "7", "--ticks", "2000",
                                         "--scenario", FIXTURE, "--out", out)
                self.assertEqual(code, 0, err)
                with open(out, "rb") as f:
                    outs.append(f.read())
        self.assertEqual(outs[0], outs[1])


if __name__ == "__main__":
    unittest.main()
