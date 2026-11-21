"""Local P2-05 preview of the proposed web interface, with scripted scenes."""
import argparse
import json
import math
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from time import monotonic

ROOT = Path(__file__).resolve().parents[3]
TUNING = json.loads((ROOT / "game.contract.json").read_text(encoding="utf-8"))["tuning"]
DISHES = [
    "ca_loc_nuong_trui", "goi_bong_sung", "lau_ca_linh_dien_dien",
    "canh_chua_ca_loc_bong_dien_dien", "ca_keo_nuong_muoi_ot", "lau_mam_mien_tay",
]
ITEMS = ["ca_linh", "ca_loc", "ca_keo", "bong_sung", "bong_dien_dien", "keo_neo"]
STOCK = dict(zip(ITEMS, [6, 3, 3, 4, 2, 2]))
OPTIONS = [
    {"id": key, "label": label, "level": level, "price": price}
    for key, label, level, price in [
        ("oxygen_1", "Bình oxy", 1, 200), ("oxygen_2", "Bình oxy", 2, 400),
        ("hp_1", "Máu", 1, 250), ("hp_2", "Máu", 2, 500),
    ]
]


class Preview:
    def __init__(self, days, faint):
        self.days, self.faint = days, faint
        self.set_screen("menu")
        self.day = 1
        self.upgrades = {"oxygen": 0, "hp": 0}
        self.last_active_oxygen = 0
        self.money = 300

    def set_screen(self, screen):
        self.screen, self.paused, self.elapsed = screen, False, 0
        self.started = monotonic()
        self.interact = False
        self.message = ""

    def tick(self):
        return int((self.elapsed + (0 if self.paused else monotonic() - self.started)) * 60)

    def action(self, action, data):
        if action == "start" and self.screen == "menu":
            self.__init__(self.days, self.faint)
            self.set_screen("day_intro")
        elif action == "menu":
            self.set_screen("menu")
        elif action == "pause" and self.screen in ("gather", "quan", "shop") and not self.paused:
            self.elapsed += monotonic() - self.started
            self.paused = True
        elif action == "resume" and self.paused:
            self.paused, self.started = False, monotonic()
        elif action == "continue" and self.screen in ("day_intro", "evening_intro", "day_result"):
            self.set_screen({"day_intro": "gather", "evening_intro": "quan", "day_result": "shop"}[self.screen])
        elif action == "buy" and self.screen == "shop" and not self.paused:
            # Scripted success for one purchase; other attempts exercise feedback.
            if data.get("upgrade_id") == "oxygen_1" and not self.upgrades["oxygen"]:
                self.upgrades["oxygen"] = 1
                self.money -= 200
                self.message = "Đã mua bình oxy cấp 1. Có hiệu lực ngày kế tiếp."
            else:
                self.message = "Mua thất bại: nâng cấp này chưa khả dụng trong kịch bản."
        elif action == "shop_done" and self.screen == "shop" and not self.paused:
            if self.day == self.days:
                self.set_screen("summary")
            else:
                self.day += 1
                self.last_active_oxygen = self.upgrades["oxygen"]
                self.set_screen("day_intro")
        else:
            return False
        return True

    def keys(self, data):
        pressed = data.get("interact") is True
        if pressed and not self.interact and not self.paused:
            if self.screen == "gather":
                self.set_screen("evening_intro")
            elif self.screen == "quan":
                self.set_screen("day_result")
        self.interact = pressed

    def expire_shop(self):
        if self.screen == "shop" and not self.paused and self.tick() >= 600:
            self.action("shop_done", {})

    def snapshot(self):
        self.expire_shop()
        tick = self.tick()
        inventory = {} if self.faint else STOCK
        served = 0 if self.faint else 2
        covered_days = self.days if self.screen == "summary" else 1
        state = dict(mode="day", screen=self.screen, day=self.day, days=self.days, fixture=True,
                     paused=self.paused, can_pause=self.screen in ("gather", "quan", "shop"), tick_hz=60,
                     menu=[{"dish_id": dish, "servings": 1} for dish in DISHES],
                     needed=STOCK, inventory=inventory, cookable=[] if self.faint else DISHES,
                     gather_reason="fainted" if self.faint else "docked",
                     result=dict(served=served*covered_days, left=2*covered_days,
                                 earned=110*covered_days if served else 0, tips=10*covered_days if served else 0,
                                 money=self.money, reputation=3.5 if served else 3),
                     shop=dict(money=self.money, time_left_ticks=max(0, 600-tick),
                               upgrades=self.upgrades, options=OPTIONS, message=self.message), events=[])
        if self.screen == "gather":
            oxygen = 2700 if self.last_active_oxygen else 1800
            fish = [{"id": f"F{i+1}", "kind": ITEMS[i%3], "heading_deg": 0,
                     "pos": [8+7*i+.7*math.sin(tick/48+i), 6+6*(i%3)]} for i in range(12)]
            nodes = [{"id": f"N{i+1}", "kind": ITEMS[3+i%3], "ready": True, "pos": [18+13*i, 0]} for i in range(6)]
            monsters = [{"id": "M1", "pos": [50+.8*math.sin(tick/50), 15], "state": "chase"}]
            if self.day >= 3:
                monsters.append({"id": "M2", "pos": [76, 21], "state": "patrol"})
            state["snapshot"] = dict(tick=tick, meta=TUNING["gather"], hold=["ca_keo","bong_sung","keo_neo"],
                hold_capacity=12, time_left_ticks=max(0, 10800-tick), fish=fish, nodes=nodes, monsters=monsters,
                player={"pos": [34, 8], "at_surface": False, "heading_deg": 0, "hp": 2, "hp_max": 3,
                        "oxygen_ticks": max(0, oxygen-tick), "oxygen_max_ticks": oxygen, "catch_cd_ticks": 0})
            if tick >= 120:
                state["events"] = [{"name": "crocodile_hit", "tick": 120, "data": {"damage": 1}}]
        elif self.screen == "quan":
            stoves = [{"id": f"B{i+1}", "pos": [3+i*4, 8], "state": "cooking" if served else "idle",
                       "cook_ticks_left": 180+i*60, "dish": {"dish_id": DISHES[i]} if served else None}
                      for i in range(2)]
            tables = [{"id": f"T{i+1}", "pos": pos} for i, pos in enumerate([[3, 3], [7, 3], [11, 3], [13, 7]])]
            customers = [{"id": f"C{i+1}", "table_id": t["id"], "state": "waiting", "order_status": "reserved",
                          "dish_id": DISHES[i+2], "reserved": {ITEMS[i]: 1},
                          "patience_ticks_left": max(0, 3600-i*280-tick)} for i, t in enumerate(tables)] if served else []
            state["snapshot"] = dict(tick=tick, meta=TUNING["quan"], time_left_ticks=max(0, 10800-tick),
                player={"pos": [8, 5]}, money=self.money, reputation=3, hand=None,
                stock=inventory, stoves=stoves, tables=tables, customers=customers)
        return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, choices=range(1, 6), default=1)
    parser.add_argument("--port", type=int, default=8782)
    parser.add_argument("--faint", action="store_true")
    args = parser.parse_args()
    preview, lock = Preview(args.days, args.faint), Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, code, body, kind="application/json"):
            payload = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", f"{kind}; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                self.reply(200, (ROOT / "chonoi/web/index.html").read_bytes(), "text/html")
            elif self.path == "/state":
                with lock:
                    self.reply(200, preview.snapshot())
            else:
                self.reply(404, {"ok": False})

        def do_POST(self):
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 4096:
                    raise ValueError
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError
            except ValueError:
                self.reply(400, {"ok": False})
                return
            with lock:
                preview.expire_shop()
                if self.path == "/input":
                    preview.keys(data)
                    self.reply(200, {"ok": True})
                elif self.path == "/action":
                    ok = preview.action(data.get("action"), data)
                    self.reply(200 if ok else 409, {"ok": ok})
                else:
                    self.reply(404, {"ok": False})

    with ThreadingHTTPServer(("127.0.0.1", args.port), Handler) as server:
        print(f"Fixture Phase 2 tại http://127.0.0.1:{server.server_port}/", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
