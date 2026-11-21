"""Soak headless (Test Contract v1.3, Ticket-04 mục 2): python3 -m chonoi.soak --seed 7 --days 10 --out soak.json

Chạy N Ngày trong MỘT tiến trình headless (`chonoi.day.DaySession`), điều khiển bằng bot tất định: mỗi bước bot chỉ
đọc trạng thái mô phỏng hiện tại, không dùng ngẫu nhiên hay đồng hồ, nên cùng seed cho cùng kết quả gameplay.
Mỗi Ngày đi qua gather -> quan -> shop. Kế hoạch D1-D5 lặp ở Ngày 6-10 (DaySession lo). Tiền, tổng thu, uy tín,
cấp nâng cấp, số Ngày và id cá thể tiếp tục xuyên suốt. Không ghi file kho, không ghi bảng xếp hạng.

soak.json: {"days", "days_completed", "crashes", "results": [{"day", "earned", "reputation", "score"}], "duration_s"}
- results ghi lúc mỗi Shop đóng (event shop_end).
- crashes: số lần mô phỏng ném lỗi (lỗi đầu tiên làm dừng lượt, ghi chi tiết ra stderr).
- duration_s là thời gian thực, không thuộc gameplay (bỏ qua khi so tính lặp).
Mã thoát: 0 đã ghi soak.json (kể cả khi có crash); 2 tham số sai; 1 không ghi được đầu ra.
"""

import argparse
import json
import math
import os
import sys
import time
import traceback

from .contract import load_contract
from .errors import BadInput
from .inputs import InputState
from .runner import score_of

TICKS_PER_DAY_MAX = 22_200  # Ticket-02: một Ngày không pause tối đa 22.200 tick


class Bot:
    """Bot tất định: sáng hái nút ở mặt nước rồi cập bến; tối nấu, bưng, phục vụ; Shop mua nâng cấp nếu đủ tiền
    rồi đóng. Chỉ đọc trạng thái sim, không sửa."""

    HOLD_TARGET = 8          # hái tới chừng này món thì về bến
    RETURN_MARGIN = 1_500    # còn ít tick hơn mức này thì về bến
    NEAR = 0.6               # coi như tới đích (m)

    def __init__(self, tuning):
        self.t = tuning
        self._pressed = False  # nhả nút xen kẽ để mỗi lần bấm là một cạnh lên
        self._shop_ticks = 0

    def _press(self, want):
        """Trả edges cho bước này: chỉ bấm khi bước trước đã nhả."""
        if want and not self._pressed:
            self._pressed = True
            return {"interact"}
        self._pressed = False
        return set()

    @staticmethod
    def _toward(src, dst):
        dx, dy = dst[0] - src[0], dst[1] - src[1]
        n = math.hypot(dx, dy)
        return (0.0, 0.0) if n < 1e-9 else (dx / n, dy / n)

    def act(self, sim) -> InputState:
        if sim.phase == "gather":
            return self._gather(sim)
        if sim.phase == "quan":
            return self._quan(sim)
        return self._shop(sim)

    # --- buổi sáng -----------------------------------------------------------------
    def _gather(self, sim):
        g = self.t["gather"]
        pos = sim.pos
        go_home = len(sim.hold) >= self.HOLD_TARGET or sim.time_left_ticks <= self.RETURN_MARGIN
        if not go_home:
            free = int(g["hold_capacity"]) - len(sim.hold)
            ready = [n for n in sim.nodes if n["regrow_ticks"] == 0 and free > 0]
            if ready:
                node = min(ready, key=lambda n: (abs(n["pos"][0] - pos[0]), n["id"]))
                target = [node["pos"][0], 0.0]
                if abs(node["pos"][0] - pos[0]) <= g["interact_radius"] * 0.5 and pos[1] <= g["surface_depth"]:
                    return InputState((0.0, 0.0), {}, self._press(True))
                return InputState(self._toward(pos, target), {}, self._press(False))
        dock = g["dock_pos"]
        if math.dist(pos, dock) <= g["dock_radius"] * 0.5:
            return InputState((0.0, 0.0), {}, self._press(True))
        return InputState(self._toward(pos, dock), {}, self._press(False))

    # --- buổi tối ------------------------------------------------------------------
    def _quan(self, sim):
        q = self.t["quan"]
        target = None
        if sim.hand:
            order = sim.hand.get("order_id") if isinstance(sim.hand, dict) else None
            seat = next((c for c in sim.customers if c["id"] == order), None)
            if seat is not None:
                target = next(tb["pos"] for tb in sim.tables if tb["id"] == seat["table_id"])
        if target is None:
            ready = [s for s in sim.stoves if s.get("state") == "ready"]
            idle = [s for s in sim.stoves if s.get("state") == "idle"]
            waiting = [c for c in sim.customers if c.get("order_status") == "reserved"]
            if ready and not sim.hand:
                target = ready[0]["pos"]
            elif idle and waiting:
                target = idle[0]["pos"]
        if target is None:
            return InputState((0.0, 0.0), {}, self._press(False))
        if math.dist(sim.pos, target) <= min(self.NEAR, q["interact_radius"]):
            return InputState((0.0, 0.0), {}, self._press(True))
        return InputState(self._toward(sim.pos, target), {}, self._press(False))

    # --- Shop ----------------------------------------------------------------------
    def _shop(self, sim):
        self._shop_ticks += 1
        if self._shop_ticks == 1:
            ups, money = self.t["shop"]["upgrades"], sim.money
            for kind in ("oxygen", "hp"):
                level = sim.upgrades.get(kind, 0)
                if level < len(ups[kind]) and money >= ups[kind][level]["price"]:
                    return InputState((0.0, 0.0), {}, set(), buy=kind)
            return InputState((0.0, 0.0), {}, set())
        if self._shop_ticks == 2:
            return InputState((0.0, 0.0), {"shop_done": True}, {"shop_done"})
        return InputState((0.0, 0.0), {}, set())

    def reset_shop(self):
        self._shop_ticks = 0


