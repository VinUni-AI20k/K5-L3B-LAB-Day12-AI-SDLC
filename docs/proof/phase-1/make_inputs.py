"""Bot chơi thử để tạo file inputs THẬT cho lượt đầy đủ (bằng chứng "chơi được cả hai buổi").

Bot lái cùng `Session` mà headless dùng, ghi lại frame mỗi khi điều khiển đổi. File inputs sinh ra
rồi được chạy lại qua headless_cmd (run_proof.sh) — bot không đụng vào luật.

Chạy từ gốc repo: python3 docs/proof/phase-1/make_inputs.py
"""

import json
import math
import os
import sys

sys.path.insert(0, os.getcwd())
from chonoi.contract import load_contract  # noqa: E402
from chonoi.inputs import InputState, normalize  # noqa: E402
from chonoi.runner import Session  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TUNING = load_contract()["tuning"]


class Recorder:
    def __init__(self):
        self.frames, self.move, self.held = [], (0.0, 0.0), {"interact": False, "catch": False}

    def state(self, tick, move, press=None):
        fr = {"tick": tick}
        move = tuple(round(c, 3) for c in move)
        if move != self.move:
            fr["move"] = list(move)
            self.move = move
        edges = set()
        for b in ("interact", "catch"):
            want = b == press
            if want != self.held[b]:
                fr[b] = want
                self.held[b] = want
                if want:
                    edges.add(b)
        if len(fr) > 1:
            self.frames.append(fr)
        return InputState(normalize(self.move), dict(self.held), edges)


def toward(pos, tgt):
    dx, dy = tgt[0] - pos[0], tgt[1] - pos[1]
    n = math.hypot(dx, dy)
    return (0.0, 0.0) if n < 1e-9 else (dx / n, dy / n)


def gather_bot():
    plan = [((15, 5), "catch"), ((12, 0), "interact"), ((28, 0), "interact"), ((30, 10), "catch"),
            ((44, 0), "interact"), ((45, 10), "catch"), ((60, 0), "interact"), ((2, 0), "interact")]
    s = Session("gather", TUNING, {}, 7)
    rec, i, cool = Recorder(), 0, 0
    while not s.done and s.tick < 10800:
        snap = s.snapshot()
        pos = snap["player"]["pos"]
        if i < len(plan):
            tgt, act = plan[i]
            # đi lên mặt nước trước khi tới nút; thiếu oxy thì nổi lên
            if snap["player"]["oxygen_ticks"] < 300 and pos[1] > 0.5 and act == "catch":
                tgt = (pos[0], 0)
            d = math.dist(pos, tgt)
            if d < 0.8 and cool == 0:
                inp = rec.state(s.tick, (0.0, 0.0), act)
                i, cool = i + 1, 2
            else:
                inp = rec.state(s.tick, toward(pos, tgt) if d >= 0.3 else (0.0, 0.0))
                cool = max(0, cool - 1)
        else:
            inp = rec.state(s.tick, (0.0, 0.0))
        s.step(inp)
    return rec.frames


def quan_bot(stock):
    q = TUNING["quan"]
    stove, table = q["stoves"][0]["pos"], q["tables"][0]["pos"]
    s = Session("quan", TUNING, {}, 7, inventory=stock)
    rec, cool = Recorder(), 0
    while not s.done and s.tick < 10800:
        snap = s.snapshot()
        pos = snap["player"]["pos"]
        st = snap["stoves"][0]
        waiting = [c for c in snap["customers"] if c["state"] == "waiting"]
        tgt = None
        if snap["hand"] is not None:
            tgt = table
        elif st["state"] == "ready" or (st["state"] == "idle" and any(c["order_status"] == "reserved" for c in waiting)):
            tgt = stove
        elif st["state"] == "cooking":
            tgt = stove
        if tgt is None:
            inp = rec.state(s.tick, (0.0, 0.0))
        else:
            d = math.dist(pos, tgt)
            busy = st["state"] == "cooking" and snap["hand"] is None
            if d < 1.0 and cool == 0 and not busy:
                inp = rec.state(s.tick, (0.0, 0.0), "interact")
                cool = 2
            else:
                inp = rec.state(s.tick, toward(pos, tgt) if d >= 0.5 else (0.0, 0.0))
                cool = max(0, cool - 1)
        s.step(inp)
    return rec.frames


def main():
    g = gather_bot()
    with open(os.path.join(HERE, "full-gather-inputs.json"), "w") as f:
        json.dump({"frames": g}, f)
    # kho cho quán lấy từ đúng lượt gather vừa chơi (qua Session, cùng luật)
    s = Session("gather", TUNING, {}, 7)
    from chonoi.inputs import InputPlayer
    pl = InputPlayer(g)
    while not s.done and s.tick < 10800:
        s.step(pl.advance(s.tick))
    stock = s.sim.inventory_items()
    qf = quan_bot(stock)
    with open(os.path.join(HERE, "full-quan-inputs.json"), "w") as f:
        json.dump({"frames": qf}, f)
    print("gather frames", len(g), "reason", s.sim.reason, "stock", stock, "| quan frames", len(qf))


if __name__ == "__main__":
    main()
