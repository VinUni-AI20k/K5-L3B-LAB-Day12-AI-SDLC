"""Phase 4 mở rộng (TICKET-04 mục 3): bảng xếp hạng cục bộ.

- headless `--mode day` nhận cặp `--leaderboard <store> --player-name <name>`; ghi đúng một mục khi đủ 5 Ngày
  chuẩn (không scenario, reason "days_complete"); thiếu một cờ hoặc sai mode → mã 2.
- `<run_cmd> --export-leaderboard <out> [--leaderboard <store>]` xuất {"entries":[{name,score,days_completed,seed}]}.
- Top 10, điểm giảm dần, hòa thì mục ghi trước đứng trước. Soak không ghi xếp hạng.
"""

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from chonoi import headless, leaderboard, live  # noqa: E402
from chonoi.errors import BadInput  # noqa: E402

TICKS = "120000"


def _run(fn, argv):
    err = io.StringIO()
    with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
        try:
            rc = fn(argv)
        except SystemExit as e:  # argparse
            rc = e.code
    return rc, err.getvalue()


def _read(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _end(path):
    with open(path, encoding="utf-8") as f:
        return json.loads(f.read().splitlines()[-1])


class _Tmp(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.d = self._td.name

    def tearDown(self):
        self._td.cleanup()

    def p(self, name):
        return os.path.join(self.d, name)

    def day(self, *extra, days="5", seed="7"):
        return _run(headless.main, ["--mode", "day", "--days", days, "--seed", seed, "--ticks", TICKS,
                                    "--out", self.p("out.jsonl"), *extra])


class RecordP4(_Tmp):
    def test_standard_run_writes_one_entry_matching_end_row(self):
        rc, err = self.day("--leaderboard", self.p("lb.json"), "--player-name", "Út Sen")
        self.assertEqual(rc, 0, err)
        end = _end(self.p("out.jsonl"))
        self.assertEqual(end["reason"], "days_complete")
        self.assertEqual(_read(self.p("lb.json")), {"entries": [
            {"name": "Út Sen", "score": end["score"], "days_completed": 5, "seed": 7}]})

    def test_second_run_appends_exactly_one(self):
        self.day("--leaderboard", self.p("lb.json"), "--player-name", "A")
        rc, err = self.day("--leaderboard", self.p("lb.json"), "--player-name", "B", seed="3")
        self.assertEqual(rc, 0, err)
        names = [e["name"] for e in _read(self.p("lb.json"))["entries"]]
        self.assertEqual(sorted(names), ["A", "B"])

    def test_jsonl_unchanged_by_flags(self):
        self.day()
        plain = _text(self.p("out.jsonl"))
        self.day("--leaderboard", self.p("lb.json"), "--player-name", "A")
        self.assertEqual(_text(self.p("out.jsonl")), plain)

    def test_not_standard_no_entry(self):
        rc, err = self.day("--leaderboard", self.p("lb.json"), "--player-name", "A", days="4")
        self.assertEqual(rc, 0, err)
        self.assertFalse(os.path.exists(self.p("lb.json")))
        sc = self.p("sc.json")
        with open(sc, "w", encoding="utf-8") as f:
            json.dump({"day": {}}, f)
        rc, err = self.day("--scenario", sc, "--leaderboard", self.p("lb.json"), "--player-name", "A")
        self.assertEqual(rc, 0, err)
        self.assertFalse(os.path.exists(self.p("lb.json")))

    def test_tick_limit_no_entry(self):
        rc, err = _run(headless.main, ["--mode", "day", "--days", "5", "--seed", "7", "--ticks", "1000",
                                       "--out", self.p("out.jsonl"), "--leaderboard", self.p("lb.json"),
                                       "--player-name", "A"])
        self.assertEqual(rc, 0, err)
        self.assertFalse(os.path.exists(self.p("lb.json")))


class BadFlagsP4(_Tmp):
    def _short(self, *argv, mode="day"):
        return _run(headless.main, ["--mode", mode, "--seed", "1", "--ticks", "10", "--out", self.p("o.jsonl"), *argv])

    def test_missing_one_flag_exit_2(self):
        self.assertEqual(self._short("--leaderboard", self.p("lb.json"))[0], 2)
        self.assertEqual(self._short("--player-name", "A")[0], 2)
        self.assertFalse(os.path.exists(self.p("o.jsonl")))

    def test_wrong_mode_exit_2(self):
        for mode in ("gather", "quan"):
            rc, _ = self._short("--leaderboard", self.p("lb.json"), "--player-name", "A", mode=mode)
            self.assertEqual(rc, 2, mode)
        self.assertFalse(os.path.exists(self.p("o.jsonl")))

    def test_bad_store_or_name_exit_2(self):
        with open(self.p("lb.json"), "w", encoding="utf-8") as f:
            f.write("{không phải json")
        self.assertEqual(self._short("--leaderboard", self.p("lb.json"), "--player-name", "A")[0], 2)
        self.assertEqual(self._short("--leaderboard", self.p("x.json"), "--player-name", "  ")[0], 2)
        self.assertFalse(os.path.exists(self.p("o.jsonl")))

    def test_store_same_as_out_exit_2(self):
        self.assertEqual(self._short("--leaderboard", self.p("o.jsonl"), "--player-name", "A")[0], 2)


class RankingP4(unittest.TestCase):
    def test_sorted_desc_ties_keep_write_order_top10(self):
        es = []
        for i, s in enumerate([100, 300, 300, 200, 50, 300, 10, 20, 30, 40, 60, 70]):
            es = leaderboard.add(es, f"p{i}", s, 5, i)
        self.assertEqual(len(es), 10)
        self.assertEqual([e["name"] for e in es[:4]], ["p1", "p2", "p5", "p3"])
        self.assertEqual([e["score"] for e in es], sorted([e["score"] for e in es], reverse=True))
        self.assertNotIn("p6", [e["name"] for e in es])  # 10 điểm: thấp nhất, bị đẩy ra

    def test_new_tie_with_tenth_is_dropped(self):
        es = []
        for i in range(10):
            es = leaderboard.add(es, f"p{i}", 100, 5, i)
        es = leaderboard.add(es, "late", 100, 5, 99)
        self.assertNotIn("late", [e["name"] for e in es])

    def test_load_rejects_bad_schema(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "lb.json")
            for bad in ([], {"entries": {}}, {"entries": [{"name": "a", "score": 1}]},
                        {"entries": [{"name": "a", "score": 1.5, "days_completed": 5, "seed": 1}]},
                        {"entries": []}, ):
                with open(p, "w", encoding="utf-8") as f:
                    json.dump(bad, f)
                if bad == {"entries": []}:
                    self.assertEqual(leaderboard.load(p), [])
                else:
                    with self.assertRaises(BadInput):
                        leaderboard.load(p)


class ExportP4(_Tmp):
    def test_export_from_store(self):
        leaderboard.save(self.p("lb.json"), leaderboard.add(leaderboard.add([], "A", 10, 5, 1), "B", 20, 5, 2))
        rc, err = _run(live.main, ["--mode", "gather", "--export-leaderboard", self.p("out.json"),
                                   "--leaderboard", self.p("lb.json")])
        self.assertEqual(rc, 0, err)
        out = _read(self.p("out.json"))
        self.assertEqual(list(out), ["entries"])
        self.assertEqual([e["name"] for e in out["entries"]], ["B", "A"])
        for e in out["entries"]:
            self.assertEqual(set(e), {"name", "score", "days_completed", "seed"})

    def test_export_missing_store_is_empty(self):
        rc, err = _run(live.main, ["--mode", "gather", "--export-leaderboard", self.p("out.json"),
                                   "--leaderboard", self.p("none.json")])
        self.assertEqual(rc, 0, err)
        self.assertEqual(_read(self.p("out.json")), {"entries": []})

    def test_export_bad_store_exit_2(self):
        with open(self.p("lb.json"), "w", encoding="utf-8") as f:
            f.write("[]")
        rc, _ = _run(live.main, ["--mode", "gather", "--export-leaderboard", self.p("out.json"),
                                 "--leaderboard", self.p("lb.json")])
        self.assertEqual(rc, 2)
        self.assertFalse(os.path.exists(self.p("out.json")))

    def test_leaderboard_without_export_exit_2(self):
        rc, _ = _run(live.main, ["--mode", "gather", "--leaderboard", self.p("lb.json")])
        self.assertEqual(rc, 2)


class SoakDoesNotRecordP4(unittest.TestCase):
    def test_soak_has_no_leaderboard_hook(self):
        import soak
        src = _text(soak.__file__)
        self.assertNotIn("leaderboard", src)


if __name__ == "__main__":
    unittest.main()
