"""Test tích hợp & tính tất định byte-for-byte cho M6.4 (PRD-0 mục E, G)."""

import json
import unittest

from helpers import Workdir, frames, read_jsonl, run_headless, snapshots, write_json


class IntegrationAndDeterminismM6(unittest.TestCase):
    def test_gather_to_quan_inventory_pipeline_deterministic(self):
        """Chạy 2 lần cùng seed luồng gather --inventory-out -> quan --inventory: JSONL và kho giống từng byte."""
        with Workdir() as w:
            sc_gather = write_json(w.path("dock.json"), {
                "gather": {"hold": ["ca_loc", "bong_sung", "bong_sung"]}
            })
            inp_gather = write_json(w.path("dock_in.json"), frames({"tick": 0, "interact": True}))
            inp_quan = write_json(w.path("quan_in.json"), frames(
                {"tick": 0, "move": [-1, 1]},
                {"tick": 40, "move": [0, 0]},
            ))

            for run_idx in (1, 2):
                g_out = w.path(f"gather_{run_idx}.jsonl")
                inv_out = w.path(f"inv_{run_idx}.json")
                q_out = w.path(f"quan_{run_idx}.jsonl")

                code, err = run_headless(
                    "--mode", "gather", "--seed", "42",
                    "--scenario", sc_gather, "--inputs", inp_gather,
                    "--ticks", "10", "--out", g_out, "--inventory-out", inv_out,
                )
                self.assertEqual(code, 0, err)

                with open(inv_out, encoding="utf-8") as f:
                    self.assertEqual(json.load(f), {"items": {"bong_sung": 2, "ca_loc": 1}})

                code, err = run_headless(
                    "--mode", "quan", "--seed", "42",
                    "--inventory", inv_out, "--inputs", inp_quan,
                    "--ticks", "120", "--out", q_out,
                )
                self.assertEqual(code, 0, err)
                snap0 = snapshots(read_jsonl(q_out))[0]
                self.assertEqual(snap0["stock"], {"bong_sung": 2, "ca_loc": 1})

            for prefix in ("gather", "inv", "quan"):
                ext = "json" if prefix == "inv" else "jsonl"
                with open(w.path(f"{prefix}_1.{ext}"), "rb") as a, open(w.path(f"{prefix}_2.{ext}"), "rb") as b:
                    self.assertEqual(a.read(), b.read(), f"{prefix} không tất định byte-for-byte")


if __name__ == "__main__":
    unittest.main()
