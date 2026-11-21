"""Lát 2: hái/bắt thật, đưa về bến và chuyển kho qua hai tiến trình."""

import json
import os
import unittest

from helpers import ROOT, Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


FIXTURES = os.path.join(ROOT, "tests", "fixtures", "gather_lat2")


class GatherInventory(unittest.TestCase):
    def test_collect_dock_export_and_load_in_separate_quan_process(self):
        with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
            tuning = json.load(f)["tuning"]["gather"]
        expected = {"items": {
            "bong_sung": 2 * tuning["node_yield"],
            "bong_dien_dien": tuning["node_yield"],
            "ca_linh": tuning["fish_yield"]["ca_linh"],
            "ca_loc": tuning["fish_yield"]["ca_loc"],
        }}
        with Workdir() as w:
            # Lặp cùng seed để kiểm cả JSONL và file kho giống từng byte.
            for suffix in ("a", "b"):
                code, err = run_headless(
                    "--mode", "gather", "--seed", "42", "--ticks", "240",
                    "--scenario", os.path.join(FIXTURES, "dock.json"),
                    "--inputs", os.path.join(FIXTURES, "inputs.json"),
                    "--inventory-out", w.path(f"catch-{suffix}.json"),
                    "--out", w.path(f"gather-{suffix}.jsonl"),
                )
                self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("gather-a.jsonl"))
            self.assertEqual([e["data"]["node_id"] for e in events(rows, "gather")], ["N2", "N3", "N10"])
            self.assertEqual([e["data"]["fish_id"] for e in events(rows, "fish_caught")], ["F2", "F10"])
            end = events(rows, "gather_end")
            self.assertEqual(len(end), 1)
            self.assertEqual(end[0]["tick"], 181)
            self.assertEqual(end[0]["data"], {"reason": "docked", "inventory": expected})
            with open(w.path("catch-a.json"), encoding="utf-8") as f:
                self.assertEqual(json.load(f), expected)
            for pattern in ("gather-{}.jsonl", "catch-{}.json"):
                with open(w.path(pattern.format("a")), "rb") as a, open(w.path(pattern.format("b")), "rb") as b:
                    self.assertEqual(a.read(), b.read())
            code, err = run_headless(
                "--mode", "quan", "--seed", "42", "--ticks", "0",
                "--inventory", w.path("catch-a.json"), "--out", w.path("quan.jsonl"),
            )
            self.assertEqual(code, 0, err)
            self.assertEqual(snapshots(read_jsonl(w.path("quan.jsonl")))[0]["stock"], expected["items"])

    def test_final_tick_catch_is_in_timeout_inventory(self):
        with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
            count = json.load(f)["tuning"]["gather"]["fish_yield"]["ca_loc"]
        with Workdir() as w:
            scenario = write_json(w.path("scenario.json"), {"gather": {
                "player": {"pos": [20, 5]}, "time_left_ticks": 1, "nodes": [],
                "fish": [{"id": "F1", "kind": "ca_loc", "pos": [20, 5]}],
            }})
            inputs = write_json(w.path("inputs.json"), frames({"tick": 0, "catch": True}))
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "10", "--scenario", scenario,
                "--inputs", inputs, "--inventory-out", w.path("catch.json"), "--out", w.path("out.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("out.jsonl"))
            self.assertEqual([e["name"] for e in events(rows)], ["fish_caught", "gather_end"])
            self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "time")
            with open(w.path("catch.json"), encoding="utf-8") as f:
                inventory = json.load(f)
            self.assertEqual(inventory, {"items": {"ca_loc": count}})
            self.assertEqual(inventory, events(rows, "gather_end")[0]["data"]["inventory"])
            self.assertEqual(snapshots(rows)[-1]["hold"], ["ca_loc"] * count)


if __name__ == "__main__":
    unittest.main()
