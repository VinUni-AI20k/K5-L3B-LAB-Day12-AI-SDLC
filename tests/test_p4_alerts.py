"""P4-04 (AC-P4-04): ba cảnh báo dễ nhận biết và chế độ tương phản cao.

Cảnh báo tính từ snapshot (chonoi/alerts.py). Test dựng snapshot bằng Session thật rồi kiểm đúng mốc kích hoạt.
"""

import json
import math
import os
import unittest

from chonoi import alerts
from chonoi.contract import load_contract
from chonoi.inputs import InputPlayer
from chonoi.live import LiveGame
from chonoi.runner import Session
from helpers import ROOT

TUNING = load_contract()["tuning"]
G, Q = TUNING["gather"], TUNING["quan"]
HZ = TUNING["tick_hz"]
SP = G["monsters"]["species"]["ca_sau"]
OXY_MAX = round(G["oxygen_max_s"] * HZ)
OXY_LOW = math.floor(alerts.OXYGEN_LOW_RATIO * OXY_MAX)
PATIENCE = round(Q["patience_s"] * HZ)
ANGRY = math.floor(alerts.CUSTOMER_ANGRY_RATIO * PATIENCE)
MID = sum(SP["depths"]) / 2


def gather_snap(monsters=(), **player):
    sc = {"fish": [], "nodes": [], "monsters": list(monsters),
          "player": {"pos": [50, MID], **player}}
    return Session("gather", TUNING, sc, 1).snapshot()


def ids(snap):
    return [a["id"] for a in alerts.compute(snap, TUNING)]


class OxygenLow(unittest.TestCase):
    def test_threshold_boundary(self):
        self.assertEqual(ids(gather_snap(oxygen_ticks=OXY_LOW + 1)), [])
        got = alerts.compute(gather_snap(oxygen_ticks=OXY_LOW), TUNING)
        self.assertEqual([(a["id"], a["level"]) for a in got], [("oxygen_low", "warning")])
        self.assertIn("OXY SẮP HẾT", got[0]["text"])
        self.assertEqual(got[0]["seconds"], math.ceil(OXY_LOW / HZ))

    def test_empty_is_danger(self):
        got = alerts.compute(gather_snap(oxygen_ticks=0), TUNING)
        self.assertEqual([(a["id"], a["level"]) for a in got], [("oxygen_low", "danger")])
        self.assertIn("HẾT OXY", got[0]["text"])

    def test_not_at_surface(self):
        self.assertEqual(ids(gather_snap(pos=[50, 0], oxygen_ticks=1)), [])

    def test_triggers_in_real_dive(self):
        sess = Session("gather", TUNING, {"fish": [], "nodes": [], "monsters": [], "player": {"pos": [20, 5]}}, 1)
        inp = InputPlayer([])
        first = None
        while not sess.done and first is None:
            sess.step(inp.advance(sess.tick))
            if "oxygen_low" in ids(sess.snapshot()):
                first = sess.snapshot()["player"]["oxygen_ticks"]
        self.assertEqual(first, OXY_LOW)


class MonsterNear(unittest.TestCase):
    def croc(self, gap, **kw):
        return {"id": "M1", "kind": "ca_sau", "pos": [50 + gap, MID], **kw}

    def test_detect_radius_boundary(self):
        got = alerts.compute(gather_snap([self.croc(SP["detect_radius"])]), TUNING)
        self.assertEqual([(a["id"], a["level"]) for a in got], [("monster_near", "danger")])
        self.assertEqual((got[0]["monster_ids"], got[0]["distance"]), (["M1"], SP["detect_radius"]))
        self.assertIn("CÁ SẤU GẦN", got[0]["text"])
        self.assertEqual(ids(gather_snap([self.croc(SP["detect_radius"] + 0.5)])), [])

    def test_chasing_far_away_still_warns(self):
        far = (SP["detect_radius"] + SP["exit_radius"]) / 2
        self.assertEqual(ids(gather_snap([self.croc(far, state="chase")])), ["monster_near"])

    def test_not_at_surface(self):
        snap = gather_snap([{"id": "M1", "kind": "ca_sau", "pos": [50, SP["depths"][0]]}], pos=[50, 0])
        self.assertEqual(ids(snap), [])

    def test_danger_listed_before_warning(self):
        snap = gather_snap([self.croc(1)], oxygen_ticks=OXY_LOW)
        self.assertEqual(ids(snap), ["monster_near", "oxygen_low"])


class CustomerAngry(unittest.TestCase):
    def snap(self, left, state="waiting"):
        return {"phase": "quan", "mode": "quan", "state": "playing",
                "customers": [{"id": "C1", "table_id": "T1", "state": state, "patience_ticks_left": left}]}

    def test_threshold_boundary(self):
        self.assertEqual(ids(self.snap(ANGRY + 1)), [])
        got = alerts.compute(self.snap(ANGRY), TUNING)
        self.assertEqual([(a["id"], a["level"]) for a in got], [("customer_angry", "warning")])
        self.assertIn("KHÁCH SẮP GIẬN", got[0]["text"])
        self.assertIn("T1", got[0]["text"])

    def test_eating_customer_is_not_angry(self):
        self.assertEqual(ids(self.snap(0, state="eating")), [])

    def test_triggers_in_real_shift(self):
        stock = {kind: 20 for kind in ("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo")}
        sess = Session("quan", TUNING, {}, 1, inventory=stock)  # có hàng thì khách mới đến
        inp = InputPlayer([])
        hit = None
        while not sess.done and hit is None:
            sess.step(inp.advance(sess.tick))
            snap = sess.snapshot()
            if "customer_angry" in ids(snap):
                hit = [c["patience_ticks_left"] for c in snap["customers"] if c["state"] == "waiting"]
        self.assertIsNotNone(hit, "ca quán không có khách nào chờ tới mốc sắp giận")
        self.assertEqual(min(hit), ANGRY)


class Scope(unittest.TestCase):
    def test_no_alerts_in_shop_menu_or_finished(self):
        self.assertEqual(alerts.compute({"phase": "shop", "state": "playing"}, TUNING), [])
        self.assertEqual(alerts.compute({**gather_snap(oxygen_ticks=0), "state": "finished"}, TUNING), [])

    def test_live_state_carries_alerts_but_headless_snapshot_does_not(self):
        sc = {"fish": [], "nodes": [], "monsters": [], "player": {"pos": [20, 5], "oxygen_ticks": 1}}
        game = LiveGame("gather", TUNING, sc, 1)
        st = json.loads(game.state_json())
        self.assertEqual([a["id"] for a in st["alerts"]], ["oxygen_low"])
        self.assertNotIn("alerts", Session("gather", TUNING, sc, 1).snapshot())


class HighContrast(unittest.TestCase):
    def test_page_has_toggle_and_alert_banner(self):
        with open(os.path.join(ROOT, "chonoi", "web", "index.html"), encoding="utf-8") as f:
            html = f.read()
        for marker in ('k === "h"', "toggleHC", "hc=1", "localStorage", "drawAlerts", "snap.alerts",
                       "LEVEL_ICON", 'strokeStyle = "#ffffff"'):
            self.assertIn(marker, html)


if __name__ == "__main__":
    unittest.main()
