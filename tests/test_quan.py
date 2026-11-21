"""Test hộp đen quan: chỉ run_headless, đọc JSONL; số liệu từ game.contract.json.

@lat3: khách/giữ chỗ/kiên nhẫn; @lat4: bếp/bưng/phục vụ/thu tiền/hết ca.
Lát 3 & 4 đã xong (PR #3) nên hai decorator không còn bỏ qua test. Nguồn: contracts mục 1, 2.2, 3.2.
"""

import json
import math
import os
import unittest

from helpers import ROOT, Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

# Lát 3 & 4 đã hoàn thành (PR #3): không bỏ qua test
lat3 = lat4 = lambda f: f
with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
    TUNING = json.load(f)["tuning"]
Q, MENU, HZ = TUNING["quan"], TUNING["menu"], TUNING["tick_hz"]
DISH = sorted(MENU)[0]
RECIPE = MENU[DISH]["recipe"]
PRICE = MENU[DISH]["price"]
PATIENCE = int(round(Q["patience_s"] * HZ))
COOK = int(round(MENU[DISH]["cook_s"] * HZ))
EAT = int(round(Q["eat_s"] * HZ))
STOVE, TABLE = Q["stoves"][0], Q["tables"][0]
PRESS = [{"tick": 0, "interact": True}]


def run_quan(scenario=None, inputs=None, ticks=1, seed=1, inventory=None):
    """Scenario là khối quan; inventory là object file kho {items: ...}; trả rows."""
    with Workdir() as w:
        args = ["--mode", "quan", "--seed", str(seed), "--ticks", str(ticks),
                "--snapshot-every", "1", "--out", w.path("o.jsonl")]
        if scenario is not None:
            args += ["--scenario", write_json(w.path("sc.json"), {"quan": scenario})]
        if inputs is not None:
            args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
        if inventory is not None:
            args += ["--inventory", write_json(w.path("inv.json"), inventory)]
        code, err = run_headless(*args)
        assert code == 0, err
        return read_jsonl(w.path("o.jsonl"))


def near(entity, offset=0):
    return [entity["pos"][0] + offset, entity["pos"][1]]


def customer(**updates):
    c = {"id": "C1", "table_id": TABLE["id"], "dish_id": DISH, "order_tick": 0,
         "state": "waiting", "patience_ticks_left": PATIENCE, "eat_ticks_left": 0,
         "order_status": "reserved", "reserved": dict(RECIPE), "base_price": 0, "tip": 0}
    c.update(updates)
    return c


def scenario(**updates):
    s = {"random_customers": False, "customers": [], "stock": dict(RECIPE)}
    s.update(updates)
    return s


def payload():
    return {"order_id": "C1", "dish_id": DISH, "base_price": PRICE}


def ready_scene(**updates):
    return scenario(customers=[customer(order_status="assigned", reserved={}, base_price=PRICE)],
                    stock={}, stoves=[{"id": STOVE["id"], "state": "ready", "dish": payload(),
                                      "cook_ticks_left": 0, "ready_ticks": 0}], **updates)


def serving_scene(patience=PATIENCE, **updates):
    return scenario(customers=[customer(order_status="assigned", reserved={}, base_price=PRICE,
                                        patience_ticks_left=patience)], stock={}, hand=payload(),
                    player={"pos": near(TABLE)}, **updates)


