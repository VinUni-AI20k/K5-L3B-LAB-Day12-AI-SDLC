"""TV6 khung Phase 3 (T305, T306, T330, T331): scenario/kho theo version, id toàn cục, day bàn giao.

Không đụng inventory.py/contract.py (TV1). Khi TV1 chưa có validate_items_v12 / read|write(version=),
đường v1.2 báo "chờ TV1". v1.0/v1.1 headless phải giống từng byte so với cây HEAD (git archive).
"""

import filecmp
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inventory import read_inventory, write_inventory
from chonoi.runner import _item_ids, inventory_io
from chonoi.scenario import UNITS_PER_POINT, apply_items_v12, fresh_units, is_v12, load_scenario
from chonoi.sim.day import DaySim, DayState
from chonoi.sim.shop import ShopSim
from helpers import ROOT, Workdir, events, frames, headless_cmd, read_jsonl, snapshots, write_json

FIXTURE_V11 = os.path.join(ROOT, "tests", "fixtures", "contract-v1.1-day.json")
FIXTURE_V12 = os.path.join(ROOT, "tests", "fixtures", "contract-v1.2-freshness.json")
SC_GATHER_V12 = os.path.join(ROOT, "tests", "fixtures", "scenario-gather-hold-v12.json")
SC_QUAN_V12 = os.path.join(ROOT, "tests", "fixtures", "scenario-quan-reserved-v12.json")
INV_V12 = os.path.join(ROOT, "tests", "fixtures", "inventory-items-v12.json")


def _tuning_v12():
    with open(FIXTURE_V12, encoding="utf-8") as f:
        return json.load(f)["tuning"]


def _ok_items(items):
    """Stub TV1 validate_items_v12: chỉ kiểm khóa tối thiểu để khung scenario chạy được trong unit test."""
    if not isinstance(items, list):
        raise BadInput("items phải là mảng")
    seen = set()
    for it in items:
        if not isinstance(it, dict) or set(it) != {"id", "kind", "fresh"}:
            raise BadInput("mỗi cá thể cần đúng {id, kind, fresh}")
        if it["id"] in seen:
            raise BadInput(f"id trùng {it['id']}")
        seen.add(it["id"])
    return items


def run_headless(*args, contract=FIXTURE_V11):
    env = dict(os.environ, CHONOI_CONTRACT=contract)
    p = subprocess.run([*headless_cmd(), *args], cwd=ROOT, capture_output=True, text=True, env=env)
    return p.returncode, p.stderr


class HelpersTest(unittest.TestCase):
    def test_is_v12_and_fresh_units(self):
        self.assertFalse(is_v12(None))
        self.assertFalse(is_v12("1.1"))
        self.assertTrue(is_v12("1.2"))
        self.assertTrue(is_v12("1.10"))
        self.assertEqual(UNITS_PER_POINT, 240)
        self.assertEqual(fresh_units(30), 7200)
        self.assertEqual(fresh_units(100), 24000)


class InventoryIoTest(unittest.TestCase):
    def test_v10_keeps_legacy_functions(self):
        r, w = inventory_io("1.0")
        self.assertIs(r, read_inventory)
        self.assertIs(w, write_inventory)
        r, w = inventory_io("1.1")
        self.assertIs(r, read_inventory)

    def test_v12_waits_for_tv1_version_param(self):
        with self.assertRaises(BadInput) as cm:
            inventory_io("1.2")
        self.assertIn("chờ TV1", str(cm.exception))
        self.assertIn("read_inventory", str(cm.exception))


