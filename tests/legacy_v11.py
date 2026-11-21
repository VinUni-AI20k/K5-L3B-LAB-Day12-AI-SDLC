"""Chạy một module test cũ (Phase 1–2, fixture kho ĐẾM) trên manifest v1.1 tạm trong lúc chuyển sang v1.2.

Từ khi `game.contract.json` bật `contract_version: "1.2"` (Ticket-03), mọi fixture `hold: ["ca_loc"]`,
`stock: {"ca_loc": 1}`, `reserved: {"ca_loc": 1}` và file kho đếm đều đúng luật mà bị mã 2. Ticket-03 mục 3 cho phép
"hỗ trợ hai phiên bản nội bộ trong lúc chuyển": code vẫn nhận v1.1 (`contract.SUPPORTED_VERSIONS`), nên các test cũ
vẫn bảo vệ được các luật KHÔNG đổi ở v1.2 (bơi, oxy, Cá Sấu, cá bơi, khách, bếp, day/Shop/pause...).

Phần v1.2 (kho cá thể, độ tươi, giữ theo id, giá theo tươi) được kiểm bằng manifest thật qua `test_lat0_v12.py`,
`test_fresh_p3.py` (QA), `test_quan_p3.py`. Khi chủ mỗi file test chuyển fixture sang kho cá thể thì bỏ dòng import
module này. Danh sách module còn ghim: CHANGELOG.md mục v1.2.

Dùng trong module test:
    from legacy_v11 import setUpModule, tearDownModule  # noqa: F401
"""

import json
import os
import tempfile

from helpers import ROOT

_state = {}


def manifest_v11() -> dict:
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        m = json.load(f)
    m["contract_version"] = "1.1"
    m["tuning"].pop("freshness", None)
    return m


def setUpModule():
    d = tempfile.TemporaryDirectory()
    path = os.path.join(d.name, "contract_v11.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest_v11(), f, ensure_ascii=False)
    _state["dir"], _state["old"] = d, os.environ.get("CHONOI_CONTRACT")
    os.environ["CHONOI_CONTRACT"] = path


def tearDownModule():
    old = _state.pop("old", None)
    if old is None:
        os.environ.pop("CHONOI_CONTRACT", None)
    else:
        os.environ["CHONOI_CONTRACT"] = old
    _state.pop("dir").cleanup()
