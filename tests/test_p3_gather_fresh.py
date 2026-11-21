"""Test Phase 3, lát giỏ cá thể và độ tươi buổi sáng (B), Ticket-03 mục 1.

Manifest còn ở 1.1 trong lúc chuyển, nên:
- Phần in-process dựng tuning v1.2 trong bộ nhớ (thêm khối `freshness`) rồi chạy `GatherSim.step()` thật.
- Phần headless (`Headless`) chạy khi `game.contract.json` đã bật v1.2 (A bật khoảng 2:20); trước đó tự bỏ qua.
- `Hai phien ban` kiểm v1.1 (giỏ là chuỗi, không hao, không `spoiled`) vẫn nguyên.

Độ tươi tính bằng đơn vị nguyên: 240 đơn vị mỗi điểm, giỏ hao 2 đơn vị mỗi tick, ươn khi dưới 7200.

Chạy: PYTHONPATH=tests:. python3 -m unittest discover -s tests -p "test_p3_gather_fresh.py" -v
(PowerShell: `$env:PYTHONPATH = "tests;."` trước khi chạy.)
"""

import copy
import unittest

from chonoi import fresh
from chonoi.contract import FRESHNESS_V12, load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

MANIFEST = load_contract()["tuning"]
T11 = copy.deepcopy(MANIFEST)
T11.pop("freshness", None)
T12 = dict(copy.deepcopy(T11), freshness=dict(FRESHNESS_V12))
MANIFEST_V12 = "freshness" in MANIFEST
G = T12["gather"]
CAP = G["hold_capacity"]
UNITS = fresh.UNITS
DECAY_U = fresh.cfg(T12)["gather_decay_u"]  # 2 đơn vị mỗi tick = 0.5 điểm mỗi giây
SPOILED_U = fresh.cfg(T12)["spoiled_u"]     # 7200
INITIAL_U = fresh.cfg(T12)["initial_u"]     # 24000
SURF = [20, 0]
UNDER = [20, 5]


def make(scenario=None, tuning=T12, seed=1):
    base = {"random_fish": False, "nodes": [], "monsters": []}
    base.update(scenario or {})
    return GatherSim(tuning, base, Streams(seed), IdAllocator())


def inst(iid, kind="ca_linh", f=100):
    return {"id": iid, "kind": kind, "fresh": f}


def idle():
    return InputState((0.0, 0.0), {}, set())


def press(button):
    return InputState((0.0, 0.0), {button: True}, {button})


def run(sim, n):
    """n bước không bấm gì; trả [(tick sau bước, tên, data)]."""
    out = []
    for _ in range(n):
        evs = sim.step(idle())
        out += [(sim.phase_tick, name, data) for name, data in evs]
    return out


def spoiled_events(evs):
    return [(t, d["item_id"], d["kind"], d["location"]) for t, n, d in evs if n == "spoiled"]


def node(nid, x, kind="bong_sung"):
    return {"id": nid, "kind": kind, "pos": [x, 0]}


def fish(fid, x, d, kind="ca_linh"):
    return {"id": fid, "kind": kind, "pos": [x, d]}


class HaoTuoi(unittest.TestCase):
    def test_gio_hao_2_don_vi_moi_tick_la_0_5_diem_moi_giay(self):
        sim = make({"hold": [inst("I1")]})
        run(sim, 60)
        self.assertEqual(sim.hold[0]["u"], INITIAL_U - 60 * DECAY_U)
        self.assertAlmostEqual(fresh.public(sim.hold[0])["fresh"], 100 - 0.5, places=9)
        run(sim, 540)  # 10 giây
        self.assertAlmostEqual(fresh.public(sim.hold[0])["fresh"], 95.0, places=9)

    def test_hang_co_san_hao_tu_buoc_1(self):
        sim = make({"hold": [inst("I1")]})
        run(sim, 1)
        self.assertEqual(sim.hold[0]["u"], INITIAL_U - DECAY_U)

    def test_snapshot_hold_la_ca_the_public_theo_thu_tu_nhat(self):
        sim = make({"hold": [inst("I2", "ca_loc", 90), inst("I1", "ca_linh", 80)]})
        snap = sim.snapshot()["hold"]
        self.assertEqual(snap, [{"id": "I2", "kind": "ca_loc", "fresh": 90.0},
                                {"id": "I1", "kind": "ca_linh", "fresh": 80.0}])  # không sắp lại theo id
        self.assertEqual(sim.snapshot()["hold_count"], 2)

    def test_hao_ke_ca_hang_uon_va_kep_day_0(self):
        sim = make({"hold": [inst("I1", f=0.01)]})
        run(sim, 10)
        self.assertEqual(sim.hold[0]["u"], 0)
        self.assertEqual(sim.snapshot()["hold"][0]["fresh"], 0.0)


