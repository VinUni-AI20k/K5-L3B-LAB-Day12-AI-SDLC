"""Test Phase 2, lát 1 (B): 8 đàn đầu ca, cá bơi, cá sinh, cá kèo, nút kèo nèo (Ticket-02 mục 1.1).

Gồm test in-process (dựng GatherSim, chạy `step()` thật) và test headless hộp đen. Số liệu lấy từ
game.contract.json (v1.1). Luật cá của B nằm trong `chonoi/sim/gather.py`.

Chạy: PYTHONPATH=tests:. python3 -m unittest discover -s tests -p "test_p2_fish.py" -v
(PowerShell: `$env:PYTHONPATH = "tests;."` trước khi chạy.)
"""

import copy
import math
import random
import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

TUNING = load_contract()["tuning"]
G = TUNING["gather"]
SPAWN = G["fish_spawn_ticks"]
TURN = G["fish_turn_ticks"]
STEP = G["fish_speed"] / 60


def make_sim(scenario=None, seed=1, tuning=None):
    return GatherSim(tuning or TUNING, scenario or {}, Streams(seed), IdAllocator())


def idle():
    return InputState((0.0, 0.0), {}, set())


def pressed(button):
    return InputState((0.0, 0.0), {button: True}, {button})


def run(sim, n):
    """n bước `step()` thật không bấm gì; trả toàn bộ event theo thứ tự (tên, data, tick sau bước)."""
    out = []
    for k in range(n):
        out += [(name, data, sim.phase_tick) for name, data in sim.step(idle())]
    return out


def grid(kind):
    return [[float(x), float(d)] for x in G["fish_spawn_x"] for d in G["fish_spawn_depths"][kind]]


def fish_at(fid, kind, pos, heading=0.0, age=0):
    return {"id": fid, "kind": kind, "pos": pos, "heading_deg": heading, "age_ticks": age}


def swim_once(kind, pos, heading, age=0, seed=1):
    sim = make_sim({"fish": [fish_at("F1", kind, pos, heading, age)]}, seed=seed)
    sim._fish_swim()
    return sim.fish[0]


class DauCa(unittest.TestCase):
    def test_8_dan_o_8_diem_sinh_chuan_khac_nhau(self):
        sim = make_sim()
        self.assertEqual([f["id"] for f in sim.fish], [f"F{i}" for i in range(1, G["fish_initial"] + 1)])
        self.assertEqual(len({tuple(f["pos"]) for f in sim.fish}), G["fish_initial"])
        for f in sim.fish:
            self.assertIn(f["pos"], grid(f["kind"]), f)
            self.assertEqual(f["age_ticks"], 0)
            self.assertTrue(0 <= f["heading_deg"] < 360)
        for i, a in enumerate(sim.fish):
            for b in sim.fish[i + 1:]:
                self.assertGreater(math.dist(a["pos"], b["pos"]), G["fish_spawn_clearance"])

    def test_cung_seed_cung_dan_khac_seed_khac(self):
        key = lambda s: [(f["id"], f["kind"], f["pos"], f["heading_deg"]) for f in s.fish]
        self.assertEqual(key(make_sim(seed=7)), key(make_sim(seed=7)))
        self.assertNotEqual(key(make_sim(seed=7)), key(make_sim(seed=8)))

    def test_random_fish_false_khong_ca_khong_boi_khong_sinh(self):
        sim = make_sim({"random_fish": False})
        self.assertEqual(sim.fish, [])
        self.assertEqual(run(sim, SPAWN + 5), [])
        self.assertEqual(sim.fish, [])

    def test_random_fish_false_ca_fixture_dung_yen(self):
        sim = make_sim({"random_fish": False, "fish": [fish_at("F1", "ca_linh", [20, 6], heading=45)]})
        run(sim, 200)
        self.assertEqual((sim.fish[0]["pos"], sim.fish[0]["age_ticks"]), ([20.0, 6.0], 0))

    def test_khai_fish_thay_dan_ban_dau_van_boi_va_sinh(self):
        sim = make_sim({"fish": [fish_at("F1", "ca_linh", [20, 6])]})
        self.assertEqual([f["id"] for f in sim.fish], ["F1"])
        ev = run(sim, SPAWN)
        self.assertNotEqual(sim.fish[0]["pos"], [20.0, 6.0])
        spawned = [e for e in ev if e[0] == "fish_spawned"]
        self.assertEqual([(e[1]["id"], e[2]) for e in spawned], [("F2", SPAWN)])


