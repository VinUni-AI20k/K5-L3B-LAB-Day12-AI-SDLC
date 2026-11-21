import json
import subprocess
import sys
import unittest
from fractions import Fraction
from pathlib import Path

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputPlayer
from chonoi.rng import Streams
from chonoi.runner import Session
from chonoi.sim.quan import QuanSim
from helpers import ROOT, Workdir, ingredient_fixture, item_schema_enabled, write_json

DISH = "ca_loc_nuong_trui"


def customer(**fields):
    return {"id": "C1", "table_id": "T1", "dish_id": DISH, **fields}


def cooked_dish(order_id="C1", base_price=60):
    return {"order_id": order_id, "dish_id": DISH, "base_price": base_price}


class QuanTests(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]
        # Preserve count-based fixtures and explicit layouts after v1.2 is enabled.
        self.tuning.pop("freshness", None)
        quan = self.tuning["quan"]
        quan["stoves"] = [stove for stove in quan["stoves"] if stove["id"] == "B1"]
        quan["tables"] = [table for table in quan["tables"] if table["id"] == "T1"]

    def play(self, scenario, ticks, frames=(), inventory=None):
        session = Session("quan", self.tuning, scenario, seed=42, inventory=inventory)
        inputs = InputPlayer(frames)
        snapshots = [session.snapshot()]
        events = []
        for tick in range(ticks):
            events.extend(session.step(inputs.advance(tick)))
            snapshots.append(session.snapshot())
            if session.done:
                break
        return events, snapshots

    def test_arrival_uses_phase_tick_and_reserves_recipe_from_inventory(self):
        events, snapshots = self.play(
            {"time_left_ticks": 121}, 120, inventory={"ca_loc": 1}
        )
        self.assertEqual(events, [{
            "type": "event", "tick": 120, "phase": "quan", "name": "customer_arrived",
            "data": {"order_id": "C1", "table_id": "T1", "dish_id": DISH},
        }])
        self.assertEqual(snapshots[119]["customers"], [])
        self.assertEqual(snapshots[120]["stock"], {"ca_loc": 1})
        arrived = snapshots[120]["customers"][0]
        self.assertEqual(arrived["reserved"], {"ca_loc": 1})
        self.assertEqual(arrived["patience_ticks_left"], 3600)

    def test_no_dish_only_when_a_table_is_free(self):
        events, _ = self.play({}, 1020)
        self.assertEqual([(e["tick"], e["name"], e["data"]) for e in events],
                         [(120, "no_dish", {}), (1020, "no_dish", {})])
        events, _ = self.play({"stock": {"ca_loc": 1}, "customers": [customer()]}, 120)
        self.assertEqual(events, [])

    def test_inventory_reserved_for_one_table_is_unavailable_to_another(self):
        self.tuning["quan"]["tables"].append({"id": "T2", "pos": [4, 4]})
        events, snapshots = self.play(
            {"stock": {"ca_loc": 1}, "customers": [customer()]}, 120
        )
        self.assertEqual([e["name"] for e in events], ["no_dish"])
        self.assertEqual(snapshots[0]["customers"][0]["reserved"], {"ca_loc": 1})
        self.assertIsNone(snapshots[-1]["tables"][1]["customer_id"])

    def test_fixture_conflicts_exit_2_before_opening_output(self):
        stock = ingredient_fixture(["ca_loc", "ca_loc"]) if item_schema_enabled() else {"ca_loc": 2}
        reserved = ["I1", "I2"] if item_schema_enabled() else {"ca_loc": 2}
        fixtures = (
            {"customers": [customer()]},
            {"stock": stock, "customers": [customer(reserved=reserved)]},
            {"customers": [customer(order_status="assigned")]},
            {"customers": [customer(state="eating", order_status="served", eat_ticks_left=1)]},
            {"customers": [customer(order_status="assigned", patience_ticks_left=-1)]},
            {"hand": {"order_id": "C9", "dish_id": DISH, "base_price": 60}},
            {"stoves": [{"id": "B1", "state": "cooking", "cook_ticks_left": 0}]},
            {"tables": [{"id": "T1", "customer_id": "C1"}]},
        )
        with Workdir() as work:
            out = work.path("out.jsonl")
            with open(out, "w", encoding="utf-8") as file:
                file.write("original")
            for fixture in fixtures:
                with self.subTest(fixture=fixture):
                    scenario = write_json(work.path("scenario.json"), {"quan": fixture})
                    result = subprocess.run([
                        sys.executable, "-B", "-m", "chonoi.headless", "--mode", "quan",
                        "--scenario", scenario, "--seed", "42", "--ticks", "0", "--out", out,
                    ], cwd=ROOT, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 2, result.stderr)
                    with open(out, encoding="utf-8") as file:
                        self.assertEqual(file.read(), "original")

    def test_cook_pick_on_ready_tick_and_serve_after_releasing_button(self):
        scenario = {
            "player": {"pos": [2, 8]},
            "tables": [{"id": "T1", "pos": [3, 8]}],
            "stock": {"ca_loc": 1},
            "customers": [customer()],
            "random_customers": False,
        }
        events, snapshots = self.play(scenario, 381, [
            {"tick": 0, "interact": True},
            {"tick": 1, "interact": False},
            {"tick": 360, "interact": True},
            {"tick": 361, "move": [1, 0]},
            {"tick": 379, "interact": False, "move": [0, 0]},
            {"tick": 380, "interact": True},
        ])
        self.assertEqual([(e["tick"], e["name"]) for e in events], [
            (1, "cook_started"), (361, "dish_ready"), (361, "dish_picked"), (381, "served"),
        ])
        self.assertEqual(events[0]["data"], {
            "stove_id": "B1", **cooked_dish(), "items": ["ca_loc"],
        })
        self.assertEqual(snapshots[1]["customers"][0]["reserved"], {})
        self.assertEqual(snapshots[1]["stock"], {})
        self.assertEqual(snapshots[360]["stoves"][0]["cook_ticks_left"], 1)
        self.assertEqual(snapshots[361]["hand"], cooked_dish())
        self.assertIsNone(snapshots[381]["hand"])
        self.assertEqual(snapshots[381]["customers"][0]["eat_ticks_left"], 600)

    def test_equal_distance_selects_stove_even_if_it_cannot_interact(self):
        scenario = {
            "player": {"pos": [3.5, 8]},
            "tables": [{"id": "T1", "pos": [5, 8]}],
            "stoves": [{"id": "B1", "state": "cooking", "cook_ticks_left": 2, "dish": cooked_dish()}],
            "customers": [customer(order_status="assigned")],
        }
        events, snapshots = self.play(scenario, 2, [{"tick": 0, "interact": True}])
        self.assertEqual([(e["tick"], e["name"]) for e in events], [(2, "dish_ready")])
        self.assertEqual(snapshots[2]["stoves"][0]["ready_ticks"], 0)

        scenario["stoves"] = []
        scenario["hand"] = cooked_dish()
        events, snapshots = self.play(scenario, 1, [{"tick": 0, "interact": True}])
        self.assertEqual(events, [])
        self.assertEqual(snapshots[-1]["hand"], cooked_dish())

    def test_serving_at_exact_radius_patience_and_closing_deadlines(self):
        events, _ = self.play({
            "player": {"pos": [10.5, 2]},
            "time_left_ticks": 1,
            "hand": cooked_dish(),
            "customers": [customer(order_status="assigned", patience_ticks_left=1)],
        }, 1, [{"tick": 0, "interact": True}])
        self.assertEqual(events[0]["name"], "served")
        self.assertEqual(events[0]["data"], {
            **cooked_dish(), "table_id": "T1", "patience_ticks_left": 0, "tip": 0,
        })

    def test_tip_threshold_uses_patience_after_decrement_and_payment_waits_for_eating(self):
        for patience, tip in ((1800, 0), (1801, 12)):
            with self.subTest(patience=patience):
                events, snapshots = self.play({
                    "player": {"pos": [9, 2]}, "random_customers": False,
                    "hand": cooked_dish(),
                    "customers": [customer(order_status="assigned", patience_ticks_left=patience)],
                }, 601, [{"tick": 0, "interact": True}])
                self.assertEqual([(e["tick"], e["name"]) for e in events],
                                 [(1, "served"), (601, "paid")])
                self.assertEqual(events[0]["data"]["tip"], tip)
                self.assertEqual(events[1]["data"], {
                    "order_id": "C1", "table_id": "T1", "base_price": 60, "tip": tip,
                    "amount": 60 + tip, "reason": "finished_eating",
                })
                self.assertEqual(snapshots[600]["money"], 0)
                self.assertEqual(snapshots[601]["earned"], 60 + tip)
                self.assertEqual(snapshots[601]["reputation"], 3.2 if tip else 3)
                self.assertEqual(snapshots[601]["customers"], [])

    def test_tip_floors_the_decimal_rate_applied_to_locked_price(self):
        self.tuning["quan"]["tip_rate"] = 0.58
        events, _ = self.play({
            "player": {"pos": [9, 2]}, "time_left_ticks": 1,
            "hand": cooked_dish(base_price=50),
            "customers": [customer(order_status="assigned")],
        }, 1, [{"tick": 0, "interact": True}])
        self.assertEqual(events[0]["data"]["tip"], 29)
        self.assertEqual(events[1]["data"]["amount"], 79)

    def test_waiting_customer_leaves_before_arrival_and_releases_raw_stock(self):
        events, snapshots = self.play({
            "stock": {"ca_loc": 1}, "customers": [customer(id="C9", patience_ticks_left=120)],
        }, 120)
        self.assertEqual([(e["tick"], e["name"]) for e in events],
                         [(120, "customer_left"), (120, "customer_arrived")])
        self.assertEqual(events[0]["data"], {
            "order_id": "C9", "table_id": "T1", "reason": "patience", "reputation": 2.5,
        })
        self.assertEqual(events[1]["data"]["order_id"], "C10")
        self.assertEqual(snapshots[120]["stock"], {"ca_loc": 1})
        self.assertEqual(snapshots[120]["customers"][0]["reserved"], {"ca_loc": 1})

    def test_closing_pays_eaters_and_clears_waiting_orders_in_table_order(self):
        self.tuning["quan"]["tables"].extend([
            {"id": "T10", "pos": [5, 8]}, {"id": "T2", "pos": [6, 8]},
        ])
        events, snapshots = self.play({
            "time_left_ticks": 1,
            "player": {"pos": [9, 2]},
            "hand": cooked_dish(),
            "stoves": [{"id": "B1", "state": "ready", "dish": cooked_dish("C2")}],
            "customers": [
                customer(id="C3", table_id="T10", state="eating", order_status="served",
                         eat_ticks_left=1, base_price=60, tip=12),
                customer(id="C2", table_id="T2", order_status="assigned", patience_ticks_left=1),
                customer(order_status="assigned"),
            ],
        }, 1, [{"tick": 0, "interact": True}])
        self.assertEqual([e["name"] for e in events], ["served", "paid", "customer_left", "paid", "quan_end"])
        self.assertEqual([(e["data"]["table_id"], e["data"]["reason"]) for e in events[1:4]],
                         [("T1", "closing"), ("T2", "closing"), ("T10", "finished_eating")])
        self.assertEqual(events[-1]["data"], {
            "reason": "time", "money": 144, "earned": 144, "shift_earned": 144, "reputation": 3.4,
        })
        final = snapshots[-1]
        self.assertEqual(final["customers"], [])
        self.assertEqual(final["stock"], {})
        self.assertIsNone(final["hand"])
        self.assertEqual(final["stoves"][0]["state"], "idle")
        self.assertIsNone(final["stoves"][0]["dish"])
        self.assertTrue(all(table["customer_id"] is None for table in final["tables"]))

    def test_reputation_uses_exact_whole_number_for_score_and_clamps(self):
        self.tuning["quan"]["tables"].extend([
            {"id": "T2", "pos": [5, 8]}, {"id": "T3", "pos": [6, 8]},
        ])
        customers = [
            customer(id=f"C{n}", table_id=f"T{n}", state="eating", order_status="served",
                     eat_ticks_left=1, base_price=60, tip=12)
            for n in range(1, 4)
        ]
        for start, reputation, score in ((1.4, 2, 416), (4.9, 5, 716)):
            with self.subTest(start=start):
                _, snapshots = self.play({"customers": customers, "reputation": start}, 1)
                self.assertEqual(snapshots[-1]["reputation"], reputation)
                self.assertEqual(snapshots[-1]["score"], score)

    def test_patience_drops_dish_without_refunding_used_ingredients(self):
        for location in (
            {"hand": cooked_dish()},
            {"stoves": [{"id": "B1", "state": "cooking", "cook_ticks_left": 2, "dish": cooked_dish()}]},
        ):
            with self.subTest(location=location):
                events, snapshots = self.play({
                    **location, "reputation": 0.2,
                    "customers": [customer(order_status="assigned", patience_ticks_left=1)],
                }, 1)
                self.assertEqual([e["name"] for e in events], ["customer_left"])
                self.assertEqual(events[0]["data"]["reputation"], 0)
                self.assertEqual(snapshots[-1]["stock"], {})
                self.assertIsNone(snapshots[-1]["hand"])
                self.assertEqual(snapshots[-1]["stoves"][0]["state"], "idle")


