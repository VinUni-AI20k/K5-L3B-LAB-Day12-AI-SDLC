"""Test adapter kho cá thể (AC-P3-01): chonoi/freshness.py và đọc/ghi kho theo contract_version (chonoi/inventory.py).

Đối chiếu docs/contracts/phase-3.md, ADR 0001 và hai file mẫu docs/contracts/inventory{,.v1.2}.sample.json.
Chạy: PYTHONPATH=tests:. python3 -m unittest discover -s tests -p 'test_freshness.py' -v
"""

import json
import os
import unittest
from collections import Counter
from fractions import Fraction

from chonoi.errors import BadInput
from chonoi.freshness import age_items, new_item, parse_items, to_fraction, view_items
from chonoi.ids import IdAllocator
from chonoi.inventory import KINDS_P2, is_item_schema, read_inventory, write_inventory
from helpers import ROOT, Workdir, write_json

SAMPLE_V11 = os.path.join(ROOT, "docs", "contracts", "inventory.sample.json")
SAMPLE_V12 = os.path.join(ROOT, "docs", "contracts", "inventory.v1.2.sample.json")
# Số liệu tuning.freshness theo docs/contracts/phase-3.md (manifest trên main còn v1.1, chưa có khối này)
FRESHNESS = {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30}
THR = FRESHNESS["spoiled_below"]
TICK_HZ = 60


def item(iid, kind="ca_loc", fresh=100):
    return {"id": iid, "kind": kind, "fresh": fresh}


class InventoryAdapter(unittest.TestCase):
    """Đọc/ghi kho theo version: v1.0/v1.1 giữ nguyên, v1.2 là mảng cá thể với fresh chính xác."""

    def read12(self, obj):
        with Workdir() as w:
            return read_inventory(write_json(w.path("kho.json"), obj), KINDS_P2, contract_version="1.2")

    def test_two_samples_hold_the_same_counts_by_kind(self):
        counts = read_inventory(SAMPLE_V11, KINDS_P2)
        items = read_inventory(SAMPLE_V12, KINDS_P2, contract_version="1.2")
        self.assertEqual(Counter(it["kind"] for it in items), Counter(counts))
        self.assertEqual([(it["id"], it["kind"]) for it in items], [("I1", "bong_sung"), ("I2", "bong_sung"),
                                                                     ("I3", "ca_loc")])
        self.assertEqual([it["fresh"] for it in items], [Fraction(100), Fraction(2999, 100), Fraction(195, 2)],
                         "fresh đọc thành phân số chính xác, không qua float; nhận cả hàng đã ươn (29.99)")

    def test_v12_reads_decimal_text_without_float_rounding(self):
        """Hợp đồng: đọc số thập phân không qua làm tròn trước khi kiểm độ tươi (qua float thì 29.99…9 thành 30.0)."""
        with Workdir() as w:
            with open(w.path("k.json"), "w", encoding="utf-8") as f:
                f.write('{"items":[{"id":"I1","kind":"ca_loc","fresh":29.999999999999999999}]}')
            (got,) = read_inventory(w.path("k.json"), KINDS_P2, contract_version="1.2")
        self.assertEqual(got["fresh"], Fraction("29.999999999999999999"))
        self.assertLess(got["fresh"], THR, "vẫn là hàng ươn")

    def test_version_selects_schema_and_old_interface_is_unchanged(self):
        self.assertEqual([is_item_schema(v) for v in ("1.0", "1.1", "1.2", "1.3")], [False, False, True, True])
        with self.assertRaises(BadInput):  # v1.2 từ chối kho đếm
            read_inventory(SAMPLE_V11, KINDS_P2, contract_version="1.2")
        with self.assertRaises(BadInput):  # giao diện cũ (không truyền version) từ chối mảng cá thể
            read_inventory(SAMPLE_V12, KINDS_P2)
        with Workdir() as w:
            write_inventory(w.path("k.json"), {"ca_loc": 1, "bong_sung": 0})
            with open(w.path("k.json"), encoding="utf-8") as f:
                self.assertEqual(f.read(), '{"items":{"ca_loc":1}}\n')

    def test_v12_rejects_bad_records(self):
        bad = {
            "id trùng": [item("I1"), item("I1")],
            "id rỗng": [item("")],
            "id không phải chuỗi": [item(1)],
            "loại lạ": [item("I1", "ca_la_lung")],
            "fresh âm": [item("I1", fresh=-0.01)],
            "fresh > 100": [item("I1", fresh=100.01)],
            "fresh chuỗi": [item("I1", fresh="50")],
            "fresh boolean": [item("I1", fresh=True)],
            "fresh null": [item("I1", fresh=None)],
            "thiếu khóa": [{"id": "I1", "kind": "ca_loc"}],
            "khóa lạ": [{**item("I1"), "x": 1}],
            "phần tử không phải object": ["ca_loc"],
        }
        for label, items in bad.items():
            with self.assertRaises(BadInput, msg=label):
                self.read12({"items": items})
        for label, text in {"NaN": '{"items":[{"id":"I1","kind":"ca_loc","fresh":NaN}]}',
                            "vô cực": '{"items":[{"id":"I1","kind":"ca_loc","fresh":1e999}]}',
                            "khóa gốc lạ": '{"items":[],"x":1}'}.items():
            with Workdir() as w:
                with open(w.path("k.json"), "w", encoding="utf-8") as f:
                    f.write(text)
                with self.assertRaises(BadInput, msg=label):
                    read_inventory(w.path("k.json"), KINDS_P2, contract_version="1.2")
        self.assertEqual(self.read12({"items": []}), [], "kho rỗng là {\"items\":[]}")
        self.assertEqual([it["fresh"] for it in self.read12({"items": [item("I1", fresh=0), item("I2", fresh=100)]})],
                         [0, 100], "đúng hai mép miền [0, 100]")

    def test_write_v12_sorts_by_id_atomically_and_byte_stable(self):
        view = view_items([item("I10", "ca_linh", Fraction(97, 2)), item("I2")], THR)
        with Workdir() as w:
            for name in ("a.json", "b.json"):
                write_inventory(w.path(name), view, contract_version="1.2")
            with open(w.path("a.json"), "rb") as a, open(w.path("b.json"), "rb") as b:
                raw = a.read()
                self.assertEqual(raw, b.read())
            self.assertEqual(raw, b'{"items":[{"id":"I2","kind":"ca_loc","fresh":100.0},'
                                  b'{"id":"I10","kind":"ca_linh","fresh":48.5}]}\n')
            self.assertEqual(sorted(os.listdir(w.path(""))), ["a.json", "b.json"], "không sót file tạm")

    def test_write_then_read_keeps_each_item_on_its_side_of_threshold(self):
        exact = [Fraction(THR), Fraction(THR) - Fraction(1, 120), Fraction(THR) - Fraction(1, 10 ** 20),
                 Fraction(THR) + Fraction(1, 10 ** 20), Fraction(2999, 100) - Fraction(1, 120), Fraction(0),
                 Fraction(100)]
        items = [item(f"I{i}", fresh=x) for i, x in enumerate(exact, 1)]
        with Workdir() as w:
            write_inventory(w.path("k.json"), view_items(items, THR), contract_version="1.2")
            back = read_inventory(w.path("k.json"), KINDS_P2, contract_version="1.2")
        self.assertEqual([it["id"] for it in back], [it["id"] for it in items])
        for orig, got in zip(exact, back):
            self.assertEqual(got["fresh"] < THR, orig < THR, (orig, got["fresh"]))
            self.assertLess(abs(got["fresh"] - orig), Fraction(1, 10 ** 12), (orig, got["fresh"]))


