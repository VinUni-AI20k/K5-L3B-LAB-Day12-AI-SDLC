"""Soak test nhiều Ngày trong một tiến trình (Test Contract v1.3, AC-P4-03).

Chạy: python3 -m chonoi.soak --seed 7 --days 10 --out soak.json
- Một `DaySim` chạy N Ngày bằng bot tất định (cập bến ngay -> quán mở tới hết giờ -> đóng Shop ngay).
- Kế hoạch Ngày 6..N lặp lại D1..D5 (`((day - 1) % 5) + 1`), tiền/earned/uy tín/cấp/id giữ xuyên suốt.
- Xuất `{days, days_completed, crashes, results, duration_s}`; `results[]` = `{day, earned, reputation, score}`
  tại thời điểm Shop đóng. Chạy lại cùng seed cho `results` giống hệt (không ghi xếp hạng).
"""

import argparse
import json
import os
import sys
import time

from .contract import load_contract
from .errors import BadInput
from .inputs import InputState
from .sim.day import DaySim


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write(f"lỗi: {message}\n")
        sys.exit(2)


def _int(name):
    def conv(s):
        try:
            return int(s)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{name} phải là số nguyên")
    return conv


def _day_score(earned: int, reputation) -> int:
    """Công thức điểm cuối Ngày: earned + round(reputation * 100)."""
    return int(earned) + int(round(float(reputation) * 100))


def _ensure_cyclic_plans(day_sim: DaySim, days: int):
    """Đảm bảo Ngày > 5 lặp lại kế hoạch D1..D5 (`((day - 1) % 5) + 1`)."""
    base_len = len(day_sim.plans)
    if base_len <= 0:
        return
    for d in range(1, days + 1):
        if d not in day_sim.plans:
            src_day = ((d - 1) % base_len) + 1
            src = day_sim.plans[src_day]
            day_sim.plans[d] = {
                "dishes": dict(src["dishes"]),
                "ingredients": dict(src["ingredients"]),
            }


def _bot_input(sim: DaySim, phase_tick: int) -> InputState:
    """Bot tất định: cập bến ngay ở gather, chờ hết ca ở quan, đóng Shop ngay ở shop."""
    if sim.phase == "gather":
        # Bấm interact ở tick 0 (đang đứng sẵn ở bến dock_pos) để cập bến ngay
        if phase_tick == 0:
            return InputState((0.0, 0.0), {"interact": True}, {"interact"})
        return InputState((0.0, 0.0), {}, set())
    if sim.phase == "shop":
        if phase_tick == 0:
            return InputState((0.0, 0.0), {"shop_done": True}, {"shop_done"})
        return InputState((0.0, 0.0), {}, set())
    return InputState((0.0, 0.0), {}, set())


def run_soak(tuning: dict, seed: int, days: int) -> dict:
    t0 = time.perf_counter()
    crashes = 0
    results = []
    days_completed = 0

    try:
        sim = DaySim(tuning, {}, seed=seed, days=days)
        _ensure_cyclic_plans(sim, days)

        # Giới hạn tick an toàn mỗi Ngày (gather + quan + shop tối đa ~30.000 tick)
        max_ticks_per_day = 50000
        day_ticks = 0

        while not sim.done:
            current_day = sim.day
            try:
                inp = _bot_input(sim, sim.phase_tick)
                events = sim.step(inp)
                day_ticks += 1

                for phase, day_num, name, _data in events:
                    if phase == "shop" and name == "shop_end":
                        results.append({
                            "day": day_num,
                            "earned": sim.earned,
                            "reputation": sim.reputation,
                            "score": _day_score(sim.earned, sim.reputation),
                        })

                if sim.day != current_day or sim.done:
                    day_ticks = 0
                elif day_ticks > max_ticks_per_day:
                    raise RuntimeError(f"Ngày {current_day} vượt quá {max_ticks_per_day} tick")
            except Exception:
                crashes += 1
                break

        days_completed = sim.days_completed
    except Exception:
        crashes += 1

    duration_s = round(time.perf_counter() - t0, 4)
    return {
        "days": days,
        "days_completed": days_completed,
        "crashes": crashes,
        "results": results,
        "duration_s": duration_s,
    }


def main(argv=None) -> int:
    p = _Parser(prog="chonoi.soak")
    p.add_argument("--seed", required=True, type=_int("seed"))
    p.add_argument("--days", required=True, type=_int("days"))
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)

    try:
        if a.days < 1:
            raise BadInput("--days phải là số nguyên >= 1")
        contract = load_contract()
        tuning = contract["tuning"]
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2

    report = run_soak(tuning, seed=a.seed, days=a.days)
    try:
        out_dir = os.path.dirname(os.path.abspath(a.out))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            f.write("\n")
    except OSError as e:
        sys.stderr.write(f"lỗi ghi: {e}\n")
        return 1

    return 0 if report["crashes"] == 0 and report["days_completed"] == a.days else 1


if __name__ == "__main__":
    sys.exit(main())