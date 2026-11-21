"""Soak headless (Test Contract v1.3, TICKET-04 mục 2): nhiều Ngày trong MỘT tiến trình, bot tất định.

    python3 -m chonoi.soak --seed 7 --days 10 --out soak.json

Mỗi Ngày đi qua gather → quan → shop; kế hoạch D1–D5 lặp ở Ngày 6–10 (`DaySession.day_plan()`).
Tiền, tổng thu, uy tín, cấp nâng cấp, số Ngày và id cá thể đi xuyên suốt (cùng một DaySession).

Bot tất định (không RNG, không đồng hồ): ở gather nhấn `interact` ngay (đang đứng ở bến → cập bến với giỏ
mẫu rỗng); ở quán đứng yên tới hết ca; ở Shop nhấn `shop_done`. Mục tiêu là kiểm vòng ngày chạy dài không
lỗi và tất định, không tối ưu điểm.

Đầu ra: {"days", "days_completed", "crashes", "results": [{"day", "earned", "reputation", "score"}], "duration_s"}.
`results` chụp lúc Shop đóng. `duration_s` là đồng hồ thật — bỏ qua khi so tất định.
"""

import argparse
import json
import sys
import time
import traceback

from .contract import load_contract
from .day import DaySession
from .errors import BadInput
from .inputs import InputState

MAX_TICKS_PER_DAY = 22_200  # gather 10.800 + quán 10.800 + Shop 600 (TICKET-02, một Ngày không pause)


class Bot:
    """Nhấn nút theo pha, tạo cạnh lên bằng cách nhả ở bước xen kẽ."""

    BUTTON = {"gather": "interact", "shop": "shop_done"}

    def __init__(self):
        self._held = False

    def advance(self, phase) -> InputState:
        btn = self.BUTTON.get(phase)
        if btn is None:
            self._held = False
            return InputState((0.0, 0.0), {}, set())
        press = not self._held
        self._held = press
        return InputState((0.0, 0.0), {btn: press}, {btn} if press else set())


def run_soak(seed: int, days: int) -> dict:
    tuning = load_contract()["tuning"]
    t0 = time.perf_counter()
    results, crashes = [], 0
    sess = None
    try:
        sess = DaySession(tuning, {}, seed, days)
        bot = Bot()
        limit = days * MAX_TICKS_PER_DAY + 10
        while not sess.done and sess.tick < limit:
            for row in sess.step(bot.advance(sess.sim.phase)):
                if row["type"] == "event" and row["name"] == "shop_end":
                    results.append({"day": row["day"], "earned": sess.earned, "reputation": sess.reputation,
                                    "score": sess._score()})
    except Exception:  # lỗi thực thi trong vòng ngày: đếm crash, không giấu
        crashes += 1
        traceback.print_exc(file=sys.stderr)
    return {"days": days, "days_completed": sess.days_completed if sess else 0, "crashes": crashes,
            "results": results, "duration_s": round(time.perf_counter() - t0, 3)}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.soak")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--days", type=int, required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    if a.days < 1:
        sys.stderr.write("đầu vào sai: --days phải >= 1\n")
        return 2
    try:
        report = run_soak(a.seed, a.days)
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    try:
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            json.dump(report, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
    except OSError as e:
        sys.stderr.write(f"lỗi ghi: {e}\n")
        return 1
    return 0 if report["crashes"] == 0 and report["days_completed"] == report["days"] else 1


if __name__ == "__main__":
    sys.exit(main())