class ScenarioV12Test(unittest.TestCase):
    def test_apply_passthrough_when_not_v12(self):
        block = {"hold": ["ca_loc"]}
        self.assertIs(apply_items_v12("gather", block, _tuning_v12(), "1.1"), block)

    def test_v12_waits_for_tv1_validate_items(self):
        with open(SC_GATHER_V12, encoding="utf-8") as f:
            hold = json.load(f)["gather"]
        with self.assertRaises(BadInput) as cm:
            apply_items_v12("gather", hold, _tuning_v12(), "1.2")
        self.assertIn("chờ TV1", str(cm.exception))
        self.assertIn("validate_items_v12", str(cm.exception))

    def test_v12_rejects_duplicate_id_and_bad_reserved(self):
        t = _tuning_v12()
        with mock.patch("chonoi.inventory.validate_items_v12", _ok_items, create=True):
            with self.assertRaises(BadInput) as cm:
                apply_items_v12("gather", {
                    "hold": [{"id": "I1", "kind": "ca_loc", "fresh": 100},
                             {"id": "I1", "kind": "ca_linh", "fresh": 90}],
                }, t, "1.2")
            self.assertIn("trùng", str(cm.exception))

            stock = [{"id": "I1", "kind": "ca_loc", "fresh": 20},
                     {"id": "I2", "kind": "ca_loc", "fresh": 80}]
            with self.assertRaises(BadInput) as cm:
                apply_items_v12("quan", {
                    "stock": stock,
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                   "reserved": ["I1"]}],
                }, t, "1.2")
            self.assertIn("ươn", str(cm.exception))

            with self.assertRaises(BadInput) as cm:
                apply_items_v12("quan", {
                    "stock": stock,
                    "customers": [
                        {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I2"]},
                        {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "reserved": ["I2"]},
                    ],
                }, t, "1.2")
            self.assertIn("đã được giữ", str(cm.exception))

            with self.assertRaises(BadInput) as cm:
                apply_items_v12("quan", {
                    "stock": [{"id": "I9", "kind": "ca_loc", "fresh": 90}],
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                   "reserved": ["I404"]}],
                }, t, "1.2")
            self.assertIn("không có trong quan.stock", str(cm.exception))

    def test_v12_view_counts_and_reserved_kinds(self):
        t = _tuning_v12()
        with mock.patch("chonoi.inventory.validate_items_v12", _ok_items, create=True):
            with open(SC_QUAN_V12, encoding="utf-8") as f:
                block = json.load(f)["quan"]
            view = apply_items_v12("quan", block, t, "1.2")
            self.assertEqual(view["stock"], {"ca_loc": 2, "bong_sung": 1})
            self.assertEqual(view["customers"][0]["reserved"], {"ca_loc": 1})

    def test_load_scenario_v12_file(self):
        t = _tuning_v12()
        with mock.patch("chonoi.inventory.validate_items_v12", _ok_items, create=True):
            sc = load_scenario(SC_GATHER_V12, "gather", t, "1.2")
            self.assertEqual(sc["hold"][0]["id"], "I1")  # trả block gốc, không góc nhìn


class IdAllocatorFrameTest(unittest.TestCase):
    def test_item_ids_from_scenario_and_inventory_file_shape(self):
        sc = {"gather": {"hold": [{"id": "I3", "kind": "ca_loc", "fresh": 100}]},
              "quan": {"stock": [{"id": "I7", "kind": "ca_linh", "fresh": 50}]}}
        with open(INV_V12, encoding="utf-8") as f:
            inv = json.load(f)
        self.assertEqual(sorted(_item_ids(sc, inv)), ["I1", "I2", "I3", "I7"])
        ids = IdAllocator()
        for iid in _item_ids(sc, inv):
            ids.reserve(iid)
        self.assertEqual(ids.new("I"), "I8")


