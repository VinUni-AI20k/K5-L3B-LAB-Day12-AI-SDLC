"""File inputs (Contract C): frames, kế thừa trường vắng, cạnh lên (false -> true).

Dùng: ip = InputPlayer(frames); mỗi bước k: state = ip.advance(k)
  state.move -> (x, d) trong gather hoặc (x, z) trong quan, đã chuẩn hóa;
  state.pressed("interact") -> True nếu CẠNH LÊN ở bước này.
  state.buy -> chuỗi `buy` (v1.1) CHỈ ở bước có frame khai báo, không kế thừa; None nếu không có.

v1.1 (TV6, T241): thêm nút `pause`, `shop_done`, `attack`, `photo` (bool, cạnh lên) và trường chuỗi `buy`.
`attack`/`photo` nhận đúng kiểu nhưng sim bỏ qua khi chưa bật mở rộng (đề §4.2). Bộ nút chọn theo
`contract_version` (xem `buttons_for`) để contract v1.0 vẫn từ chối nút của phase sau như Phase 1.
"""

import json
import math

from .errors import BadInput

BUTTONS_V10 = ("interact", "catch")  # v1.0
BUTTONS_V11 = ("interact", "catch", "pause", "shop_done", "attack", "photo")  # v1.1 (đề §4.2)
STRINGS_V11 = ("buy",)  # chuỗi khác rỗng, chỉ tại frame khai báo


def is_v11(contract: dict) -> bool:
    """contract_version >= 1.1 (so theo số, "1.10" > "1.9")."""
    try:
        return tuple(int(x) for x in str(contract.get("contract_version", "1.0")).split(".")) >= (1, 1)
    except ValueError:
        return False


def buttons_for(contract: dict):
    """(nút bool, trường chuỗi) theo phiên bản contract."""
    return (BUTTONS_V11, STRINGS_V11) if is_v11(contract) else (BUTTONS_V10, ())


class InputState:
    def __init__(self, move, held, edges, buy=None):
        self.move = move
        self.held = held
        self._edges = edges
        self.buy = buy

    def without_actions(self) -> "InputState":
        """Bản bỏ mọi cạnh và `buy` (dùng khi đang pause), giữ move/held."""
        return InputState(self.move, self.held, set(), None)

    def pressed(self, name: str) -> bool:
        return name in self._edges


def load_frames(path, buttons=BUTTONS_V10, strings=()):
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
    allowed = {"tick", "move", *buttons, *strings}
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
        for k in strings:
            if k in fr and not (isinstance(fr[k], str) and fr[k]):
                raise BadInput(f"frame {i}: {k} phải là chuỗi khác rỗng")
        frames.append(fr)
    return frames


def normalize(move):
    x, y = float(move[0]), float(move[1])
    n = math.hypot(x, y)
    if n > 1:
        return (x / n, y / n)
    return (x, y)


class InputPlayer:
    def __init__(self, frames, buttons=BUTTONS_V10, strings=()):
        self._frames = {fr["tick"]: fr for fr in frames}
        self._buttons = buttons
        self._move = (0.0, 0.0)
        self._held = {b: False for b in buttons}
        self._strings = strings

    def advance(self, k: int) -> InputState:
        """Đọc input có tick == k. Trả trạng thái dùng cho bước k."""
        edges = set()
        buy = None
        fr = self._frames.get(k)
        if fr:
            if "move" in fr:
                self._move = normalize(fr["move"])
            for b in self._buttons:
                if b in fr:
                    if fr[b] and not self._held[b]:
                        edges.add(b)
                    self._held[b] = fr[b]
            if "buy" in self._strings:
                buy = fr.get("buy")  # không kế thừa sang frame sau
        return InputState(self._move, dict(self._held), edges, buy)


class LiveInputs:
    """Input trực tiếp (cửa sổ chơi): giữ trạng thái nút, nhớ cạnh lên giữa hai tick để không mất cú bấm nhanh.

    Luồng khác gọi set(); luồng mô phỏng gọi advance() mỗi tick (cần khóa ngoài nếu dùng nhiều luồng).
    """

    def __init__(self, buttons=BUTTONS_V10):
        self._buttons = buttons
        self._move = (0.0, 0.0)
        self._held = {b: False for b in buttons}
        self._pending = set()
        self._buy = None

    def set(self, move=None, buy=None, **buttons):
        """`buy` (chuỗi) là lệnh một lần: giữ tới tick kế rồi xóa (lệnh mới ghi đè lệnh chưa chạy)."""
        if buy is not None:
            self._buy = buy
        if move is not None:
            self._move = normalize(move)
        for b, v in buttons.items():
            if b not in self._held:
                continue
            if v and not self._held[b]:
                self._pending.add(b)
            self._held[b] = bool(v)

    def advance(self) -> InputState:
        edges, self._pending = self._pending, set()
        buy, self._buy = self._buy, None
        return InputState(self._move, dict(self._held), edges, buy)
