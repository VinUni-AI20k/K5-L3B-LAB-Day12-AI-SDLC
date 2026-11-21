"""P3-02: kho cá thể (contract 1.2), adapter đếm <-> cá thể, độ tươi số nguyên, migration test.

v1.2 chưa bật trong game.contract.json (bật ở P3-08); các test ở đây gọi thẳng hàm theo `contract_version`.
"""

import copy
import json
import os
import unittest

from helpers import ROOT, Workdir, write_json

from chonoi.contract import load_contract, validate_tuning
from chonoi.errors import BadInput
from chonoi.freshness import Freshness, decay_units_per_tick
from chonoi.inventory import (
    counts_to_individuals, hold_to_individuals, individuals_to_counts, inventory_schema, next_individual_id,
    read_inventory, read_inventory_for, read_inventory_v12, validate_individuals, write_inventory,
    write_inventory_v12,
)

CONTRACT = load_contract()
T = CONTRACT["tuning"]
SAMPLE = os.path.join(ROOT, "docs", "contracts", "inventory.v12.sample.json")


def text(path, mode="r"):
    with open(path, mode, **({"encoding": "utf-8"} if mode == "r" else {})) as f:
        return f.read()


def indiv(i, kind="ca_linh", fresh=100):
    return {"id": f"I{i}", "kind": kind, "fresh": fresh}


