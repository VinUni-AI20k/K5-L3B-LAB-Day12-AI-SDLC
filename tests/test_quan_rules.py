"""Test hộp đen cho luật `quan` Phase 1 (ticket 07, phần chờ ticket 01).

Bốn test này dựng trạng thái giữa chừng bằng `quan.customers` / `quan.hand` — những khóa
chưa được `scenario.py` hỗ trợ ở v1.0. Vì vậy chúng đang `skip`; khi ticket 01 merge thì
BỎ `@unittest.skip` (không phải viết lại gì khác).

Nguồn: PRD-0 §E/§F + docs/plan/phase-1-conformance.md §6.
"""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def tuning():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]


class Base(unittest.TestCase):
    def run_quan(self, w, scenario=None, inputs=None, ticks=30, every="1", name="q", inventory=None):
        args = ["--mode", "quan", "--seed", "1", "--ticks", str(ticks),
                "--snapshot-every", every, "--out", w.path(name + ".jsonl")]
        if scenario is not None:
            args += ["--scenario", write_json(w.path("sc.json"), scenario)]
        if inputs is not None:
            args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
        if inventory is not None:
            args += ["--inventory", inventory]
        code, err = run_headless(*args)
        self.assertEqual(code, 0, err)
        return read_jsonl(w.path(name + ".jsonl"))

    def snaps(self, rows):
        return {r["tick"]: r for r in snapshots(rows)}


class Customers(Base):
    def test_khach_den_tick_120_va_giu_cho(self):
        """Có kho: khách đầu đến ở tick 120, ngồi bàn trống id nhỏ nhất, giữ đúng công thức."""
        sc = {"quan": {"stock": {"ca_loc": 1, "bong_sung": 2}}}
        with Workdir() as w:
            rows = self.run_quan(w, sc, ticks=200, every="1")
            arrived = events(rows, "customer_arrived")
            self.assertEqual([e["tick"] for e in arrived], [120], [e["tick"] for e in events(rows)])
            data = arrived[0]["data"]
            self.assertEqual(data["table_id"], "T1")
            snap = self.snaps(rows)[121]
            guest = [c for c in snap["customers"] if c["id"] == data["order_id"]][0]
            self.assertEqual(guest["order_status"], "reserved")
            self.assertEqual(guest["reserved"], tuning()["menu"][data["dish_id"]]["recipe"])
            # giữ chỗ không làm đổi tồn vật lý (stock đã bao gồm phần đang giữ)
            self.assertEqual(snap["stock"], {"ca_loc": 1, "bong_sung": 2})

    def test_het_kho_thi_no_dish(self):
        """Có bàn trống nhưng không món nào đủ nguyên liệu: phát no_dish, không tạo khách."""
        with Workdir() as w:
            rows = self.run_quan(w, ticks=200, every="1")
            self.assertEqual(events(rows, "customer_arrived"), [])
            self.assertEqual([e["tick"] for e in events(rows, "no_dish")], [120])

    def test_het_kien_nhan_thi_roi_va_mat_uy_tin(self):
        """Khách chờ với kiên nhẫn 60 tick: rời ở tick 60, uy tín 3.0 → 2.5."""
        sc = {"quan": {"stock": {"ca_loc": 1}, "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                      "patience_ticks_left": 60, "order_status": "reserved",
                                      "reserved": {"ca_loc": 1}}]}}
        with Workdir() as w:
            rows = self.run_quan(w, sc, ticks=70)
            left = events(rows, "customer_left")
            self.assertEqual(len(left), 1, [(e["name"], e["tick"]) for e in events(rows)])
            self.assertEqual((left[0]["tick"], left[0]["data"]["reason"]), (60, "patience"))
            self.assertAlmostEqual(left[0]["data"]["reputation"], 2.5, places=2)
            self.assertEqual(self.snaps(rows)[70]["customers"], [])



