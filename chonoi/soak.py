"""Soak headless (P4-04, AC-P4-03): chạy nhiều Ngày liền trong MỘT tiến trình bằng chế độ `day`, ghi `soak.json`.

    python3 -m chonoi.soak --seed 7 --days 10 --out soak.json

Ngày 6 trở đi lặp lại kế hoạch D1–D5 (`DaySim._plan_for`). Input do một bot tất định: lặn, hái nút gần nhất ở mặt nước
rồi về bến; buổi quán và Shop không có input. Mục tiêu là chạy lâu mà không sập, không phải chơi giỏi.

`soak.json` có đúng năm trường: `days` (số Ngày yêu cầu), `days_completed`, `crashes` (số lần sim ném lỗi; có lỗi thì
dừng và thoát mã 1), `results` (mỗi Ngày xong một dòng: tiền, tổng thu, uy tín, điểm, nâng cấp) và `duration_s` (thời
gian thật, không tất định). Soak không ghi bảng xếp hạng. Mã thoát: 0 bình thường, 1 có lỗi khi chạy hoặc ghi, 2 sai đối số.
"""

import argparse
import json
import math
from pathlib import Path
import tempfile
from time import perf_counter

from .contract import load_contract
from .errors import BadInput
from .inputs import InputState
from .runner import Session

MAX_DAYS = 100


def _steer(dx):
    """Bơi theo chiều ngang về phía mục tiêu, dừng khi đã tới (tránh dao động)."""
    return 0.0 if abs(dx) < 1e-9 else math.copysign(1.0, dx)


def bot_input(sim, tuning):
    """Input tất định theo trạng thái sim hiện tại (chỉ pha gather mới có hành động)."""
    if sim.phase != "gather":
        return InputState((0.0, 0.0), {}, set())
    g = tuning["gather"]
    cur = sim.current
    x = cur.pos[0]
    ready = [n for n in cur.nodes if n["regrow_ticks"] == 0]
    full = len(cur.hold) + g["node_yield"] > g["hold_capacity"]
    if ready and not full:
        target, radius = min(ready, key=lambda n: (abs(n["pos"][0] - x), n["id"]))["pos"], g["interact_radius"]
    else:
        target, radius = g["dock_pos"], g["dock_radius"]
    dx = target[0] - x
    near = abs(dx) <= radius * 0.5 and cur.pos[1] <= g["surface_depth"]
    edges = {"interact"} if near and cur.phase_tick % 2 == 0 else set()  # cạnh lên cách tick, không giữ phím
    return InputState((0.0 if near else _steer(dx), 0.0), {}, edges)


def run_soak(seed, days):
    contract = load_contract()
    tuning = contract["tuning"]
    session = Session("day", tuning, {}, seed, days=days, contract_version=contract["contract_version"])
    mult = tuning["score"]["reputation_multiplier"]
    results, crashes, start = [], 0, perf_counter()
    try:
        while not session.done:
            session.step(bot_input(session.sim, tuning))
            sim = session.sim
            if sim.days_completed > len(results):  # đúng tick đóng Shop: tiền, uy tín, nâng cấp là của Ngày vừa xong
                results.append({"day": sim.days_completed, "money": sim.money, "earned": sim.earned,
                                "reputation": sim.reputation, "score": sim.earned + mult * math.floor(sim.reputation),
                                "upgrades": dict(sim.upgrades)})
    except Exception:  # noqa: BLE001 — soak phải đếm mọi lỗi sim thay vì tự sập
        crashes += 1
    return {"days": days, "days_completed": session.sim.days_completed, "crashes": crashes, "results": results,
            "duration_s": perf_counter() - start}


def write_report(path, report):
    """Thay file đích sau khi đã ghi xong JSON."""
    stream = tempfile.NamedTemporaryFile(dir=path.resolve().parent, delete=False, mode="w", encoding="utf-8", newline="\n")
    temporary = Path(stream.name)
    try:
        with stream:
            json.dump(report, stream, indent=2, allow_nan=False)
            stream.write("\n")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--seed", type=int, default=7, help="seed (mặc định: 7)")
    parser.add_argument("--days", type=int, default=10, help=f"số Ngày liền nhau, 1 đến {MAX_DAYS} (mặc định: 10)")
    parser.add_argument("--out", type=Path, default=Path("soak.json"))
    args = parser.parse_args(argv)
    if not 1 <= args.days <= MAX_DAYS:
        parser.error(f"--days phải từ 1 đến {MAX_DAYS}")
    try:
        report = run_soak(args.seed, args.days)
        write_report(args.out, report)
    except BadInput as exc:
        parser.error(str(exc))
    except OSError as exc:
        parser.exit(1, f"lỗi ghi soak: {exc}\n")
    return 1 if report["crashes"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