class QuanCase(unittest.TestCase):
    """Đọc dữ liệu thiếu đều trở thành assertion failure, không IndexError/KeyError."""

    def fields(self, obj, keys):
        self.assertIsInstance(obj, dict)
        self.assertTrue(set(keys) <= set(obj), f"Thiếu {set(keys) - set(obj)}: {obj}")
        return obj

    def snap(self, rows, tick=None):
        ss = snapshots(rows)
        if tick is not None:
            ss = [s for s in ss if s.get("tick") == tick]
        self.assertTrue(ss, f"Thiếu snapshot tick {tick}")
        return ss[-1]

    def one(self, rows, name, tick=None):
        es = events(rows, name)
        self.assertEqual(len(es), 1, (name, es))
        self.fields(es[0], ("tick", "phase", "data"))
        self.assertEqual(es[0]["phase"], "quan")
        if tick is not None:
            self.assertEqual(es[0]["tick"], tick)
        return es[0]["data"]

    def entity(self, snap, collection, entity_id):
        self.fields(snap, (collection,))
        found = [e for e in snap[collection] if e.get("id") == entity_id]
        self.assertEqual(len(found), 1, (collection, entity_id, found))
        return found[0]

    def rep(self, value, expected):
        self.assertAlmostEqual(value, expected, delta=0.01)


class Framework(QuanCase):
    def test_common_snapshot_and_end(self):
        rows = run_quan(ticks=0)
        s = self.snap(rows, 0)
        self.fields(s, ("type", "tick", "sim_tick", "mode", "phase", "phase_tick", "state",
                        "time_left_ticks", "money", "earned", "reputation", "score",
                        "player", "stock", "hand", "stoves", "tables", "customers"))
        self.assertEqual((s["mode"], s["phase"], s["state"]), ("quan", "quan", "playing"))
        self.assertEqual((s["tick"], s["sim_tick"], s["phase_tick"]), (0, 0, 0))
        self.assertEqual(s["time_left_ticks"], int(round(Q["duration_s"] * HZ)))
        self.assertEqual((s["money"], s["earned"], s["stock"], s["hand"]), (0, 0, {}, None))
        self.rep(s["reputation"], Q["reputation_initial"])
        self.assertEqual(s["score"], TUNING["score"]["reputation_multiplier"] * math.floor(s["reputation"]))
        self.assertEqual(sum(r["type"] == "end" for r in rows), 1)
        self.fields(rows[-1], ("type", "ticks", "sim_tick", "mode", "state", "reason", "money", "earned", "reputation", "score"))
        self.assertEqual((rows[-1]["type"], rows[-1]["reason"], rows[-1]["ticks"]), ("end", "tick_limit", 0))

    def test_empty_tables_customer_id_null(self):
        s = self.snap(run_quan(scenario(), ticks=0))
        self.assertEqual(len(s["tables"]), len(Q["tables"]))
        for t in s["tables"]:
            self.fields(t, ("id", "pos", "customer_id"))
            self.assertIsNone(t["customer_id"])

    def test_inventory_file_and_scenario_stock(self):
        stock = {k: n * (TUNING["gather"]["hold_capacity"] + 1) for k, n in RECIPE.items()}
        for rows in (run_quan(inventory={"items": stock}, ticks=0),
                     run_quan(scenario(stock=stock), ticks=0)):
            s = self.snap(rows, 0)
            self.assertEqual(s["stock"], stock)  # trần giỏ không áp lên kho
            self.assertEqual((s["money"], s["earned"]), (0, 0))

    def test_walk_speed_and_diagonal_normalization(self):
        ramp = Q["ramp_max_ticks"]
        for move in ([1, 0], [0, -1], [-1, -1]):
            with self.subTest(move=move):
                rows = run_quan(scenario(), [{"tick": 0, "move": move}], ticks=ramp + HZ)
                a, b = self.snap(rows, ramp)["player"]["pos"], self.snap(rows)["player"]["pos"]
                self.assertAlmostEqual(math.dist(a, b), Q["walk_speed"], delta=0.1)
                for axis in range(2):
                    self.assertAlmostEqual(b[axis] - a[axis], Q["walk_speed"] * move[axis] / math.hypot(*move), delta=0.1)

    def test_all_bounds_clamp(self):
        for axis, name in enumerate(("x", "z")):
            for edge, sign in zip(Q["bounds"][name], (-1, 1)):
                pos = list(Q["start_pos"])
                pos[axis] = edge
                move = [0, 0]
                move[axis] = sign
                s = self.snap(run_quan(scenario(player={"pos": pos}), [{"tick": 0, "move": move}], ticks=Q["ramp_max_ticks"] + 1))
                self.assertAlmostEqual(s["player"]["pos"][axis], edge, delta=0.1)

    def test_timeout_quan_end_and_event_order(self):
        rows = run_quan(scenario(time_left_ticks=1), ticks=Q["ramp_max_ticks"])
        data = self.one(rows, "quan_end", 1)
        self.assertEqual(data, {"reason": "time", "money": 0, "earned": 0, "shift_earned": 0,
                                "reputation": Q["reputation_initial"]})
        ev = events(rows, "quan_end")[0]
        self.assertEqual(set(ev), {"type", "tick", "phase", "name", "data"})
        i = rows.index(ev)
        self.assertGreater(len(rows), i + 1)
        self.assertEqual((rows[i + 1]["type"], rows[i + 1]["tick"], rows[i + 1]["state"]), ("snapshot", 1, "finished"))
        self.assertEqual([s["tick"] for s in snapshots(rows)], [0, 1])
        self.assertEqual((rows[-1]["reason"], rows[-1]["ticks"]), ("time", 1))