class Uon(unittest.TestCase):
    def test_fixture_ticket_03_fresh_30_uon_o_tick_1(self):
        sim = make({"hold": [inst("I1", "ca_linh", 30)]})
        evs = run(sim, 1)
        self.assertEqual(spoiled_events(evs), [(1, "I1", "ca_linh", "hold")])

    def test_uon_dung_tick_theo_so_nguyen(self):
        # fresh 30.01 -> u = 7202: tick 1 còn 7200 (chưa ươn), tick 2 còn 7198 (ươn)
        sim = make({"hold": [inst("I1", f=30.01)]})
        self.assertEqual(spoiled_events(run(sim, 1)), [])
        self.assertEqual(spoiled_events(run(sim, 1)), [(2, "I1", "ca_linh", "hold")])
        # fresh 31 -> u = 7440: cần 121 tick để xuống dưới 7200
        sim = make({"hold": [inst("I1", f=31)]})
        self.assertEqual(spoiled_events(run(sim, 120)), [])
        self.assertEqual([e[0] for e in spoiled_events(run(sim, 1))], [121])

    def test_chi_phat_mot_lan(self):
        sim = make({"hold": [inst("I1", f=30)]})
        self.assertEqual(len(spoiled_events(run(sim, 400))), 1)

    def test_da_uon_san_khong_phat(self):
        sim = make({"hold": [inst("I1", f=29.9)]})
        self.assertEqual(spoiled_events(run(sim, 50)), [])

    def test_nhieu_ca_the_cung_tick_phat_theo_id_so(self):
        sim = make({"hold": [inst("I10", "ca_loc", 30), inst("I2", "ca_linh", 30), inst("I3", "ca_linh", 80)]})
        evs = spoiled_events(run(sim, 1))
        self.assertEqual([e[1] for e in evs], ["I2", "I10"])

    def test_event_o_dau_buoc_truoc_cac_event_khac(self):
        sim = make({"hold": [inst("I1", f=30)], "player": {"pos": SURF}, "nodes": [node("N1", 20)]})
        evs = sim.step(press("interact"))
        self.assertEqual([n for n, _ in evs], ["spoiled", "gather"])

    def test_hang_uon_van_chiem_o_trong_gio(self):
        hold = [inst(f"I{i + 1}", "ca_loc", 10) for i in range(CAP)]  # toàn hàng ươn, giỏ đầy
        sim = make({"hold": hold, "player": {"pos": SURF}, "nodes": [node("N1", 20)]})
        evs = sim.step(press("interact"))
        full = [d for n, d in evs if n == "hold_full"]
        self.assertEqual(full, [{"action": "gather", "node_id": "N1", "required": G["node_yield"], "free": 0}])
        self.assertEqual(len(sim.hold), CAP)


