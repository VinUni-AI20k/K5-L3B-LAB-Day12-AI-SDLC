"""Điểm vào headless: python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out out.jsonl

Mã thoát: 0 bình thường; 2 tham số/đầu vào sai (kiểm TRƯỚC khi ghi đầu ra); 1 lỗi chạy/ghi.
"""

import argparse
import os
import sys

from .contract import load_contract
from .errors import BadInput
from .inputs import load_frames
from .inventory import read_inventory
from .leaderboard import DEFAULT_STORE, export as export_leaderboard, record as record_leaderboard
from .runner import run
from .scenario import load_scenario


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


def main(argv=None) -> int:
    p = _Parser(prog="chonoi.headless")
    p.add_argument("--mode", choices=["gather", "quan", "day"])  # `day` có từ v1.1
    p.add_argument("--seed", type=_int("seed"))
    p.add_argument("--ticks", type=_int("ticks"))
    p.add_argument("--out")
    p.add_argument("--scenario")
    p.add_argument("--inputs")
    p.add_argument("--inventory")
    p.add_argument("--inventory-out", dest="inventory_out")
    p.add_argument("--snapshot-every", dest="snapshot_every", type=_int("snapshot-every"), default=10)
    p.add_argument("--days", type=_int("days"))  # v1.1: chỉ với day, 1..5, mặc định 1
    p.add_argument("--leaderboard")
    p.add_argument("--player-name")
    p.add_argument("--export-leaderboard", metavar="OUT_JSON")
    a = p.parse_args(argv)
    if a.export_leaderboard:
        if a.mode or a.seed is not None or a.ticks is not None or a.out or a.scenario or a.inputs or a.inventory \
                or a.inventory_out or a.days is not None or a.player_name:
            sys.stderr.write("--export-leaderboard không dùng kèm tham số chạy\n")
            return 2
        try:
            store = a.leaderboard or DEFAULT_STORE
            if os.path.abspath(store) == os.path.abspath(a.export_leaderboard):
                raise ValueError("store và file export phải khác đường dẫn")
            export_leaderboard(store, a.export_leaderboard)
        except (OSError, ValueError) as e:
            sys.stderr.write(f"lỗi leaderboard: {e}\n")
            return 1
        return 0
    try:
        if not a.mode or a.seed is None or a.ticks is None or not a.out:
            raise BadInput("cần --mode, --seed, --ticks và --out")
        if (a.leaderboard is None) != (a.player_name is None):
            raise BadInput("--leaderboard và --player-name phải dùng cùng nhau")
        if a.leaderboard is not None and (a.mode != "day" or (a.days if a.days is not None else 1) != 5
                                          or a.scenario or a.inputs or a.inventory or a.inventory_out):
            raise BadInput("leaderboard chỉ hỗ trợ day chuẩn đủ 5 ngày, không scenario/input/kho")
        if a.leaderboard and os.path.abspath(a.leaderboard) == os.path.abspath(a.out):
            raise BadInput("store leaderboard phải khác file JSONL")
        if a.player_name is not None and not a.player_name.strip():
            raise BadInput("--player-name không được rỗng")
        if a.days is not None and a.mode != "day":
            raise BadInput("--days chỉ dùng với --mode day")
        if a.mode == "day" and not (1 <= (a.days if a.days is not None else 1) <= 5):
            raise BadInput("--days phải là số nguyên từ 1 đến 5")
        if a.ticks < 0:
            raise BadInput("--ticks phải >= 0")
        if a.snapshot_every <= 0:
            raise BadInput("--snapshot-every phải > 0")
        if a.inventory and a.mode != "quan":
            raise BadInput("--inventory chỉ dùng với quan")
        if a.inventory_out and a.mode != "gather":
            raise BadInput("--inventory-out chỉ dùng với gather")
        outs = [x for x in (a.out, a.inventory_out) if x]
        ins = [x for x in (a.scenario, a.inputs, a.inventory) if x]
        paths = [os.path.abspath(x) for x in outs + ins]
        if len(set(paths)) != len(paths):
            raise BadInput("các đường dẫn đầu vào/đầu ra phải khác nhau")
        contract = load_contract()
        tuning = contract["tuning"]
        scenario = load_scenario(a.scenario, a.mode, tuning)
        frames = load_frames(a.inputs)
        inventory = read_inventory(a.inventory) if a.inventory else None
        if inventory is not None and "stock" in scenario:
            raise BadInput("vừa có quan.stock vừa có --inventory")
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    try:
        sess = run(a.mode, tuning, scenario, a.seed, frames, a.ticks, a.out, a.snapshot_every,
            inventory=inventory, inventory_out=a.inventory_out, days=a.days or 1)
        if a.leaderboard and sess.done and sess.reason == "days_complete" and sess.days_completed == 5:
            record_leaderboard(a.leaderboard, a.player_name, sess.end_row()["score"], sess.days_completed, a.seed)
    except BadInput as e:  # lỗi mức luật phát hiện lúc dựng sim
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    except OSError as e:
        sys.stderr.write(f"lỗi ghi: {e}\n")
        return 1
    except ValueError as e:
        sys.stderr.write(f"lỗi leaderboard: {e}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