class Customers(QuanCase):
    @lat3
    def test_arrival_schedule_lowest_table_and_reserved_recipe(self):
        first = Q["first_customer_tick"]
        interval = int(round(Q["customer_interval_s"] * HZ))
        # Chưa hết kiên nhẫn tại lượt thứ hai; bàn vẫn kín.
        # v1.1 có nhiều bàn: lấp mọi bàn trừ bàn id nhỏ nhất bằng khách chờ (unfulfillable, không giữ hàng)
        # để lượt thứ hai vẫn không có bàn trống, giữ nguyên ý định của test.
        def id_key(e):
            import re
            m = re.fullmatch(r"(.*?)(\d+)", e["id"])
            return (m[1], int(m[2]), e["id"]) if m else (e["id"], -1, e["id"])
        others = sorted(Q["tables"], key=id_key)[1:]
        fillers = [customer(id=f"C{i + 2}", table_id=t["id"], order_status="unfulfillable", reserved={})
                   for i, t in enumerate(others)]
        rows = run_quan(scenario(random_customers=True, customers=fillers), ticks=first + interval)
        arrived = events(rows, "customer_arrived")
        self.assertGreaterEqual(len(arrived), 1)
        self.assertEqual(arrived[0]["tick"], first)
        data = arrived[0]["data"]
        self.fields(data, ("order_id", "table_id", "dish_id"))
        self.assertEqual(set(data), {"order_id", "table_id", "dish_id"})
        # Natural id ordering, không so chuỗi T10 trước T2.
        self.assertEqual(data["table_id"], min(Q["tables"], key=id_key)["id"])
        self.assertEqual(data["dish_id"], DISH)  # chỉ công thức này đủ
        c = self.entity(self.snap(rows, first), "customers", data["order_id"])
        self.fields(c, ("reserved", "order_status", "order_tick", "patience_ticks_left"))
        self.assertEqual((c["reserved"], c["order_status"], c["order_tick"], c["patience_ticks_left"]),
                         (RECIPE, "reserved", first, PATIENCE))
        self.assertEqual(self.snap(rows, first)["stock"], RECIPE)  # tồn gồm phần giữ
        # Bàn vẫn kín ở lượt thứ hai: không customer_arrived/no_dish.
        self.assertEqual([e["tick"] for e in arrived], [first])
        self.assertEqual(events(rows, "no_dish"), [])

    @lat3
    def test_no_dish_empty_payload_at_each_scheduled_tick(self):
        first, interval = Q["first_customer_tick"], int(round(Q["customer_interval_s"] * HZ))
        rows = run_quan(scenario(stock={}, random_customers=True), ticks=first + interval)
        self.assertEqual([(e["tick"], e["data"]) for e in events(rows, "no_dish")], [(first, {}), (first + interval, {})])
        self.assertEqual(events(rows, "customer_arrived"), [])

    @lat3
    def test_no_table_skips_slot_without_event(self):
        cs = [customer(id=f"C{i + 1}", table_id=t["id"]) for i, t in enumerate(Q["tables"])]
        stock = {k: v * len(cs) for k, v in RECIPE.items()}
        rows = run_quan(scenario(customers=cs, stock=stock, random_customers=True), ticks=Q["first_customer_tick"])
        self.assertEqual(events(rows), [])
        self.assertEqual(len(self.snap(rows)["customers"]), len(cs))

    @lat3
    def test_scenario_reserved_inferred_and_patience_starts_next_step(self):
        c = customer()
        del c["reserved"]
        rows = run_quan(scenario(customers=[c]), ticks=1)
        for tick in (0, 1):
            got = self.entity(self.snap(rows, tick), "customers", "C1")
            self.fields(got, ("reserved", "patience_ticks_left", "order_status"))
            self.assertEqual(got["reserved"], RECIPE)
            self.assertEqual(got["order_status"], "reserved")
            self.assertEqual(got["patience_ticks_left"], PATIENCE - tick)

    @lat3
    def test_patience_left_releases_reservation_and_clamps_reputation(self):
        for rep in (Q["reputation_initial"], Q["reputation_min"]):
            rows = run_quan(scenario(customers=[customer(patience_ticks_left=1)], reputation=rep), ticks=1)
            data = self.one(rows, "customer_left", 1)
            expected = max(Q["reputation_min"], min(Q["reputation_max"], rep + Q["left_reputation_delta"]))
            self.fields(data, ("reputation",))
            self.rep(data["reputation"], expected)
            self.assertEqual({k: v for k, v in data.items() if k != "reputation"},
                             {"order_id": "C1", "table_id": TABLE["id"], "reason": "patience"})
            s = self.snap(rows)
            self.assertEqual(s["customers"], [])
            self.assertEqual(s["stock"], RECIPE)
            self.assertIsNone(self.entity(s, "tables", TABLE["id"])["customer_id"])
            self.rep(s["reputation"], expected)

    @lat3
    def test_released_stock_available_to_next_arrival(self):
        first = Q["first_customer_tick"]
        rows = run_quan(scenario(customers=[customer(patience_ticks_left=first)], random_customers=True), ticks=first)
        self.one(rows, "customer_left", first)
        data = self.one(rows, "customer_arrived", first)
        self.fields(data, ("order_id", "table_id", "dish_id"))
        self.assertNotEqual(data["order_id"], "C1")
        self.assertEqual((data["table_id"], data["dish_id"]), (TABLE["id"], DISH))
        c = self.entity(self.snap(rows), "customers", data["order_id"])
        self.fields(c, ("reserved",))
        self.assertEqual(c["reserved"], RECIPE)
        self.assertEqual([e["name"] for e in events(rows)], ["customer_left", "customer_arrived"])

    @lat3
    def test_reserved_stock_cannot_be_used_by_another_customer(self):
        if len(Q["tables"]) < 2:
            self.skipTest("Cần hai bàn: một giữ hết nguyên liệu, một còn trống")
        rows = run_quan(scenario(customers=[customer()], random_customers=True), ticks=Q["first_customer_tick"])
        self.assertEqual(self.one(rows, "no_dish", Q["first_customer_tick"]), {})
        self.assertEqual(events(rows, "customer_arrived"), [])
        self.assertEqual(self.snap(rows)["stock"], RECIPE)

    @lat3
    def test_arrived_patience_decreases_only_on_following_step(self):
        first = Q["first_customer_tick"]
        rows = run_quan(scenario(random_customers=True), ticks=first + 1)
        data = self.one(rows, "customer_arrived", first)
        self.fields(data, ("order_id",))
        for tick in (first, first + 1):
            c = self.entity(self.snap(rows, tick), "customers", data["order_id"])
            self.fields(c, ("patience_ticks_left",))
            self.assertEqual(c["patience_ticks_left"], PATIENCE - (tick - first))


