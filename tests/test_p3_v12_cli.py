"""P3-07, P3-08: contract 1.2 bật thật. Chạy `headless_cmd` với đúng game.contract.json (v12=True), hộp đen.

Kho là mảng cá thể {id, kind, fresh}; file kho đếm của v1.1 bị từ chối (mã 2) và ngược lại; scenario `gather.hold`,
`quan.stock` và `customers[].reserved` theo schema mới. Phase 1-2 chạy hồi quy với bản 1.1 (xem tests/helpers.py).
"""

import json
import os
import unittest

from helpers import Workdir, events, read_jsonl, run_headless, snapshots, write_json

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.freshness import Freshness
from chonoi.scenario import check_reserved_within_stock, load_scenario

CONTRACT = load_contract()
T = CONTRACT["tuning"]
F = Freshness(T)
Q = T["quan"]
GATHER_DECAY_POINTS = F.to_points(F.decay("gather"))


def item(n, kind="ca_loc", fresh=100):
    return {"id": f"I{n}", "kind": kind, "fresh": fresh}


def gather(hold, ticks=1, frames=None, seed=42, extra=None):
    """Chạy headless gather v1.2; trả (mã, dòng JSONL, kho ghi ra hoặc None, stderr)."""
    with Workdir() as w:
        args = ["--mode", "gather", "--seed", str(seed), "--ticks", str(ticks), "--out", w.path("g.jsonl"),
                "--inventory-out", w.path("kho.json"), "--snapshot-every", "1"]
        block = {"hold": hold, **(extra or {})}
        args += ["--scenario", write_json(w.path("s.json"), {"gather": block})]
        if frames:
            args += ["--inputs", write_json(w.path("i.json"), {"frames": frames})]
        code, err = run_headless(*args, v12=True)
        rows = read_jsonl(w.path("g.jsonl")) if code == 0 else []
        try:
            with open(w.path("kho.json"), encoding="utf-8") as f:
                kho = json.load(f)
        except OSError:
            kho = None
    return code, rows, kho, err


class Manifest(unittest.TestCase):
    def test_game_contract_is_v12_with_freshness(self):
        self.assertEqual(CONTRACT["contract_version"], "1.3")  # kho cá thể từ 1.2 trở lên
        self.assertEqual(set(T["freshness"]), {"initial", "gather_decay_per_s", "quan_decay_per_s", "spoiled_below"})


class GatherInventoryOut(unittest.TestCase):
    def test_docking_writes_individuals_with_decay(self):
        hold = [item(1, "ca_loc", 100), item(2, "bong_sung", 30), item(3, "bong_sung", 100)]
        code, rows, kho, err = gather(hold, ticks=1, frames=[{"tick": 0, "interact": True}])
        self.assertEqual(code, 0, err)
        end = events(rows, "gather_end")[-1]["data"]
        self.assertEqual(end["reason"], "docked")
        decayed = F.to_points(F.max_units - F.decay("gather"))
        self.assertEqual(kho, {"items": [item(1, "ca_loc", decayed), item(2, "bong_sung", F.to_points(F.spoil_units - F.decay("gather"))),
                                         item(3, "bong_sung", decayed)]})
        self.assertEqual(end["inventory"], kho)

    def test_threshold_item_spoils_on_first_tick_and_is_reported(self):
        code, rows, _, err = gather([item(1, "ca_loc", 30)], ticks=1, frames=[{"tick": 0, "interact": True}])
        self.assertEqual(code, 0, err)
        spoiled = events(rows, "spoiled")
        self.assertEqual([(e["tick"], e["data"]["id"], e["data"]["kind"]) for e in spoiled], [(1, "I1", "ca_loc")])

    def test_just_above_threshold_does_not_spoil_on_first_tick(self):
        above = F.to_points(F.spoil_units + F.decay("gather"))  # sau 1 tick hao đúng bằng ngưỡng: chưa ươn
        code, rows, _, err = gather([item(1, "ca_loc", above)], ticks=1, frames=[{"tick": 0, "interact": True}])
        self.assertEqual(code, 0, err)
        self.assertEqual(events(rows, "spoiled"), [])

    def test_unfinished_run_does_not_write_inventory(self):
        code, _, kho, err = gather([item(1)], ticks=1)  # không cập bến, chưa hết giờ
        self.assertEqual(code, 0, err)
        self.assertIsNone(kho)

    def test_faint_writes_empty_inventory(self):
        player = {"pos": [20, 5], "hp": 1, "oxygen_ticks": 0, "zero_oxy_ticks": T["gather"]["choke_interval_ticks"] - 1}
        code, rows, kho, err = gather([item(1), item(2, "bong_sung")], ticks=2, extra={"player": player})
        self.assertEqual(code, 0, err)
        faint = events(rows, "faint")[-1]["data"]
        self.assertEqual([i["id"] for i in faint["lost"]], ["I2", "I1"])  # LIFO theo thứ tự vào giỏ
        self.assertEqual(kho, {"items": []})

    def test_snapshot_hold_is_individuals_in_pickup_order(self):
        code, rows, _, err = gather([item(5, "ca_loc"), item(2, "bong_sung")], ticks=0)
        self.assertEqual(code, 0, err)
        hold = snapshots(rows)[0]["hold"]
        self.assertEqual([i["id"] for i in hold], ["I5", "I2"])
        self.assertEqual(snapshots(rows)[0]["hold_count"], 2)