class CaBoi(unittest.TestCase):
    def test_di_dung_fish_speed(self):
        sim = make_sim({"fish": [fish_at("F1", "ca_loc", [50, 14], heading=0)]})
        for _ in range(60):
            sim._fish_swim()
        f = sim.fish[0]
        self.assertAlmostEqual(f["pos"][0], 50 + G["fish_speed"], places=6)
        self.assertAlmostEqual(f["pos"][1], 14, places=6)
        self.assertEqual(f["age_ticks"], 60)

    def test_di_theo_huong_xuong_la_d_duong(self):
        f = swim_once("ca_loc", [50, 14], heading=90)
        self.assertAlmostEqual(f["pos"][1], 14 + STEP, places=9)
        self.assertAlmostEqual(f["pos"][0], 50, places=9)

    def test_phan_xa_o_mep_x(self):
        hi = G["fish_x"][1]
        f = swim_once("ca_loc", [hi - STEP / 2, 14], heading=0)
        self.assertAlmostEqual(f["pos"][0], hi - STEP / 2, places=9)  # đi STEP/2 tới mép rồi lùi STEP/2
        self.assertAlmostEqual(f["heading_deg"], 180, places=6)
        lo = G["fish_x"][0]
        f = swim_once("ca_loc", [lo + STEP / 4, 14], heading=180)
        self.assertAlmostEqual(f["pos"][0], lo + 3 * STEP / 4, places=9)
        self.assertAlmostEqual(f["heading_deg"], 0, places=6)

    def test_phan_xa_o_dai_do_sau_cua_loai(self):
        lo, hi = G["fish_depths"]["ca_keo"]
        f = swim_once("ca_keo", [50, hi - STEP / 4], heading=90)
        self.assertAlmostEqual(f["pos"][1], hi - 3 * STEP / 4, places=9)
        self.assertAlmostEqual(f["heading_deg"], 270, places=6)
        f = swim_once("ca_keo", [50, lo + STEP / 4], heading=270)
        self.assertAlmostEqual(f["pos"][1], lo + 3 * STEP / 4, places=9)
        self.assertAlmostEqual(f["heading_deg"], 90, places=6)

    def test_cham_goc_dao_ca_hai_thanh_phan(self):
        hi_x, lo_d = G["fish_x"][1], G["fish_depths"]["ca_linh"][0]
        f = swim_once("ca_linh", [hi_x - 0.001, lo_d + 0.001], heading=315)  # sang phải và lên
        self.assertAlmostEqual(f["heading_deg"], 135, places=6)
        self.assertLessEqual(f["pos"][0], hi_x)
        self.assertGreaterEqual(f["pos"][1], lo_d)

    def test_di_toi_dung_mep_chua_vuot_thi_chua_dao(self):
        hi = G["fish_x"][1]
        f = swim_once("ca_loc", [hi - STEP, 14], heading=0)
        self.assertAlmostEqual(f["pos"][0], hi, places=9)
        self.assertAlmostEqual(f["heading_deg"], 0, places=9)

    def test_khong_ra_khoi_dai_x_va_do_sau_trong_ca_dai(self):
        sim = make_sim(seed=3)
        xlo, xhi = G["fish_x"]
        for _ in range(5):
            run(sim, 600)
            for f in sim.fish:
                dlo, dhi = G["fish_depths"][f["kind"]]
                self.assertTrue(xlo <= f["pos"][0] <= xhi, f)
                self.assertTrue(dlo <= f["pos"][1] <= dhi, f)

    def test_doi_huong_dung_buoc_boi_thu_120_truoc_khi_di(self):
        sim = make_sim({"fish": [fish_at("F1", "ca_loc", [50, 14], heading=0, age=TURN - 2)]}, seed=5)
        sim._fish_swim()  # bước bơi thứ TURN-1: chưa đổi
        self.assertEqual(sim.fish[0]["heading_deg"], 0)
        x0 = sim.fish[0]["pos"][0]
        sim._fish_swim()  # bước bơi thứ TURN: đổi hướng rồi mới đi
        want = random.Random("5:fish_turn").uniform(0.0, 360.0)
        f = sim.fish[0]
        self.assertEqual(f["age_ticks"], TURN)
        self.assertAlmostEqual(f["heading_deg"], want, places=9)
        self.assertAlmostEqual(f["pos"][0], x0 + math.cos(math.radians(want)) * STEP, places=9)
        sim._fish_swim()  # bước TURN+1: không đổi nữa
        self.assertAlmostEqual(sim.fish[0]["heading_deg"], want, places=9)

    def test_moi_luong_rieng_cung_seed_cung_quy_dao(self):
        a, b = make_sim(seed=11), make_sim(seed=11)
        run(a, 900)
        run(b, 900)
        key = lambda s: [(f["id"], f["pos"], f["heading_deg"], f["age_ticks"]) for f in s.fish]
        self.assertEqual(key(a), key(b))