class CaTheMoi(unittest.TestCase):
    def test_hai_tao_ca_the_id_noi_tiep_fresh_100_hao_tu_buoc_sau(self):
        sim = make({"hold": [inst("I5", "ca_loc", 90)], "player": {"pos": SURF}, "nodes": [node("N1", 20)]})
        sim.step(press("interact"))
        self.assertEqual([h["id"] for h in sim.hold], ["I5", "I6"])
        new = sim.hold[-1]
        self.assertEqual((new["kind"], new["u"]), ("bong_sung", INITIAL_U))  # chưa hao trong bước vừa hái
        run(sim, 1)
        self.assertEqual(new["u"], INITIAL_U - DECAY_U)

    def test_bat_ca_them_du_yield_ca_the_id_tang_theo_thu_tu_vao_gio(self):
        sim = make({"player": {"pos": UNDER}, "fish": [fish("F1", 20, 6, "ca_linh")]})
        sim.step(press("catch"))
        n = G["fish_yield"]["ca_linh"]
        self.assertEqual([h["id"] for h in sim.hold], [f"I{i + 1}" for i in range(n)])
        self.assertTrue(all(h["kind"] == "ca_linh" and h["u"] == INITIAL_U for h in sim.hold))

    def test_id_xuyen_hai_va_bat_theo_thu_tu_vao_gio(self):
        inp = [press("interact"), idle(), idle()]
        sim = make({"player": {"pos": SURF}, "nodes": [node("N1", 20)], "fish": [fish("F1", 20, 1, "ca_loc")]})
        sim.step(inp[0])
        self.assertEqual([h["id"] for h in sim.hold], ["I1"])
        sim.pos = [20.0, 5.0]
        sim.fish[0]["pos"] = [20.0, 6.0]
        sim.step(press("catch"))
        self.assertEqual([(h["id"], h["kind"]) for h in sim.hold], [("I1", "bong_sung"), ("I2", "ca_loc")])

    def test_ca_the_moi_va_ca_the_cu_hao_khac_nhau(self):
        sim = make({"hold": [inst("I1", f=50)], "player": {"pos": SURF}, "nodes": [node("N1", 20)]})
        sim.step(press("interact"))
        run(sim, 120)
        a, b = sim.hold
        self.assertAlmostEqual(fresh.public(a)["fresh"], 50 - 121 / 120, places=9)
        self.assertAlmostEqual(fresh.public(b)["fresh"], 100 - 120 / 120, places=9)

    def test_thieu_cho_bat_ca_khong_tao_ca_the(self):
        need = G["fish_yield"]["ca_linh"]
        hold = [inst(f"I{i + 1}", "ca_loc") for i in range(CAP - (need - 1))]
        sim = make({"hold": hold, "player": {"pos": UNDER}, "fish": [fish("F1", 20, 6)]})
        evs = sim.step(press("catch"))
        self.assertEqual([n for n, _ in evs], ["hold_full"])
        self.assertEqual(len(sim.hold), len(hold))
        self.assertEqual(sim.ids.new("I"), f"I{len(hold) + 1}")  # không cấp id thừa cho lần bắt bị từ chối


class XuatRa(unittest.TestCase):
    def test_cap_ben_kho_la_mang_ca_the_sap_theo_id_voi_fresh(self):
        sim = make({"hold": [inst("I10", "ca_loc", 70), inst("I2", "ca_linh", 90)]})
        evs = sim.step(press("interact"))  # đang ở bến [2, 0]
        end = [d for n, d in evs if n == "gather_end"][0]
        self.assertEqual(end["reason"], "docked")
        self.assertEqual([i["id"] for i in end["inventory"]["items"]], ["I2", "I10"])
        self.assertEqual(sim.inventory_items(), end["inventory"]["items"])
        got = {i["id"]: i["fresh"] for i in end["inventory"]["items"]}
        self.assertAlmostEqual(got["I2"], 90 - 1 / 120, places=9)  # đã hao đúng một bước trước khi cập bến
        self.assertAlmostEqual(got["I10"], 70 - 1 / 120, places=9)

    def test_ngat_khi_ngat_lost_la_ca_the_theo_lifo_va_kho_rong(self):
        hold = [inst("I1", "ca_loc", 60), inst("I2", "ca_linh", 70)]
        sim = make({"hold": hold, "player": {"pos": [50, 10], "hp": 1, "oxygen_ticks": 0,
                                             "zero_oxy_ticks": G["choke_interval_ticks"] - 1}})
        evs = sim.step(idle())
        faint = [d for n, d in evs if n == "faint"][0]
        self.assertEqual([i["id"] for i in faint["lost"]], ["I2", "I1"])
        self.assertTrue(all(set(i) == {"id", "kind", "fresh"} for i in faint["lost"]))
        self.assertEqual(sim.inventory_items(), [])

    def test_tat_dinh_cung_seed_cung_ket_qua(self):
        def go():
            sim = make({"hold": [inst("I1", f=31)], "random_fish": True}, seed=5)
            evs = run(sim, 300)
            return evs, sim.snapshot()
        self.assertEqual(go(), go())