class FreshnessBlock(unittest.TestCase):
    def test_numbers_locked(self):
        """Đúng 4 khóa theo Ticket-03 (B đọc từ đề): initial, gather_decay_per_s, quan_decay_per_s, spoiled_below."""
        self.assertEqual(T["freshness"], {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25,
                                          "spoiled_below": 30})

    def test_integer_units_and_decay_per_tick(self):
        f = Freshness(T)
        self.assertEqual((f.max_units, f.spoil_units), (100 * 240, 30 * 240))
        self.assertEqual((f.decay("gather"), f.decay("quan")), (2, 1))  # 0.5 và 0.25 điểm/s ở 60 tick/s

    def test_spoil_threshold_exact(self):
        f = Freshness(T)
        self.assertFalse(f.is_spoiled(f.spoil_units))
        self.assertTrue(f.is_spoiled(f.spoil_units - 1))

    def test_threshold_tick_is_exact_in_gather(self):
        """Từ 100 điểm, hao 2 đơn vị/tick: ươn đúng sau (24000 - 7200 + 1) / 2 làm tròn lên tick."""
        f = Freshness(T)
        units, ticks = f.max_units, 0
        while not f.is_spoiled(units):
            units -= f.decay("gather")
            ticks += 1
        self.assertEqual(ticks, (f.max_units - f.spoil_units) // f.decay("gather") + 1)

    def test_points_roundtrip_through_file_rounding(self):
        f = Freshness(T)
        for units in range(0, f.max_units + 1, 7):
            self.assertEqual(f.to_units(f.to_points(units)), units)

    def test_decay_must_be_whole_units_per_tick(self):
        bad = dict(T["freshness"], quan_decay_per_s=0.3)
        with self.assertRaises(BadInput):
            decay_units_per_tick(bad, T["tick_hz"], "quan")

    def test_freshness_required_only_at_v12(self):
        t = copy.deepcopy(T)
        del t["freshness"]
        validate_tuning(t, "1.1")
        with self.assertRaises(BadInput):
            validate_tuning(t, "1.2")

    def test_freshness_validated_when_present(self):
        for edit in (lambda f: f.update(spoiled_below=101), lambda f: f.update(initial=0),
                     lambda f: f.pop("quan_decay_per_s"), lambda f: f.update(extra=1),
                     lambda f: f.update(gather_decay_per_s=0.4), lambda f: f.update(gather_decay_per_s=-1),
                     lambda f: f.update(units_per_point=240)):
            t = copy.deepcopy(T)
            edit(t["freshness"])
            with self.assertRaises(BadInput, msg=str(t["freshness"])):
                validate_tuning(t, "1.2")

    def test_v12_contract_file_loads(self):
        with Workdir() as w:
            data = json.loads(json.dumps(CONTRACT))
            data["contract_version"] = "1.2"
            path = write_json(w.path("c12.json"), data)
            self.assertEqual(load_contract(path)["contract_version"], "1.2")
            del data["tuning"]["freshness"]
            path = write_json(w.path("c12-missing.json"), data)
            with self.assertRaises(BadInput):
                load_contract(path)


class DishPrice(unittest.TestCase):
    """Công thức giá của đề: floor(giá niêm yết * trung bình fresh / 100), không hệ số phụ."""

    def test_formula_exact_with_integer_units(self):
        f = Freshness(T)
        pts = lambda *p: [f.to_units(x) for x in p]  # noqa: E731
        self.assertEqual(f.dish_price(120, pts(100, 50)), 90)
        self.assertEqual(f.dish_price(120, pts(100, 100)), 120)
        self.assertEqual(f.dish_price(120, pts(0)), 0)
        self.assertEqual(f.dish_price(100, [7199]), 29)  # 29.996 điểm: floor, không làm tròn
        self.assertEqual(f.dish_price(100, [7200]), 30)
        self.assertEqual(f.dish_price(7, pts(100, 99, 98)), 6)  # 7 * 99 / 100 = 6.93 -> 6

    def test_boundary_one_unit_changes_floor(self):
        f = Freshness(T)
        full = f.max_units
        self.assertEqual(f.dish_price(100, [full]), 100)
        self.assertEqual(f.dish_price(100, [full - 1]), 99)  # thiếu 1 đơn vị là xuống 99

    def test_needs_ingredients(self):
        with self.assertRaises(ValueError):
            Freshness(T).dish_price(100, [])


class IndividualSchema(unittest.TestCase):
    def test_sample_file_valid(self):
        self.assertEqual(read_inventory_v12(SAMPLE), [indiv(1, "ca_linh", 100), indiv(2, "bong_sung", 30)])

    def test_order_is_kept(self):
        items = [indiv(3), indiv(1, "ca_loc"), indiv(2, "bong_sung", 12.5)]
        self.assertEqual(validate_individuals(items), items)

    def test_bad_individuals_rejected(self):
        for items in ({"ca_loc": 1}, [indiv(1), indiv(1)], [{"id": "", "kind": "ca_loc", "fresh": 5}],
                      [{"id": 7, "kind": "ca_loc", "fresh": 5}], [indiv(1, "ca_la")], [indiv(1, fresh=-1)],
                      [indiv(1, fresh=float("nan"))], [indiv(1, fresh=float("inf"))],
                      [indiv(1, fresh=101)], [indiv(1, fresh=True)], [indiv(1, fresh="100")],
                      [{"id": "I1", "kind": "ca_loc"}], [{"id": "I1", "kind": "ca_loc", "fresh": 5, "x": 1}], ["I1"]):
            with self.assertRaises(BadInput, msg=str(items)):
                validate_individuals(items)

    def test_any_non_empty_unique_string_is_a_valid_id(self):
        """Ticket-03: id là chuỗi duy nhất khác rỗng, không bắt buộc dạng I<n>."""
        items = [{"id": "X1", "kind": "ca_loc", "fresh": 5}, {"id": "abc", "kind": "bong_sung", "fresh": 60}]
        self.assertEqual(validate_individuals(items), items)
        self.assertEqual(next_individual_id(items), 1)  # chỉ id dạng I<n> tính vào bộ đếm
        self.assertEqual(next_individual_id(items + [indiv(4)]), 5)

    def test_write_then_read_is_stable_bytes(self):
        items = [indiv(2, "ca_loc", 99.917), indiv(1, "bong_sung", 30)]
        with Workdir() as w:
            a, b = w.path("a.json"), w.path("b.json")
            write_inventory_v12(a, items)
            write_inventory_v12(b, read_inventory_v12(a))
            self.assertEqual(text(a, "rb"), text(b, "rb"))
            self.assertEqual(read_inventory_v12(a), items)
            self.assertEqual(text(a),
                             '{"items":[{"id":"I2","kind":"ca_loc","fresh":99.917},'
                             '{"id":"I1","kind":"bong_sung","fresh":30}]}\n')


class MigrationByVersion(unittest.TestCase):
    def test_schema_selection(self):
        self.assertEqual([inventory_schema(v) for v in ("1.0", "1.1", "1.2", "1.3")],
                         ["counts", "counts", "individuals", "individuals"])

    def test_v12_rejects_counting_file(self):
        with Workdir() as w:
            path = w.path("counts.json")
            write_inventory(path, {"ca_loc": 2})
            with self.assertRaises(BadInput):
                read_inventory_for(path, "1.2")
            self.assertEqual(read_inventory_for(path, "1.1"), {"ca_loc": 2})

    def test_v11_rejects_individual_file(self):
        with self.assertRaises(BadInput):
            read_inventory_for(SAMPLE, "1.1")
        with self.assertRaises(BadInput):
            read_inventory(SAMPLE)
        self.assertEqual(len(read_inventory_for(SAMPLE, "1.2")), 2)

    def test_missing_or_broken_file_is_bad_input(self):
        with Workdir() as w:
            with self.assertRaises(BadInput):
                read_inventory_for(w.path("nope.json"), "1.2")
            path = w.path("broken.json")
            with open(path, "w", encoding="utf-8") as f:
                f.write("{")
            with self.assertRaises(BadInput):
                read_inventory_for(path, "1.2")
            write_json(path, {"items": [], "extra": 1})
            with self.assertRaises(BadInput):
                read_inventory_for(path, "1.2")

    def test_empty_inventory_is_valid_in_both_schemas(self):
        with Workdir() as w:
            write_json(w.path("e.json"), {"items": []})
            write_json(w.path("d.json"), {"items": {}})
            self.assertEqual(read_inventory_for(w.path("e.json"), "1.2"), [])
            self.assertEqual(read_inventory_for(w.path("d.json"), "1.1"), {})


class Adapters(unittest.TestCase):
    def test_counts_to_individuals_order_and_ids(self):
        items = counts_to_individuals({"bong_sung": 2, "ca_loc": 1, "keo_neo": 0})
        self.assertEqual(items, [indiv(1, "ca_loc"), indiv(2, "bong_sung"), indiv(3, "bong_sung")])
        self.assertEqual(counts_to_individuals({"ca_loc": 1}, fresh=30, start_id=7), [indiv(7, "ca_loc", 30)])

    def test_roundtrip_counts(self):
        counts = {"bong_dien_dien": 1, "bong_sung": 2, "ca_keo": 1, "ca_linh": 2, "ca_loc": 1, "keo_neo": 3}
        self.assertEqual(individuals_to_counts(counts_to_individuals(counts)), counts)
        self.assertEqual(individuals_to_counts([]), {})

    def test_counts_are_independent_of_freshness_and_order(self):
        items = [indiv(5, "ca_loc", 12), indiv(2, "bong_sung", 99), indiv(9, "ca_loc", 0)]
        self.assertEqual(individuals_to_counts(items), {"bong_sung": 1, "ca_loc": 2})

    def test_hold_keeps_pickup_order(self):
        hold = ["ca_loc", "bong_sung", "ca_loc"]
        items = hold_to_individuals(hold, start_id=4)
        self.assertEqual([it["id"] for it in items], ["I4", "I5", "I6"])
        self.assertEqual([it["kind"] for it in items], hold)

    def test_next_id_never_reuses(self):
        self.assertEqual(next_individual_id([]), 1)
        self.assertEqual(next_individual_id([indiv(3), indiv(10)]), 11)

    def test_adapter_output_is_valid_schema(self):
        validate_individuals(counts_to_individuals({"ca_loc": 2, "ca_keo": 1}))


if __name__ == "__main__":
    unittest.main()