class QuanPhase2Tests(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]
        self.tuning.pop("freshness", None)
        delta_path = Path(ROOT) / "docs" / "contracts" / "phase-2.tuning.json"
        delta = json.loads(delta_path.read_text(encoding="utf-8"))["tuning"]
        self.tuning["quan"].update(delta["quan"])
        self.tuning["menu"].update(delta["menu"])
        self.plans = delta["day_plan"]

    def make_quan(self, scenario, **kwargs):
        return QuanSim(self.tuning, scenario, Streams(42), IdAllocator(), **kwargs)

    @staticmethod
    def play(sim, ticks, frames=()):
        inputs = InputPlayer(frames)
        events = []
        for tick in range(ticks):
            events.extend((tick + 1, name, data) for name, data in sim.step(inputs.advance(tick)))
            if sim.done:
                break
        return events

    def test_standalone_uses_expanded_layout_and_all_recipes(self):
        for expected_dish, stock in (
            ("ca_keo_nuong", {"ca_keo": 2}),
            ("lau_mam", {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1}),
        ):
            with self.subTest(dish=expected_dish):
                sim = self.make_quan({}, inventory=stock)
                self.assertEqual([stove["id"] for stove in sim.snapshot()["stoves"]], ["B1", "B2"])
                self.assertEqual([table["id"] for table in sim.snapshot()["tables"]], ["T1", "T2", "T3", "T4"])
                self.assertEqual(self.play(sim, 120), [
                    (120, "customer_arrived", {"order_id": "C1", "table_id": "T1", "dish_id": expected_dish}),
                ])
                self.assertEqual(sim.snapshot()["stock"], stock)
                self.assertEqual(sim.snapshot()["customers"][0]["reserved"], stock)

        # Canh chua and grilled ca loc share an ingredient. Exercise the explicit recipe.
        sim = self.make_quan({"player": {"pos": [5, 8]}, "customers": [
            customer(table_id="T4", dish_id="canh_chua_ca_loc"),
        ]}, inventory={"ca_loc": 1, "bong_dien_dien": 1})
        self.assertEqual(self.play(sim, 1, [{"tick": 0, "interact": True}]), [
            (1, "cook_started", {"stove_id": "B2", "order_id": "C1", "dish_id": "canh_chua_ca_loc",
                                 "items": ["bong_dien_dien", "ca_loc"], "base_price": 90}),
        ])

    def test_day_plan_filters_before_reserving_at_smallest_free_table(self):
        sim = self.make_quan({"customers": [customer(id="C7", table_id="T2")]},
                             inventory={"ca_loc": 2, "ca_keo": 2}, day_plan=self.plans[0])
        self.assertEqual(self.play(sim, 120), [
            (120, "customer_arrived", {"order_id": "C8", "table_id": "T1", "dish_id": DISH}),
        ])
        self.assertEqual([row["customer_id"] for row in sim.snapshot()["tables"]], ["C8", "C7", None, None])

    def test_day_reports_no_dish_when_planned_recipe_is_reserved(self):
        sim = self.make_quan({"customers": [customer(dish_id="goi_bong_sung")]},
                             inventory={"bong_sung": 2, "ca_loc": 1}, day_plan=self.plans[2])
        self.assertEqual(self.play(sim, 120), [(120, "no_dish", {})])
        self.assertEqual(sim.snapshot()["stock"], {"bong_sung": 2, "ca_loc": 1})

    def test_day_plan_quantity_does_not_cap_orders_after_payment(self):
        sim = self.make_quan({
            "player": {"pos": [2, 8]},
            "tables": [{"id": "T1", "pos": [3, 8]}],
        }, inventory={"ca_loc": 3}, day_plan={"dishes": {DISH: 1}, "ingredients": {"ca_loc": 1}})
        events = self.play(sim, 1920, [
            {"tick": 120, "interact": True}, {"tick": 121, "interact": False},
            {"tick": 480, "interact": True}, {"tick": 481, "move": [1, 0]},
            {"tick": 499, "interact": False, "move": [0, 0]}, {"tick": 500, "interact": True},
        ])
        self.assertIn((1101, "paid"), [(tick, name) for tick, name, _ in events])
        self.assertEqual([(tick, data["dish_id"]) for tick, name, data in events if name == "customer_arrived"],
                         [(120, DISH), (1020, DISH), (1920, DISH)])

    def test_day_fixtures_use_actual_stock_and_plan(self):
        for plan, inventory in (
            (self.plans[0], {"ca_keo": 2}),
            (self.plans[2], {"ca_keo": 1}),
        ):
            with self.subTest(plan=plan, inventory=inventory), self.assertRaises(BadInput):
                self.make_quan({"customers": [customer(dish_id="ca_keo_nuong")]},
                               inventory=inventory, day_plan=plan)

    def test_two_stoves_take_oldest_orders_tied_by_table_id(self):
        sim = self.make_quan({
            "player": {"pos": [3.5, 8]},
            "customers": [
                customer(id="C90", table_id="T1", order_tick=2),
                customer(id="C9", table_id="T2", order_tick=1),
                customer(id="C2", table_id="T3", order_tick=1),
            ],
        }, inventory={"ca_loc": 3})
        events = self.play(sim, 25, [
            {"tick": 0, "interact": True},
            {"tick": 1, "interact": False, "move": [1, 0]},
            {"tick": 24, "interact": True, "move": [0, 0]},
        ])
        self.assertEqual([(tick, name, data["stove_id"], data["order_id"]) for tick, name, data in events],
                         [(1, "cook_started", "B1", "C9"), (25, "cook_started", "B2", "C2")])
        self.assertEqual(sim.snapshot()["stock"], {"ca_loc": 1})

    def test_closing_returns_total_progress_and_unconsumed_stock(self):
        progress = {"money": 10, "earned": 210, "reputation": 2.1}
        plan = {"dishes": {DISH: 1, "ca_keo_nuong": 1}, "ingredients": {"ca_loc": 1, "ca_keo": 2}}
        sim = self.make_quan({
            "time_left_ticks": 1,
            "customers": [
                customer(id="C2", table_id="T2", dish_id="ca_keo_nuong"),
                customer(state="eating", order_status="served", eat_ticks_left=3, base_price=60, tip=12),
            ],
        }, inventory={"ca_keo": 2}, day_plan=plan, progress=progress)
        self.assertEqual((sim.money, sim.earned, sim.reputation, sim.shift_earned), (10, 210, 2.1, 0))
        events = self.play(sim, 1)
        self.assertEqual([name for _, name, _ in events], ["paid", "customer_left", "quan_end"])
        self.assertEqual(events[-1][2], {
            "reason": "time", "money": 82, "earned": 282, "shift_earned": 72, "reputation": 2.3,
        })
        self.assertEqual(sim.snapshot()["stock"], {"ca_keo": 2})
        self.assertEqual(sim.snapshot()["customers"], [])