class Kitchen(QuanCase):
    @lat4
    def test_cook_started_consumes_reserved_items_and_locks_price(self):
        rows = run_quan(scenario(customers=[customer()], player={"pos": near(STOVE, Q["interact_radius"])}), PRESS)
        items = [k for k in sorted(RECIPE) for _ in range(RECIPE[k])]
        self.assertEqual(self.one(rows, "cook_started", 1),
                         {"stove_id": STOVE["id"], "order_id": "C1", "dish_id": DISH, "items": items, "base_price": PRICE})
        s = self.snap(rows)
        self.assertEqual(s["stock"], {})
        c = self.entity(s, "customers", "C1")
        self.fields(c, ("reserved", "order_status", "base_price"))
        self.assertEqual((c["reserved"], c["order_status"], c["base_price"]), ({}, "assigned", PRICE))
        b = self.entity(s, "stoves", STOVE["id"])
        self.fields(b, ("state", "cook_ticks_left"))
        self.assertEqual((b["state"], b["cook_ticks_left"]), ("cooking", COOK))

    @lat4
    def test_oldest_reserved_order_then_table_id(self):
        if len(Q["tables"]) < 2:
            self.skipTest("Cần hai bàn để kiểm chọn đơn theo order_tick rồi id bàn")
        def key(t):
            import re
            m = re.fullmatch(r"(.*?)(\d+)", t["id"])
            return (m[1], int(m[2]), t["id"]) if m else (t["id"], -1, t["id"])
        tables = sorted(Q["tables"], key=key)[:2]
        cs = [customer(table_id=tables[0]["id"]), customer(id="C2", table_id=tables[1]["id"])]
        stock = {k: v * len(cs) for k, v in RECIPE.items()}
        rows = run_quan(scenario(customers=list(reversed(cs)), stock=stock, player={"pos": near(STOVE)}), PRESS)
        data = self.one(rows, "cook_started", 1)
        self.fields(data, ("order_id",))
        self.assertEqual(data["order_id"], "C1")
        # Tạo hai đơn ở hai lượt thật để order_tick khác nhau và không ở tương lai.
        second = Q["first_customer_tick"] + int(round(Q["customer_interval_s"] * HZ))
        rows = run_quan(scenario(stock=stock, random_customers=True, player={"pos": near(STOVE)}),
                        [{"tick": second, "interact": True}], ticks=second + 1)
        arrived = events(rows, "customer_arrived")
        self.assertEqual(len(arrived), len(cs))
        self.fields(arrived[0]["data"], ("order_id",))
        data = self.one(rows, "cook_started", second + 1)
        self.fields(data, ("order_id",))
        self.assertEqual(data["order_id"], arrived[0]["data"]["order_id"])

    @lat4
    def test_cook_started_items_sorted_for_every_menu_recipe(self):
        for dish_id, dish in sorted(MENU.items()):
            recipe = dish["recipe"]
            rows = run_quan(scenario(customers=[customer(dish_id=dish_id, reserved=dict(recipe))],
                                     stock=dict(recipe), player={"pos": near(STOVE)}), PRESS)
            self.assertEqual(self.one(rows, "cook_started", 1),
                             {"stove_id": STOVE["id"], "order_id": "C1", "dish_id": dish_id,
                              "items": [k for k in sorted(recipe) for _ in range(recipe[k])], "base_price": dish["price"]})

    @lat4
    def test_cooking_finishes_before_interact_can_pick_same_step(self):
        sc = ready_scene(player={"pos": near(STOVE)})
        sc["stoves"][0].update(state="cooking", cook_ticks_left=1)
        rows = run_quan(sc, PRESS)
        self.assertEqual([e["name"] for e in events(rows)], ["dish_ready", "dish_picked"])
        for name in ("dish_ready", "dish_picked"):
            self.assertEqual(self.one(rows, name, 1), {"stove_id": STOVE["id"], "order_id": "C1", "dish_id": DISH})
        self.assertEqual(self.snap(rows)["hand"], payload())

    @lat4
    def test_cook_duration_ready_ticks_and_no_burn(self):
        rows = run_quan(scenario(customers=[customer()], player={"pos": near(STOVE)}), PRESS, ticks=COOK + Q["ramp_max_ticks"])
        self.assertEqual(self.one(rows, "dish_ready", COOK + 1), {"stove_id": STOVE["id"], "order_id": "C1", "dish_id": DISH})
        for tick in (COOK, COOK + 1, COOK + Q["ramp_max_ticks"]):
            b = self.entity(self.snap(rows, tick), "stoves", STOVE["id"])
            self.fields(b, ("state", "cook_ticks_left", "ready_ticks"))
            self.assertEqual(b["state"], "cooking" if tick == COOK else "ready")
            self.assertEqual(b["cook_ticks_left"], 1 if tick == COOK else 0)
            if tick > COOK:
                self.assertEqual(b["ready_ticks"], tick - COOK - 1)
        self.assertIsNone(Q["burn_s"])
        self.assertEqual(events(rows, "dish_picked"), [])  # giữ nút không lặp interact

    @lat4
    def test_pick_ready_hand_payload_and_stove_idle(self):
        rows = run_quan(ready_scene(player={"pos": near(STOVE)}), PRESS)
        self.assertEqual(self.one(rows, "dish_picked", 1), {"stove_id": STOVE["id"], "order_id": "C1", "dish_id": DISH})
        s = self.snap(rows)
        self.assertEqual(s["hand"], payload())
        b = self.entity(s, "stoves", STOVE["id"])
        self.fields(b, ("state", "dish"))
        self.assertEqual((b["state"], b["dish"]), ("idle", None))

    @lat4
    def test_carry_limit_blocks_pick_when_hand_full(self):
        if len(Q["tables"]) < 2:
            self.skipTest("Cần hai bàn để dựng hai đơn hợp lệ, một món tay và một món bếp")
        other = Q["tables"][1]
        sc = ready_scene(player={"pos": near(STOVE)}, hand=payload())
        sc["customers"].append(customer(id="C2", table_id=other["id"], order_status="assigned",
                                         reserved={}, base_price=PRICE))
        sc["stoves"][0]["dish"] = dict(payload(), order_id="C2")
        rows = run_quan(sc, PRESS)
        self.assertEqual(Q["carry_limit"], 1)
        self.assertEqual(events(rows, "dish_picked"), [])
        self.assertEqual(self.snap(rows)["hand"], payload())
        b = self.entity(self.snap(rows), "stoves", STOVE["id"])
        self.fields(b, ("state", "dish"))
        self.assertEqual((b["state"], b["dish"]), ("ready", dict(payload(), order_id="C2")))

    @lat4
    def test_interact_distance_then_stove_priority_one_action(self):
        for should_serve in (False, True):
            pos = near(STOVE, Q["interact_radius"])
            # Hòa khoảng cách: bếp idle (không có đơn reserved) được chọn rồi bỏ
            # lượt. Bàn gần hơn: phục vụ dù vẫn có bếp trong bán kính.
            table_pos = pos if should_serve else near(STOVE)
            sc = serving_scene(stoves=[{"id": STOVE["id"]}],
                               tables=[{"id": TABLE["id"], "pos": table_pos}])
            sc["player"] = {"pos": pos}
            rows = run_quan(sc, PRESS)
            self.assertEqual(len(events(rows, "served")), int(should_serve))
            self.assertEqual(events(rows, "cook_started") + events(rows, "dish_picked"), [])

    @lat4
    def test_move_into_radius_before_interact(self):
        pos = near(STOVE, Q["interact_radius"] + Q["walk_speed"] / HZ)
        sc = scenario(customers=[customer()], player={"pos": pos, "vel": [-Q["walk_speed"], 0]})
        rows = run_quan(sc, [{"tick": 0, "move": [-1, 0], "interact": True}])
        self.one(rows, "cook_started", 1)

    @lat4
    def test_interact_same_type_tie_by_id(self):
        # Fixture chỉ cập nhật id tuning đã có, không tự thêm bếp trái hợp đồng.
        if len(Q["stoves"]) < 2:
            self.skipTest("Tuning có một bếp: chưa dựng được hòa khoảng cách cùng loại")
        bs = sorted(Q["stoves"], key=lambda b: (b["id"].rstrip("0123456789"), int(b["id"][len(b["id"].rstrip("0123456789")):] or -1)))
        rows = run_quan(scenario(customers=[customer()], player={"pos": near(STOVE)},
                                stoves=[{"id": b["id"], "pos": near(STOVE)} for b in bs]), PRESS)
        data = self.one(rows, "cook_started", 1)
        self.fields(data, ("stove_id",))
        self.assertEqual(data["stove_id"], bs[0]["id"])

    @lat4
    def test_outside_radius_no_action(self):
        # v1.1: B2 nằm cách B1 3 m theo x, nên lùi theo z (về phía giữa quán) để không trúng bếp/bàn khác.
        pos = [STOVE["pos"][0], STOVE["pos"][1] - Q["interact_radius"] * 2]
        rows = run_quan(scenario(customers=[customer()], player={"pos": pos}), PRESS)
        self.assertEqual(events(rows), [])
        self.assertEqual(self.snap(rows)["stock"], RECIPE)

    @lat4
    def test_patience_expiry_discards_stove_or_hand_without_refund(self):
        for carrying in (False, True):
            if carrying:
                sc = serving_scene(patience=1)
            else:
                sc = ready_scene()
                sc["customers"][0]["patience_ticks_left"] = 1
            rows = run_quan(sc)
            self.one(rows, "customer_left", 1)
            s = self.snap(rows)
            self.assertEqual(s["stock"], {})
            self.assertIsNone(s["hand"])
            b = self.entity(s, "stoves", STOVE["id"])
            self.fields(b, ("state", "dish"))
            self.assertEqual((b["state"], b["dish"]), ("idle", None))


