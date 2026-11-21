"""Subprocess probe của API gather đã chuẩn hóa, không thay validator/kho của nhóm.

P3 adapter chưa có: probe chỉ kiểm luật sim và payload bàn giao; không khẳng định
file kho/CLI v1.2 đã hoạt động. advance=false mô phỏng caller đang pause và không
gọi gameplay, thay vì cài một vòng day khác vào sản phẩm.
"""

import json
import sys

from chonoi.ids import IdAllocator
from chonoi.inputs import InputPlayer
from chonoi.jsonl import dumps
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim


def main():
    request = json.load(sys.stdin)
    ids = IdAllocator()
    for phase in request.get("phases", [request]):
        sim = GatherSim.from_contract(phase["contract"], phase.get("scenario", {}),
                                      Streams(phase.get("seed", 1)), ids,
                                      day=phase.get("day", 1), active_upgrades=phase.get("upgrades", {}))
        steps = phase.get("steps", [])
        player = InputPlayer([{"tick": i, **{k: v for k, v in step.items() if k != "advance"}}
                              for i, step in enumerate(steps)])
        played = 0
        print(dumps({"type": "snapshot", "tick": played, **sim.snapshot()}))
        for i, step in enumerate(steps):
            inp = player.advance(i)
            if step.get("advance", True) and not sim.done:
                played += 1
                for name, data in sim.step(inp):
                    print(dumps({"type": "event", "tick": played, "name": name, "data": data}))
            print(dumps({"type": "snapshot", "tick": played, **sim.snapshot()}))


if __name__ == "__main__":
    main()