class Service(Base):
    def test_nau_dung_don_va_chin_sau_cook_s(self):
        """Đứng cạnh bếp, có đơn reserved: interact → cook_started (tiêu đúng nguyên liệu), 6 s sau dish_ready."""
        sc = {"quan": {"player": {"pos": [2, 8]},
                       "stock": {"ca_loc": 2},
                       "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                      "order_status": "reserved", "reserved": {"ca_loc": 1}}]}}
        with Workdir() as w:
            rows = self.run_quan(w, sc, [{"tick": 0, "interact": True}], ticks=400, every="30")
            started = events(rows, "cook_started")
            self.assertEqual(len(started), 1, [(e["name"], e["data"]) for e in events(rows)])
            data = started[0]["data"]
            self.assertEqual(data["dish_id"], "ca_loc_nuong_trui")
            self.assertEqual(data["items"], ["ca_loc"])
            self.assertEqual(data["base_price"], 60)
            # Bếp bắt đầu ở tick sự kiện cook_started, chín sau cook_s × 60 tick (cùng quy ước bước k → k+1)
            self.assertEqual([e["tick"] for e in events(rows, "dish_ready")],
                             [started[0]["tick"] + 360])
            snap = self.snaps(rows)[400]
            self.assertEqual(snap["stock"], {"ca_loc": 1})  # đã tiêu 1 khi bắt đầu nấu
            self.assertEqual(snap["stoves"][0]["state"], "ready")

    def test_phuc_vu_dung_don_thi_tra_tien_va_boa(self):
        """Cầm đúng món, đứng cạnh bàn: served → sau 10 s paid = giá + boa 20%."""
        hand = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}
        sc = {"quan": {"player": {"pos": [9, 2]}, "hand": hand,
                       "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                      "order_status": "assigned", "reserved": {},
                                      "patience_ticks_left": 3600}]}}
        with Workdir() as w:
            rows = self.run_quan(w, sc, [{"tick": 0, "interact": True}], ticks=700, every="100")
            served = events(rows, "served")
            self.assertEqual(len(served), 1, [(e["name"], e["data"]) for e in events(rows)])
            self.assertEqual(served[0]["data"]["tip"], 12)  # floor(60 × 0.2)
            paid = events(rows, "paid")
            self.assertEqual(len(paid), 1)
            self.assertEqual(paid[0]["data"]["amount"], 72)
            self.assertEqual(paid[0]["data"]["reason"], "finished_eating")
            self.assertAlmostEqual(self.snaps(rows)[700]["reputation"], 3.2, places=2)

    def test_dong_ca_tra_tien_khach_cho_roi_va_mot_quan_end(self):
        """Hết ca: khách đang ăn trả ngay; khách còn chờ rời 'closing' không trừ uy tín; đúng MỘT quan_end."""
        eating = {"quan": {"time_left_ticks": 5,
                           "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                           "state": "eating", "order_status": "served", "eat_ticks_left": 200,
                                           "base_price": 60, "tip": 12, "reserved": {}}]}}
        with Workdir() as w:
            rows = self.run_quan(w, eating, ticks=20, every="1")
            self.assertEqual([e["tick"] for e in events(rows, "quan_end")], [5],
                             [(e["tick"], e["name"]) for e in events(rows)])
            paid = events(rows, "paid")
            self.assertEqual(len(paid), 1)
            self.assertEqual((paid[0]["data"]["reason"], paid[0]["data"]["amount"]), ("closing", 72))
            self.assertAlmostEqual(self.snaps(rows)[max(self.snaps(rows))]["reputation"], 3.2, places=2)

        waiting = {"quan": {"time_left_ticks": 5,
                            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                            "order_status": "unfulfillable", "reserved": {},
                                            "patience_ticks_left": 3000}]}}
        with Workdir() as w:
            rows = self.run_quan(w, waiting, ticks=20, every="1", name="w")
            left = events(rows, "customer_left")
            self.assertEqual([(e["data"]["reason"], e["tick"]) for e in left], [("closing", 5)])
            self.assertAlmostEqual(self.snaps(rows)[max(self.snaps(rows))]["reputation"], 3.0, places=2)
            self.assertEqual(len(events(rows, "quan_end")), 1)


if __name__ == "__main__":
    unittest.main()