class Service(QuanCase):
    @lat4
    def test_served_tip_boundary_after_patience_decrement(self):
        boundary = math.ceil(PATIENCE * Q["tip_min_patience_ratio"])
        for left in (boundary, boundary - 1):
            rows = run_quan(serving_scene(patience=left + 1), PRESS)
            tip = math.floor(PRICE * Q["tip_rate"]) if left / PATIENCE >= Q["tip_min_patience_ratio"] else 0
            self.assertEqual(self.one(rows, "served", 1), {"order_id": "C1", "table_id": TABLE["id"],
                             "dish_id": DISH, "patience_ticks_left": left, "base_price": PRICE, "tip": tip})
            s = self.snap(rows)
            self.assertIsNone(s["hand"])
            c = self.entity(s, "customers", "C1")
            self.fields(c, ("state", "order_status", "eat_ticks_left", "tip"))
            self.assertEqual((c["state"], c["order_status"], c["eat_ticks_left"], c["tip"]), ("eating", "served", EAT, tip))

    @lat4
    def test_wrong_order_not_served(self):
        if len(Q["tables"]) < 2:
            self.skipTest("Cần hai bàn để bưng đơn C1 tới khách C2 mà fixture vẫn hợp lệ")
        other = Q["tables"][1]
        sc = serving_scene()
        sc["customers"].append(customer(id="C2", table_id=other["id"]))
        sc["stock"] = dict(RECIPE)
        sc["player"] = {"pos": near(other)}
        rows = run_quan(sc, PRESS)
        self.assertEqual(events(rows, "served"), [])
        self.assertEqual(self.snap(rows)["hand"], payload())
        c = self.entity(self.snap(rows), "customers", "C2")
        self.fields(c, ("state",))
        self.assertEqual(c["state"], "waiting")

    @lat4
    def test_finished_eating_paid_money_earned_and_tip_reputation(self):
        for patience in (PATIENCE, math.ceil(PATIENCE * Q["tip_min_patience_ratio"])):
            tip = math.floor(PRICE * Q["tip_rate"]) if (patience - 1) / PATIENCE >= Q["tip_min_patience_ratio"] else 0
            for rep in (Q["reputation_initial"], Q["reputation_max"]):
                rows = run_quan(serving_scene(patience=patience, reputation=rep), PRESS, ticks=1 + EAT)
                self.assertEqual(events([r for r in rows if r.get("tick", 0) <= EAT], "paid"), [])
                self.assertEqual(self.one(rows, "paid", EAT + 1), {"order_id": "C1", "table_id": TABLE["id"],
                                 "base_price": PRICE, "tip": tip, "amount": PRICE + tip, "reason": "finished_eating"})
                s = self.snap(rows)
                self.assertEqual((s["money"], s["earned"], s["customers"]), (PRICE + tip, PRICE + tip, []))
                self.rep(s["reputation"], min(Q["reputation_max"], rep + (Q["tip_reputation"] if tip > 0 else 0)))
                self.assertIsNone(self.entity(s, "tables", TABLE["id"])["customer_id"])
                self.assertEqual(s["score"], s["earned"] + TUNING["score"]["reputation_multiplier"] * math.floor(s["reputation"]))

    @lat4
    def test_closing_pays_eating_then_quan_end_full_payload(self):
        tip = math.floor(PRICE * Q["tip_rate"])
        c = customer(state="eating", order_status="served", reserved={}, base_price=PRICE, tip=tip, eat_ticks_left=EAT)
        rows = run_quan(scenario(customers=[c], stock={}, time_left_ticks=1), ticks=EAT)
        self.assertEqual(self.one(rows, "paid", 1), {"order_id": "C1", "table_id": TABLE["id"], "base_price": PRICE,
                         "tip": tip, "amount": PRICE + tip, "reason": "closing"})
        rep = min(Q["reputation_max"], Q["reputation_initial"] + (Q["tip_reputation"] if tip else 0))
        end = self.one(rows, "quan_end", 1)
        self.fields(end, ("reputation",))
        self.rep(end["reputation"], rep)
        self.assertEqual({k: v for k, v in end.items() if k != "reputation"},
                         {"reason": "time", "money": PRICE + tip, "earned": PRICE + tip, "shift_earned": PRICE + tip})
        self.assertEqual([e["name"] for e in events(rows)], ["paid", "quan_end"])
        s = self.snap(rows)
        self.assertEqual(s["customers"], [])
        for row in (s, rows[-1]):
            self.assertEqual((row["money"], row["earned"], row["score"]),
                             (PRICE + tip, PRICE + tip, PRICE + tip + TUNING["score"]["reputation_multiplier"] * math.floor(rep)))
            self.rep(row["reputation"], rep)

    @lat4
    def test_closing_waiting_no_penalty_and_no_new_arrival(self):
        closing = Q["first_customer_tick"]
        rows = run_quan(scenario(customers=[customer(patience_ticks_left=closing)],
                                 time_left_ticks=closing, random_customers=True), ticks=closing)
        data = self.one(rows, "customer_left", closing)
        self.assertEqual(data, {"order_id": "C1", "table_id": TABLE["id"], "reason": "closing", "reputation": Q["reputation_initial"]})
        self.one(rows, "quan_end", closing)
        self.assertEqual([e["name"] for e in events(rows)], ["customer_left", "quan_end"])
        s = self.snap(rows)
        self.assertEqual((s["customers"], s["stock"], s["hand"]), ([], RECIPE, None))
        self.assertIsNone(self.entity(s, "tables", TABLE["id"])["customer_id"])


if __name__ == "__main__":
    unittest.main()