class Handoff(unittest.TestCase):
    def test_gather_to_quan_two_processes_keep_id_kind_fresh(self):
        hold = [item(1, "ca_loc", 100), item(2, "bong_sung", 30), item(3, "bong_sung", 100)]
        with Workdir() as w:
            args = ["--mode", "gather", "--seed", "42", "--ticks", "1", "--out", w.path("g.jsonl"),
                    "--scenario", write_json(w.path("s.json"), {"gather": {"hold": hold}}),
                    "--inputs", write_json(w.path("i.json"), {"frames": [{"tick": 0, "interact": True}]}),
                    "--inventory-out", w.path("kho.json")]
            self.assertEqual(run_headless(*args, v12=True)[0], 0)
            code, err = run_headless("--mode", "quan", "--seed", "42", "--ticks", "0", "--inventory", w.path("kho.json"),
                                     "--out", w.path("q.jsonl"), v12=True)
            self.assertEqual(code, 0, err)
            with open(w.path("kho.json"), encoding="utf-8") as f:
                kho = json.load(f)["items"]
            stock = snapshots(read_jsonl(w.path("q.jsonl")))[0]["stock"]
        self.assertEqual(stock, kho)
        self.assertEqual([(i["id"], i["kind"]) for i in stock], [("I1", "ca_loc"), ("I2", "bong_sung"), ("I3", "bong_sung")])

    def test_quan_reads_fresh_100_and_fresh_30_exactly(self):
        stock = [item(1, "ca_loc", 100), item(2, "ca_linh", 30)]
        with Workdir() as w:
            write_json(w.path("kho.json"), {"items": stock})
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", w.path("kho.json"),
                                     "--out", w.path("q.jsonl"), v12=True)
            self.assertEqual(code, 0, err)
            self.assertEqual(snapshots(read_jsonl(w.path("q.jsonl")))[0]["stock"], stock)

    def test_handoff_bytes_are_deterministic(self):
        outs = []
        for _ in range(2):
            code, rows, kho, err = gather([item(1), item(2, "bong_sung", 77.5)], ticks=1, frames=[{"tick": 0, "interact": True}])
            self.assertEqual(code, 0, err)
            outs.append((json.dumps(rows), json.dumps(kho)))
        self.assertEqual(outs[0], outs[1])


class SchemaByVersion(unittest.TestCase):
    def test_v12_rejects_counting_inventory(self):
        with Workdir() as w:
            write_json(w.path("kho.json"), {"items": {"ca_loc": 1}})
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", w.path("kho.json"),
                                     "--out", w.path("q.jsonl"), v12=True)
            self.assertEqual(code, 2, err)

    def test_v11_rejects_individual_inventory(self):
        with Workdir() as w:
            write_json(w.path("kho.json"), {"items": [item(1)]})
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", w.path("kho.json"),
                                     "--out", w.path("q.jsonl"))  # mặc định: contract 1.1
            self.assertEqual(code, 2, err)

    def test_bad_individuals_are_exit_2_before_writing_output(self):
        for bad in ([item(1), item(1)], [{"id": "I1", "kind": "ca_loc"}], [item(1, fresh=101)], [item(1, "ca_la")], ["ca_loc"]):
            with Workdir() as w:
                write_json(w.path("kho.json"), {"items": bad})
                code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", w.path("kho.json"),
                                       "--out", w.path("q.jsonl"), v12=True)
                self.assertEqual(code, 2, bad)
                self.assertFalse(os.path.exists(w.path("q.jsonl")))

    def test_v12_rejects_kind_list_hold_and_over_capacity(self):
        self.assertEqual(gather(["ca_loc"])[0], 2)
        too_many = [item(i + 1) for i in range(T["gather"]["hold_capacity"] + 1)]
        self.assertEqual(gather(too_many)[0], 2)