class CaSinh(unittest.TestCase):
    def test_sinh_dung_tick_360_khi_con_cho_roi_moi_360(self):
        sim = make_sim(seed=2)
        ev = run(sim, 2 * SPAWN)
        spawned = [e for e in ev if e[0] == "fish_spawned"]
        self.assertEqual([e[2] for e in spawned], [SPAWN, 2 * SPAWN])
        self.assertEqual([e[1]["id"] for e in spawned], ["F9", "F10"])
        self.assertEqual(len(sim.fish), G["fish_initial"] + 2)
        for _, data, _ in spawned:
            self.assertEqual(set(data), {"id", "kind", "pos"})
            self.assertIn(data["pos"], grid(data["kind"]))

    def test_ca_moi_tuoi_0_va_boi_tu_buoc_sau(self):
        sim = make_sim(seed=2)
        run(sim, SPAWN)
        new = [f for f in sim.fish if f["id"] == "F9"][0]
        self.assertEqual(new["age_ticks"], 0)
        spawn_pos = list(new["pos"])
        run(sim, 1)
        new = [f for f in sim.fish if f["id"] == "F9"][0]
        self.assertEqual(new["age_ticks"], 1)
        self.assertNotEqual(new["pos"], spawn_pos)

    def test_diem_sinh_cach_moi_dan_dang_song_hon_clearance(self):
        sim = make_sim(seed=6)
        run(sim, SPAWN - 1)
        before = [list(f["pos"]) for f in sim.fish]
        sim.phase_tick = SPAWN  # step kế sẽ là 361; ép lịch sinh qua hàm trực tiếp, không cho cá bơi lệch
        ev = []
        sim._spawn_fish(ev)
        self.assertEqual(len(ev), 1)
        pos = ev[0][1]["pos"]
        self.assertTrue(all(math.dist(pos, p) > G["fish_spawn_clearance"] for p in before))

    def test_khong_sinh_qua_fish_max(self):
        sim = make_sim(seed=4)
        ev = run(sim, SPAWN * 12)
        self.assertEqual(len(sim.fish), G["fish_max"])
        self.assertEqual(len([e for e in ev if e[0] == "fish_spawned"]), G["fish_max"] - G["fish_initial"])

    def _occupy(self, kinds):
        pts = [tuple(p) for k in kinds for p in grid(k)]
        return [fish_at(f"F{i + 1}", "ca_loc", list(p)) for i, p in enumerate(sorted(set(pts)))]

    def test_chuan_hoa_lai_trong_so_khi_loai_het_diem(self):
        """Chiếm hết điểm của cá linh và cá lóc: chỉ còn cá kèo được sinh."""
        t = copy.deepcopy(TUNING)
        t["gather"]["fish_max"] = 99
        for seed in range(1, 8):
            sim = make_sim({"fish": self._occupy(("ca_linh", "ca_loc"))}, seed=seed, tuning=t)
            sim.phase_tick = SPAWN
            ev = []
            sim._spawn_fish(ev)
            self.assertEqual(ev[0][1]["kind"], "ca_keo", seed)

    def test_het_diem_hop_le_bo_luot(self):
        t = copy.deepcopy(TUNING)
        t["gather"]["fish_max"] = 99
        fixture = self._occupy(tuple(G["fish_spawn_depths"]))
        sim = make_sim({"fish": fixture}, tuning=t)
        sim.phase_tick = SPAWN
        ev = []
        sim._spawn_fish(ev)
        self.assertEqual(ev, [])
        self.assertEqual(len(sim.fish), len(fixture))

    def test_khong_sinh_o_buoc_cuoi_het_gio(self):
        """Hết giờ ở đúng tick 360: gather_end, không bơi, không sinh thêm."""
        sim = make_sim({"time_left_ticks": SPAWN}, seed=2)
        ev = run(sim, SPAWN)
        self.assertEqual([e[0] for e in ev][-1], "gather_end")
        self.assertNotIn("fish_spawned", [e[0] for e in ev])
        self.assertEqual(len(sim.fish), G["fish_initial"])