class FreshnessHelpers(unittest.TestCase):
    """parse_items / new_item / age_items / view_items theo docs/contracts/phase-3.md."""

    def test_parse_items_returns_new_records_in_input_order(self):
        raw = [item("I3", "ca_linh", 50), item("I1", "keo_neo", 29.99)]
        out = parse_items(raw, KINDS_P2)
        self.assertEqual([(it["id"], it["kind"], it["fresh"]) for it in out],
                         [("I3", "ca_linh", 50), ("I1", "keo_neo", Fraction(2999, 100))])
        out[0]["fresh"] = 0
        self.assertEqual(raw[0]["fresh"], 50, "bản ghi mới, không dùng chung với đầu vào")

    def test_new_item_continues_shared_allocator_with_initial_freshness(self):
        ids = IdAllocator()
        ids.reserve("I5")
        ids.reserve("F9")
        a, b = (new_item(ids, "ca_loc", FRESHNESS["initial"]) for _ in range(2))
        self.assertEqual([(x["id"], x["kind"], x["fresh"]) for x in (a, b)],
                         [("I6", "ca_loc", 100), ("I7", "ca_loc", 100)])

    def test_age_items_decays_exactly_clamps_and_reports_spoiled_once_by_id(self):
        step = to_fraction(FRESHNESS["gather_decay_per_s"]) / TICK_HZ
        items = [item("I10", fresh=THR), item("I2", fresh=THR), item("I3", fresh=100), item("I4", fresh=step / 2)]
        events = age_items(items, FRESHNESS["gather_decay_per_s"], TICK_HZ, THR, "hold")
        self.assertEqual(events, [("spoiled", {"item_id": "I2", "kind": "ca_loc", "location": "hold"}),
                                  ("spoiled", {"item_id": "I10", "kind": "ca_loc", "location": "hold"})],
                         "cùng tick nhiều cá thể qua ngưỡng -> phát theo id")
        self.assertEqual([it["id"] for it in items], ["I10", "I2", "I3", "I4"], "hao tại chỗ, giữ thứ tự")
        self.assertEqual([it["fresh"] for it in items], [THR - step, THR - step, 100 - step, 0])
        self.assertEqual(age_items(items, FRESHNESS["gather_decay_per_s"], TICK_HZ, THR, "hold"), [],
                         "đã dưới ngưỡng thì không phát lại")
        self.assertEqual(age_items([], 0.5, TICK_HZ, THR, "hold"), [])
        stock = [item("I1", fresh=THR)]
        self.assertEqual(age_items(stock, FRESHNESS["quan_decay_per_s"], TICK_HZ, THR, "stock"),
                         [("spoiled", {"item_id": "I1", "kind": "ca_loc", "location": "stock"})])
        self.assertEqual(stock[0]["fresh"], THR - to_fraction(FRESHNESS["quan_decay_per_s"]) / TICK_HZ)

    def test_view_items_copies_in_order_and_stays_on_the_same_side_of_threshold(self):
        just_below = Fraction(THR) - Fraction(1, 10 ** 20)  # float() làm tròn lên đúng 30.0
        items = [item("I2", fresh=Fraction(THR)), item("I1", fresh=just_below), item("I3", fresh=Fraction(1, 3))]
        view = view_items(items, THR)
        self.assertEqual([v["id"] for v in view], ["I2", "I1", "I3"])
        self.assertEqual(view[0]["fresh"], 30.0)
        self.assertLess(view[1]["fresh"], THR)
        self.assertEqual(json.loads(json.dumps(view[2]["fresh"])), float(Fraction(1, 3)), "đủ chữ số qua JSON")
        view[0]["fresh"] = 1.0
        self.assertEqual(items[0]["fresh"], THR, "bản sao, không đụng kho nội bộ")


if __name__ == "__main__":
    unittest.main()