class ScenarioV12(unittest.TestCase):
    def quan(self, **block):
        with Workdir() as w:
            path = write_json(w.path("s.json"), {"quan": block})
            return load_scenario(path, "quan", T, "1.2")

    def test_stock_and_reservations_by_id(self):
        stock = [item(1, "ca_loc"), item(2, "bong_sung"), item(3, "bong_sung")]
        customers = [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}]
        self.assertEqual(self.quan(stock=stock, customers=customers)["stock"], stock)

    def test_bad_reservations_rejected(self):
        stock = [item(1, "ca_loc"), item(2, "bong_sung")]
        base = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}
        for customers in ([{**base, "reserved": ["I9"]}],                     # id không có trong kho
                          [{**base, "reserved": ["I2"]}],                     # khác công thức
                          [{**base, "reserved": {"ca_loc": 1}}],              # dạng đếm của v1.1
                          [{**base, "reserved": ["I1", "I1"]}],               # trùng id
                          [{**base, "reserved": ["I1"]}, {**base, "id": "C2", "table_id": "T2", "reserved": ["I1"]}]):
            with self.assertRaises(BadInput, msg=str(customers)):
                self.quan(stock=stock, customers=customers)

    def test_v11_counting_stock_rejected_at_v12(self):
        with self.assertRaises(BadInput):
            self.quan(stock={"ca_loc": 1})

    def test_reserved_checked_against_inventory_file_by_id(self):
        customers = [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}]
        block = self.quan(customers=customers)
        check_reserved_within_stock(block, [item(1, "ca_loc")])
        with self.assertRaises(BadInput):
            check_reserved_within_stock(block, [item(2, "ca_loc")])

    def test_headless_reservation_missing_from_inventory_exits_2(self):
        scenario = {"quan": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I7"]}]}}
        with Workdir() as w:
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--out", w.path("q.jsonl"),
                                     "--scenario", write_json(w.path("s.json"), scenario),
                                     "--inventory", write_json(w.path("kho.json"), {"items": [item(1, "ca_loc")]}), v12=True)
            self.assertEqual(code, 2, err)

    def test_day_scenario_validates_hold_as_individuals(self):
        with Workdir() as w:
            good = write_json(w.path("good.json"), {"gather": {"hold": [item(1)]}})
            self.assertEqual(load_scenario(good, "day", T, "1.2")["gather"]["hold"], [item(1)])
            bad = write_json(w.path("bad.json"), {"gather": {"hold": ["ca_loc"]}})
            with self.assertRaises(BadInput):
                load_scenario(bad, "day", T, "1.2")


class DayAndQuan(unittest.TestCase):
    def test_day_two_days_runs_to_completion_and_is_deterministic(self):
        digests = []
        for _ in range(2):
            with Workdir() as w:
                code, err = run_headless("--mode", "day", "--days", "2", "--seed", "3", "--ticks", "200000",
                                         "--snapshot-every", "600", "--out", w.path("d.jsonl"), v12=True)
                self.assertEqual(code, 0, err)
                with open(w.path("d.jsonl"), "rb") as f:
                    digests.append(f.read())
                end = read_jsonl(w.path("d.jsonl"))[-1]
        self.assertEqual(digests[0], digests[1])
        self.assertEqual((end["reason"], end["days_completed"]), ("days_complete", 2))

    def test_day_carries_individuals_with_same_tick_handoff_and_fresh_ids(self):
        scenario = {"gather": {"hold": [item(4, "ca_loc"), item(9, "bong_sung")], "time_left_ticks": 1, "random_fish": False}}
        with Workdir() as w:
            code, err = run_headless("--mode", "day", "--days", "2", "--seed", "1", "--ticks", "3", "--snapshot-every", "1",
                                     "--out", w.path("d.jsonl"), "--scenario", write_json(w.path("s.json"), scenario), v12=True)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("d.jsonl"))
        end = events(rows, "gather_end")[0]
        self.assertEqual((end["tick"], [i["id"] for i in end["data"]["inventory"]["items"]]), (1, ["I4", "I9"]))
        quan_start = [e for e in events(rows, "phase_start") if e["phase"] == "quan"][0]
        self.assertEqual(quan_start["tick"], 1)
        q = [s for s in snapshots(rows) if s["phase"] == "quan"][0]
        self.assertEqual([i["id"] for i in q["stock"]], ["I4", "I9"])

    def test_quan_full_shift_with_individuals_decays_stock(self):
        stock = [item(1, "bong_sung", 100)]
        with Workdir() as w:
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "10", "--snapshot-every", "10",
                                     "--out", w.path("q.jsonl"), "--inventory", write_json(w.path("kho.json"), {"items": stock}),
                                     v12=True)
            self.assertEqual(code, 0, err)
            last = snapshots(read_jsonl(w.path("q.jsonl")))[-1]["stock"][0]
        self.assertEqual(last["fresh"], F.to_points(F.max_units - 10 * F.decay("quan")))


class LegacyEnv(unittest.TestCase):
    def test_default_run_headless_uses_v11_and_v12_flag_uses_game_contract(self):
        """Hồi quy Phase 1-2 chạy bản 1.1 (CHONOI_CONTRACT); v12=True đọc đúng game.contract.json."""
        with Workdir() as w:
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--out", w.path("a.jsonl"),
                                     "--inventory", write_json(w.path("k.json"), {"items": {"ca_loc": 1}}))
            self.assertEqual(code, 0, err)
            self.assertEqual(snapshots(read_jsonl(w.path("a.jsonl")))[0]["stock"], {"ca_loc": 1})


if __name__ == "__main__":
    unittest.main()
