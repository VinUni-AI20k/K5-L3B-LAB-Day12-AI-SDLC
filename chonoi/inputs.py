"""File inputs (Contract C): frames, kế thừa trường vắng, cạnh lên (false -> true).

Dùng: ip = InputPlayer(frames); mỗi bước k: state = ip.advance(k)
  state.move -> (x, d) trong gather hoặc (x, z) trong quan, đã chuẩn hóa;
  state.pressed("interact") -> True nếu CẠNH LÊN ở bước này.
"""

import json
import math

from .errors import BadInput

BUTTONS_V10 = ("interact", "catch")  # v1.0; các nút khác có từ phiên bản sau
BUTTONS_V11 = ("interact", "catch", "pause", "shop_done", "attack", "photo")


class InputState:
    def __init__(self, move, held, edges, buy=None, customer_choice=None):
        self.move = move
        self.held = held
        self._edges = edges
        self.buy = buy
        self.customer_choice = customer_choice

    def pressed(self, name: str) -> bool:
        return name in self._edges


def validate_customer_choice(value):
    if not isinstance(value, dict) or set(value) != {"customer_id", "dish_id"}:
        raise BadInput("customer_choice phải gồm customer_id và dish_id")
    if any(not isinstance(value[key], str) or not value[key] or len(value[key]) > 64
           for key in ("customer_id", "dish_id")):
        raise BadInput("customer_choice.customer_id và dish_id phải là chuỗi khác rỗng")
    return dict(value)


def load_frames(path, buttons=BUTTONS_V10, allow_buy=False, allow_customer_choice=False):
    if path is None:
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được inputs {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"frames"} or not isinstance(data["frames"], list):
        raise BadInput("inputs phải có đúng một khóa 'frames' (mảng)")
    last = -1
    frames = []
    allowed = {"tick", "move", *buttons}
    if allow_buy:
        allowed.add("buy")
    if allow_customer_choice:
        allowed.add("customer_choice")
    for i, fr in enumerate(data["frames"]):
        if not isinstance(fr, dict):
            raise BadInput(f"frame {i} không phải object")
        extra = set(fr) - allowed
        if extra:
            raise BadInput(f"frame {i} có trường lạ/chưa hỗ trợ: {sorted(extra)}")
        t = fr.get("tick")
        if isinstance(t, bool) or not isinstance(t, int) or t < 0:
            raise BadInput(f"frame {i}: tick phải là số nguyên >= 0")
        if t <= last:
            raise BadInput(f"frame {i}: tick trùng hoặc giảm")
        last = t
        if "move" in fr:
            m = fr["move"]
            ok = (isinstance(m, list) and len(m) == 2 and
                  all(isinstance(c, (int, float)) and not isinstance(c, bool) and math.isfinite(c) and -1 <= c <= 1 for c in m))
            if not ok:
                raise BadInput(f"frame {i}: move phải là [x, d] (gather) hoặc [x, z] (quan), mỗi số trong [-1, 1]")
        for b in buttons:
            if b in fr and not isinstance(fr[b], bool):
                raise BadInput(f"frame {i}: {b} phải là boolean")
        if "buy" in fr and fr["buy"] is not None:
            if not isinstance(fr["buy"], str):
                raise BadInput(f"frame {i}: buy phải là chuỗi hoặc null")
        if "customer_choice" in fr:
            if not allow_customer_choice:
                raise BadInput(f"frame {i}: customer_choice chỉ dùng với quan hoặc day")
            try:
                validate_customer_choice(fr["customer_choice"])
            except BadInput as e:
                raise BadInput(f"frame {i}: {e}")
        frames.append(fr)
    return frames


def normalize(move):
    x, y = float(move[0]), float(move[1])
    n = math.hypot(x, y)
    if n > 1:
        return (x / n, y / n)
    return (x, y)


class InputPlayer:
    def __init__(self, frames, buttons=BUTTONS_V10):
        self._frames = {fr["tick"]: fr for fr in frames}
        self._buttons = buttons
        self._move = (0.0, 0.0)
        self._held = {b: False for b in buttons}

    def advance(self, k: int) -> InputState:
        """Đọc input có tick == k. Trả trạng thái dùng cho bước k."""
        edges = set()
        buy = None
        customer_choice = None
        fr = self._frames.get(k)
        if fr:
            if "move" in fr:
                self._move = normalize(fr["move"])
            buy = fr.get("buy")
            customer_choice = fr.get("customer_choice")
            for b in self._buttons:
                if b in fr:
                    if fr[b] and not self._held[b]:
                        edges.add(b)
                    self._held[b] = fr[b]
        return InputState(self._move, dict(self._held), edges, buy=buy,
                          customer_choice=customer_choice)


class LiveInputs:
    """Input trực tiếp (cửa sổ chơi): giữ trạng thái nút, nhớ cạnh lên giữa hai tick để không mất cú bấm nhanh.

    Luồng khác gọi set(); luồng mô phỏng gọi advance() mỗi tick (cần khóa ngoài nếu dùng nhiều luồng).
    """

    def __init__(self, buttons=BUTTONS_V10):
        self._buttons = buttons
        self._move = (0.0, 0.0)
        self._held = {b: False for b in buttons}
        self._pending = set()
        self._next_buy = None
        self._next_customer_choice = None

    def set(self, move=None, buy=None, customer_choice=None, **buttons):
        if move is not None:
            self._move = normalize(move)
        if buy is not None:
            self._next_buy = buy
        if customer_choice is not None:
            self._next_customer_choice = validate_customer_choice(customer_choice)
        for b, v in buttons.items():
            if b not in self._held:
                continue
            if v and not self._held[b]:
                self._pending.add(b)
            self._held[b] = bool(v)

    def advance(self) -> InputState:
        edges, self._pending = self._pending, set()
        buy = self._next_buy
        self._next_buy = None
        customer_choice = self._next_customer_choice
        self._next_customer_choice = None
        return InputState(self._move, dict(self._held), edges, buy=buy,
                          customer_choice=customer_choice)