def run(seed, days, contract=None, out_err=sys.stderr) -> dict:
    """Chạy soak, trả dict kết quả (chưa có duration_s)."""
    from .day import DaySession
    contract = contract or load_contract()
    tuning = contract["tuning"]
    results, crashes = [], 0
    sess = None
    try:
        sess = DaySession(tuning, {"gather": {}, "quan": {}, "day": {}}, seed, days, contract=contract)
        bot = Bot(tuning)
        limit = days * TICKS_PER_DAY_MAX * 2
        while not sess.done and sess.tick < limit:
            phase_before = sess.sim.phase
            rows = sess.step(bot.act(sess.sim))
            for r in rows:
                if r.get("name") == "shop_end":
                    results.append({"day": r["day"], "earned": sess.earned, "reputation": round(sess.reputation, 3),
                                    "score": score_of(tuning, sess.earned, sess.reputation)})
            if phase_before == "shop" and sess.sim.phase != "shop":
                bot.reset_shop()
        if not sess.done:
            raise RuntimeError(f"soak vượt {limit} tick mà chưa xong {days} Ngày")
    except Exception:  # soak đếm crash thay vì để tiến trình chết, để runner vẫn có soak.json
        crashes += 1
        traceback.print_exc(file=out_err)
    return {"days": days, "days_completed": sess.days_completed if sess else 0, "crashes": crashes,
            "results": results}


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write(f"lỗi: {message}\n")
        sys.exit(2)


def _pos_int(name):
    def conv(s):
        try:
            v = int(s)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{name} phải là số nguyên")
        return v
    return conv


def main(argv=None) -> int:
    p = _Parser(prog="chonoi.soak")
    p.add_argument("--seed", required=True, type=_pos_int("seed"))
    p.add_argument("--days", required=True, type=_pos_int("days"))
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    if a.days < 1:
        sys.stderr.write("lỗi: --days phải >= 1\n")
        return 2
    try:
        contract = load_contract()
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    t0 = time.perf_counter()
    report = run(a.seed, a.days, contract)
    report["duration_s"] = round(time.perf_counter() - t0, 3)
    try:
        d = os.path.dirname(os.path.abspath(a.out))
        os.makedirs(d, exist_ok=True)
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            json.dump(report, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
    except OSError as e:
        sys.stderr.write(f"lỗi ghi: {e}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