class ThuTuStep(unittest.TestCase):
    def test_bat_ca_theo_vi_tri_truoc_khi_boi(self):
        """Cá ở đúng mép tầm bắt (2.0) nhưng đang bơi ra xa: vẫn bắt được vì bắt xét TRƯỚC khi cá bơi."""
        sim = make_sim({"player": {"pos": [20, 6]}, "nodes": [],
                        "fish": [fish_at("F1", "ca_loc", [20 + G["catch_radius"], 6], heading=0)]})
        ev = sim.step(pressed("catch"))
        self.assertEqual([n for n, _ in ev], ["fish_caught"])
        self.assertEqual(sim.hold, ["ca_loc"])

    def test_ca_boi_ngay_buoc_dau_neu_khong_bi_bat(self):
        sim = make_sim({"fish": [fish_at("F1", "ca_loc", [50, 14], heading=0)]})
        sim.step(idle())
        self.assertAlmostEqual(sim.fish[0]["pos"][0], 50 + STEP, places=9)
        self.assertEqual(sim.fish[0]["age_ticks"], 1)


class LoaiMoi(unittest.TestCase):
    def test_bat_ca_keo_cho_2(self):
        lo = G["fish_depths"]["ca_keo"][0]
        sim = make_sim({"random_fish": False, "player": {"pos": [50, lo + 1]},
                        "fish": [fish_at("F1", "ca_keo", [50, lo + 2])]})
        ev = sim.step(pressed("catch"))
        self.assertEqual([d for n, d in ev if n == "fish_caught"],
                         [{"fish_id": "F1", "kind": "ca_keo", "yield": G["fish_yield"]["ca_keo"]}])
        self.assertEqual(sim.hold, ["ca_keo"] * G["fish_yield"]["ca_keo"])

    def test_hai_nut_keo_neo_n5_va_n6(self):
        for nid in ("N5", "N6"):
            node = [n for n in G["nodes"] if n["id"] == nid][0]
            sim = make_sim({"random_fish": False, "player": {"pos": list(node["pos"])}})
            ev = sim.step(pressed("interact"))
            self.assertEqual([d for n, d in ev if n == "gather"],
                             [{"node_id": nid, "kind": "keo_neo", "amount": G["node_yield"]}], nid)
            self.assertEqual(sim.hold, ["keo_neo"] * G["node_yield"])


class Headless(unittest.TestCase):
    def _run(self, ticks, seed=1, block=None, every=None):
        with Workdir() as w:
            args = ["--mode", "gather", "--seed", str(seed), "--ticks", str(ticks), "--out", w.path("o.jsonl")]
            if block is not None:
                args += ["--scenario", write_json(w.path("sc.json"), {"gather": block})]
            if every:
                args += ["--snapshot-every", str(every)]
            code, err = run_headless(*args)
            self.assertEqual(code, 0, err)
            with open(w.path("o.jsonl"), "rb") as f:
                raw = f.read()
            return read_jsonl(w.path("o.jsonl")), raw

    def test_tick_0_co_8_dan_voi_age_0(self):
        rows, _ = self._run(0)
        fish = snapshots(rows)[0]["fish"]
        self.assertEqual(len(fish), G["fish_initial"])
        self.assertTrue(all(f["age_ticks"] == 0 for f in fish))

    def test_ca_boi_va_sinh_o_tick_360(self):
        rows, _ = self._run(SPAWN + 1, every=1)
        snaps = {s["tick"]: s for s in snapshots(rows)}
        self.assertNotEqual([f["pos"] for f in snaps[0]["fish"]], [f["pos"] for f in snaps[1]["fish"]])
        sp = events(rows, "fish_spawned")
        self.assertEqual([e["tick"] for e in sp], [SPAWN])
        self.assertEqual(len(snaps[SPAWN - 1]["fish"]), G["fish_initial"])
        self.assertEqual(len(snaps[SPAWN]["fish"]), G["fish_initial"] + 1)
        self.assertEqual(snaps[SPAWN + 1]["fish"][-1]["age_ticks"], 1)

    def test_random_fish_false_khong_sinh(self):
        rows, _ = self._run(SPAWN + 5, block={"random_fish": False})
        self.assertEqual(events(rows, "fish_spawned"), [])
        self.assertEqual(snapshots(rows)[-1]["fish"], [])

    def test_tat_dinh_tung_byte(self):
        self.assertEqual(self._run(900, seed=9)[1], self._run(900, seed=9)[1])

    def test_cung_seed_hai_buoc_snapshot_khac_nhau_cho_ket_qua_cuoi_giong_nhau(self):
        a = snapshots(self._run(720, seed=4, every=1)[0])[-1]["fish"]
        b = snapshots(self._run(720, seed=4, every=60)[0])[-1]["fish"]
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