def stock_item(item_id, fresh, kind="ca_loc"):
    return {"id": item_id, "kind": kind, "fresh": fresh}


class QuanPhase3Tests(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]
        # Activate the documented v1.2 rules without switching the shared manifest.
        self.tuning["freshness"] = {
            "initial": 100, "gather_decay_per_s": 0.5,
            "quan_decay_per_s": 0.25, "spoiled_below": 30,
        }

    def make_quan(self, inventory=None, **scenario):
        return QuanSim(self.tuning, {"random_customers": False, **scenario}, Streams(42), IdAllocator(),
                       inventory=inventory)

    @staticmethod
    def play(sim, ticks, frames=()):
        inputs = InputPlayer(frames)
        events = []
        start_tick = sim.phase_tick
        for tick in range(start_tick, start_tick + ticks):
            events.extend((tick + 1, name, data) for name, data in sim.step(inputs.advance(tick)))
            if sim.done:
                break
        return events

    def test_fixture_assigns_remaining_items_by_order_then_freshness_and_id(self):
        stock = [stock_item("I10", 80), stock_item("I99", 100), stock_item("I2", 80), stock_item("I1", 29)]
        sim = self.make_quan(stock, customers=[
            customer(id="C3", table_id="T3", order_tick=9, reserved=["I99"]),
            customer(id="C2", table_id="T2", order_tick=1),
            customer(order_tick=1),
        ])
        snap = sim.snapshot()
        self.assertEqual([row["reserved"] for row in snap["customers"]], [["I2"], ["I10"], ["I99"]])
        self.assertEqual([item["id"] for item in snap["stock"]], ["I1", "I2", "I10", "I99"])
        self.assertEqual(snap["stock"][0]["fresh"], 29)

    def test_unsupplied_stock_is_empty_and_scenario_stock_is_available_at_tick_zero(self):
        self.assertEqual(self.make_quan().snapshot()["stock"], [])
        stock = [stock_item("I1", 30)]
        sim = self.make_quan(stock=stock)
        self.assertEqual(sim.snapshot()["stock"], stock)

    def test_stock_accepts_catalog_ingredients_absent_from_menu(self):
        self.tuning["menu"] = {DISH: self.tuning["menu"][DISH]}
        stock = [{"id": "I7", "kind": "keo_neo", "fresh": 90}]
        sim = self.make_quan(stock)
        self.assertEqual(sim.snapshot()["stock"], stock)

    def test_fixture_rejects_wrong_shape_spoiled_items_and_conflicting_reservations(self):
        stock = [stock_item("I2", 29), stock_item("I3", 60), stock_item("I4", 70, "bong_sung")]
        for reservations in (
            [customer(reserved={"ca_loc": 1})],
            [customer(reserved=["I2"])],
            [customer(reserved=["I4"])],
            [customer(reserved=["I9"])],
            [customer(reserved=["I3", "I3"])],
            [customer(reserved=["I3"]), customer(id="C2", table_id="T2", reserved=["I3"])],
            [customer(order_status="unfulfillable", reserved=["I3"])],
        ):
            with self.subTest(reservations=reservations), self.assertRaises(BadInput):
                self.make_quan(stock, customers=reservations)
        with self.assertRaises(BadInput):
            self.make_quan({"ca_loc": 1})

    def test_reserved_item_can_reach_threshold_then_spoils_once(self):
        stock = [stock_item("I1", Fraction(7201, 240))]
        sim = self.make_quan(stock, customers=[customer(reserved=["I1"])])
        self.assertEqual(self.play(sim, 1), [])
        self.assertEqual(sim.snapshot()["stock"][0]["fresh"], 30)
        self.assertEqual(sim.snapshot()["customers"][0]["reserved"], ["I1"])
        self.assertEqual(stock[0]["fresh"], Fraction(7201, 240))
        self.assertEqual(self.play(sim, 2), [
            (2, "spoiled", {"item_id": "I1", "kind": "ca_loc", "location": "stock"}),
        ])
        self.assertLess(sim.snapshot()["stock"][0]["fresh"], 30)
        self.assertEqual(sim.snapshot()["customers"][0]["order_status"], "unfulfillable")
        self.assertEqual(sim.snapshot()["customers"][0]["reserved"], [])

    def test_re_reservation_uses_order_priority_before_ready_and_cooking(self):
        stock = [stock_item("I10", 30), stock_item("I2", 30), stock_item("I11", 50)]
        sim = self.make_quan(stock, player={"pos": [2, 8]}, customers=[
            customer(id="C2", table_id="T2", order_tick=1, reserved=["I10"]),
            customer(order_tick=2, reserved=["I2"]),
            customer(id="C3", table_id="T3", order_status="assigned"),
        ], stoves=[{"id": "B2", "state": "cooking", "cook_ticks_left": 1, "dish": cooked_dish("C3")}])
        events = self.play(sim, 1, [{"tick": 0, "interact": True}])
        self.assertEqual([name for _, name, _ in events], ["spoiled", "spoiled", "dish_ready", "cook_started"])
        self.assertEqual([data["item_id"] for _, _, data in events[:2]], ["I2", "I10"])
        self.assertEqual(events[-1][2]["order_id"], "C2")
        self.assertEqual(events[-1][2]["items"], [stock_item("I11", float(Fraction(11999, 240)))])
        self.assertEqual(events[-1][2]["base_price"], 29)
        snap = sim.snapshot()
        self.assertEqual(snap["customers"][0]["order_status"], "unfulfillable")
        self.assertEqual(snap["customers"][0]["reserved"], [])
        self.assertEqual([item["id"] for item in snap["stock"]], ["I2", "I10"])

    def test_re_reservation_replaces_the_whole_recipe(self):
        stock = [stock_item("I1", 30), stock_item("I2", 80),
                 stock_item("I3", 40, "bong_dien_dien"), stock_item("I4", 70, "bong_dien_dien")]
        sim = self.make_quan(stock, customers=[customer(dish_id="canh_chua_ca_loc", reserved=["I3", "I1"])])
        self.play(sim, 1)
        self.assertEqual(set(sim.snapshot()["customers"][0]["reserved"]), {"I2", "I4"})

    def test_new_customer_cannot_use_spoiled_or_held_items_but_can_use_released_stock(self):
        sim = self.make_quan([stock_item("I1", 28), stock_item("I2", 70)],
                             customers=[customer(reserved=["I2"], patience_ticks_left=121)],
                             random_customers=True)
        events = self.play(sim, 1020)
        self.assertEqual([(tick, name) for tick, name, _ in events],
                         [(120, "no_dish"), (121, "customer_left"), (1020, "customer_arrived")])
        self.assertEqual(sim.snapshot()["customers"][0]["reserved"], ["I2"])

    def test_cooking_consumes_exact_items_in_kind_and_id_order_and_floors_average(self):
        stock = [
            stock_item("I10", 70, "ca_linh"), stock_item("I2", 60, "ca_linh"),
            stock_item("I3", 50, "ca_keo"), stock_item("I4", 80, "keo_neo"),
            stock_item("I6", 90, "bong_dien_dien"), stock_item("I5", 100, "ca_linh"),
        ]
        sim = self.make_quan(stock, player={"pos": [2, 8]}, customers=[
            customer(dish_id="lau_mam", reserved=["I4", "I10", "I6", "I2", "I3"]),
        ])
        events = self.play(sim, 1, [{"tick": 0, "interact": True}])
        _, name, event = events[0]
        self.assertEqual(name, "cook_started")
        self.assertEqual(event["base_price"], 139)
        self.assertEqual([item["id"] for item in event["items"]], ["I6", "I3", "I2", "I10", "I4"])
        self.assertEqual([item["id"] for item in sim.snapshot()["stock"]], ["I5"])
        self.assertEqual(sim.snapshot()["customers"][0]["reserved"], [])

    def test_locked_price_and_tip_are_paid_on_the_closing_tick(self):
        sim = self.make_quan([stock_item("I1", 80)], player={"pos": [2, 8]},
                             tables=[{"id": "T1", "pos": [3, 8]}], time_left_ticks=381,
                             customers=[customer(reserved=["I1"])])
        events = self.play(sim, 381, [
            {"tick": 0, "interact": True}, {"tick": 1, "interact": False},
            {"tick": 360, "interact": True}, {"tick": 361, "move": [1, 0]},
            {"tick": 379, "interact": False, "move": [0, 0]}, {"tick": 380, "interact": True},
        ])
        self.assertEqual([(tick, name) for tick, name, _ in events], [
            (1, "cook_started"), (361, "dish_ready"), (361, "dish_picked"),
            (381, "served"), (381, "paid"), (381, "quan_end"),
        ])
        self.assertEqual(events[3][2]["base_price"], 47)
        self.assertEqual(events[3][2]["tip"], 9)
        self.assertEqual(events[4][2]["amount"], 56)
        self.assertEqual(events[4][2]["reason"], "closing")
        self.assertEqual(events[5][2]["earned"], 56)
        self.assertEqual(events[5][2]["reputation"], 3.2)