class HaiPhienBan(unittest.TestCase):
    def test_v11_gio_la_chuoi_khong_hao_khong_spoiled(self):
        sim = make({"hold": ["ca_loc"], "player": {"pos": SURF}, "nodes": [node("N1", 20)]}, tuning=T11)
        self.assertFalse(sim.fresh_on)
        self.assertEqual(spoiled_events(run(sim, 500)), [])
        sim.step(press("interact"))
        self.assertEqual(sim.hold, ["ca_loc", "bong_sung"])
        self.assertEqual(sim.inventory_items(), {"bong_sung": 1, "ca_loc": 1})

    def test_v12_bat_bang_khoi_freshness(self):
        self.assertTrue(make().fresh_on)


@unittest.skipUnless(MANIFEST_V12, "chờ A bật contract_version 1.2 (manifest chưa có khối freshness)")
class Headless(unittest.TestCase):
    def _gather(self, block, ticks, inputs=None, inv_out=None, every=1):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"random_fish": False, "monsters": [], **block}})
            args = ["--mode", "gather", "--seed", "1", "--ticks", str(ticks), "--scenario", sc,
                    "--snapshot-every", str(every), "--out", w.path("o.jsonl")]
            if inputs is not None:
                args += ["--inputs", write_json(w.path("in.json"), inputs)]
            if inv_out:
                args += ["--inventory-out", w.path("inv.json")]
            code, err = run_headless(*args)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            inv = None
            if inv_out:
                import json
                with open(w.path("inv.json"), encoding="utf-8") as f:
                    inv = json.load(f)
            return rows, inv

    def test_fixture_ticket_03_spoiled_o_tick_1(self):
        rows, _ = self._gather({"hold": [inst("I1", "ca_linh", 30)]}, 1)
        ev = events(rows, "spoiled")
        self.assertEqual([(e["tick"], e["data"]) for e in ev],
                         [(1, {"item_id": "I1", "kind": "ca_linh", "location": "hold"})])

    def test_hao_0_5_moi_giay_trong_snapshot(self):
        rows, _ = self._gather({"hold": [inst("I1", "ca_linh", 100)]}, 120)
        hold = snapshots(rows)[-1]["hold"]
        self.assertEqual([h["id"] for h in hold], ["I1"])
        self.assertAlmostEqual(hold[0]["fresh"], 99.0, places=2)

    def test_cap_ben_ghi_kho_ca_the_va_quan_doc_dung_id_kind_fresh(self):
        rows, inv = self._gather({"hold": [inst("I1", "ca_linh", 100)]}, 1,
                                 inputs=frames({"tick": 0, "interact": True}), inv_out=True)
        want = 100 - 1 / 120  # hao đúng một bước trước khi cập bến
        self.assertEqual([i["id"] for i in inv["items"]], ["I1"])
        self.assertAlmostEqual(inv["items"][0]["fresh"], want, places=9)
        with Workdir() as w:
            p = write_json(w.path("inv.json"), inv)
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", p,
                                     "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)
            stock = snapshots(read_jsonl(w.path("q.jsonl")))[0]["stock"]
            self.assertEqual([(i["id"], i["kind"]) for i in stock], [("I1", "ca_linh")])
            self.assertAlmostEqual(stock[0]["fresh"], want, delta=0.001)  # JSONL làm tròn 3 chữ số, file kho thì không


if __name__ == "__main__":
    unittest.main()