class DayHandoffTest(unittest.TestCase):
    def test_gather_end_quan_same_tick_no_extra_step(self):
        """AC-P3-19 khung: gather_end và phase_start quan cùng tick; stock = inventory (không hao thêm)."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {"hold": ["ca_loc", "bong_sung"], "random_fish": False},
                "quan": {"time_left_ticks": 1},
            })
            inp = write_json(w.path("i.json"), frames({"tick": 0, "interact": True}))
            out = w.path("o.jsonl")
            code, err = run_headless("--mode", "day", "--seed", "1", "--ticks", "5",
                                     "--scenario", sc, "--inputs", inp, "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            ge = events(rows, "gather_end")[0]
            ps = [e for e in events(rows, "phase_start") if e["phase"] == "quan"][0]
            self.assertEqual(ge["tick"], ps["tick"])
            snap = next(s for s in snapshots(rows) if s["tick"] == ge["tick"] and s["phase"] == "quan")
            self.assertEqual(snap["phase_tick"], 0)
            self.assertEqual(snap["stock"], ge["data"]["inventory"]["items"])
            self.assertEqual(snap["stock"], {"bong_sung": 1, "ca_loc": 1})

    def test_day2_reallocates_hold_item_ids(self):
        t = _tuning_v12()
        streams = __import__("chonoi.rng", fromlist=["Streams"]).Streams(1)
        ids = IdAllocator()
        sc = {"day": {}, "gather": {
            "hold": [{"id": "I1", "kind": "ca_linh", "fresh": 100},
                     {"id": "I2", "kind": "ca_loc", "fresh": 90}],
            "random_fish": False,
        }, "quan": {}}
        day = DaySim(t, sc, streams, ids, days=2, version="1.2")
        d1 = day._gather_scenario_for_day()
        self.assertEqual([it["id"] for it in d1["hold"]], ["I1", "I2"])
        day.day = 2
        d2 = day._gather_scenario_for_day()
        self.assertEqual([it["id"] for it in d2["hold"]], ["I3", "I4"])
        self.assertEqual([it["kind"] for it in d2["hold"]], ["ca_linh", "ca_loc"])
        self.assertEqual([it["fresh"] for it in d2["hold"]], [100, 90])
        # mẫu gốc không bị đổi
        self.assertEqual([it["id"] for it in day.tpl_gather["hold"]], ["I1", "I2"])

    def test_shop_individual_stock_does_not_decay(self):
        st = DayState(_tuning_v12(), {"money": 100, "earned": 100})
        items = [{"id": "I1", "kind": "ca_loc", "fresh": 50.0}]
        shop = ShopSim(_tuning_v12()["shop"], st, items)

        class _Inp:
            buy = None
            def pressed(self, _):
                return False
        for _ in range(10):
            shop.step(_Inp())
        self.assertEqual(shop.stock[0]["fresh"], 50.0)
        self.assertEqual(shop.snapshot()["stock"][0]["id"], "I1")


class HeadlessV12GateTest(unittest.TestCase):
    def test_inventory_out_v12_exits_2_before_out(self):
        with Workdir() as w:
            out, inv = w.path("o.jsonl"), w.path("inv.json")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "0",
                                     "--inventory-out", inv, "--out", out, contract=FIXTURE_V12)
            self.assertEqual(code, 2)
            self.assertIn("chờ TV1", err)
            self.assertFalse(os.path.exists(out))
            self.assertFalse(os.path.exists(inv))

    def test_inventory_in_v12_exits_2(self):
        with Workdir() as w:
            out = w.path("o.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                     "--inventory", INV_V12, "--out", out, contract=FIXTURE_V12)
            self.assertEqual(code, 2)
            self.assertIn("chờ TV1", err)
            self.assertFalse(os.path.exists(out))


class ByteIdentityVsHeadTest(unittest.TestCase):
    """v1.0/v1.1: so byte output headless với bản gốc HEAD (git archive)."""

    @classmethod
    def setUpClass(cls):
        cls._scratch = tempfile.mkdtemp(prefix="chonoi-head-")
        tar = subprocess.run(
            ["git", "archive", "HEAD", "chonoi", "game.contract.json", "tests"],
            cwd=ROOT, capture_output=True, check=True)
        subprocess.run(["tar", "-x"], cwd=cls._scratch, input=tar.stdout, check=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._scratch, ignore_errors=True)

    def _cmp_mode(self, mode, extra, ticks=30):
        with Workdir() as w:
            out_cur, out_old = w.path("cur.jsonl"), w.path("old.jsonl")
            args = ["--mode", mode, "--seed", "7", "--ticks", str(ticks), "--out"]
            env = dict(os.environ, CHONOI_CONTRACT=FIXTURE_V11, PYTHONPATH=f"tests:.")
            cur = subprocess.run(
                ["python3", "-m", "chonoi.headless", *args, out_cur, *extra],
                cwd=ROOT, capture_output=True, text=True, env=env)
            old = subprocess.run(
                ["python3", "-m", "chonoi.headless", *args, out_old, *extra],
                cwd=self._scratch, capture_output=True, text=True, env=env)
            self.assertEqual(cur.returncode, 0, cur.stderr)
            self.assertEqual(old.returncode, 0, old.stderr)
            self.assertTrue(filecmp.cmp(out_cur, out_old, shallow=False),
                            f"{mode}: output khác HEAD từng byte")

    def test_gather_bytes(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"hold": ["ca_loc"], "random_fish": False}})
            # copy scenario vào scratch cũng dùng path tuyệt đối → chung file
            self._cmp_mode("gather", ["--scenario", sc], ticks=20)

    def test_quan_bytes(self):
        with Workdir() as w:
            inv = write_json(w.path("inv.json"), {"items": {"ca_loc": 1}})
            self._cmp_mode("quan", ["--inventory", inv], ticks=0)

    def test_day_bytes(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {"hold": ["ca_loc"], "random_fish": False},
                "quan": {"time_left_ticks": 1},
            })
            self._cmp_mode("day", ["--scenario", sc, "--days", "1"], ticks=50)


if __name__ == "__main__":
    unittest.main()
