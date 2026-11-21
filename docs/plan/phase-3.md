# Kế hoạch Phase 3 (≤ 1 trang)

- **Mục tiêu:** Nâng game lên **Test Contract v1.2 (Ticket-03 "Mùa Nước Nổi")** trong 35 phút (`1:55–2:30`): kho đếm thành **kho cá thể** `{"id","kind","fresh"}`, độ tươi hao theo giỏ/kho, hàng ươn (`fresh < 30`), giữ chỗ theo id, giá theo độ tươi, `contract_version: "1.2"` + khối `freshness`. Phần của `common-maker` (QA lead + HUD): HUD cho đọc độ tươi và nhận ra hàng ươn, smoke bàn giao kho cá thể, sửa test chung theo v1.2, CHANGELOG, `docs/verification/phase-3.md`, retro, và ghi trung thực việc tag `phase-1`, `phase-2` gắn trễ.

- **Bảng đầu việc theo AC (phần của `common-maker` in đậm):**

| Mã AC | Nội dung chính | Phụ trách | Phụ thuộc |
|---|---|---|---|
| `AC-P3-01` | Tag `phase-1` (`759caeb`), `phase-2` (`main`), ADR 0001, bảng tác động | `LeBao403` | — |
| `AC-P3-02` | Nền v1.2 hai phiên bản: `fresh.py`, đọc/ghi kho theo `contract_version`, `freshness`, scenario `hold`/`stock` cá thể | `LeBao403` | `AC-P3-01` |
| `AC-P3-03` | Giỏ cá thể: `_try_harvest`, `_try_catch`, hao tươi giỏ 0.5/s, `spoiled{location: hold}`, sức chứa tính cả hàng ươn | `LaanLee` | `AC-P3-02` |
| `AC-P3-04` | Giữ chỗ theo id (tươi nhất, hòa id nhỏ), `_rereserve_spoiled`, `unfulfillable`, `day.py`/`shop.py` bàn giao cá thể, id xuyên Ngày | `TheDLCrimson` | `AC-P3-02` |
| `AC-P3-05` | Kho quán hao 0.25/s, `spoiled{location: stock}`, nấu tiêu đúng id, giá `price × TB fresh / 100`, boa trên giá chốt | `baoduy2048` | `AC-P3-02`, `AC-P3-04` |
| `AC-P3-06` | Bật `contract_version: "1.2"` + khối `freshness`, kho đếm trả mã 2, chuyển test của A sang cá thể | `LeBao403` | `AC-P3-03`..`05` |
| **`AC-P3-07`** | **HUD độ tươi:** ô giỏ có thanh `fresh` đổi màu gần 30 và nhãn "ƯƠN" khi < 30, dòng "Độ tươi kho" ở quán, kho khả dụng chỉ tính hàng chưa ươn, chưa giữ; đọc được cả kho đếm (v1.1) | **`common-maker`** | dữ liệu giả (`?demo=fresh`) → nối `AC-P3-06` |
| **`AC-P3-08`** | **Smoke bàn giao kho cá thể** (fixture `I1 ca_linh fresh 100`, `--inventory-out` rồi `quan --inventory --ticks 0`, so id/kind/fresh), `skill smoke-p3`, `tests/test_p3_hud_qa.py` | **`common-maker`** | `AC-P3-06` |
| **`AC-P3-09`** | **Sửa test chung theo v1.2** (`test_smoke_p1.py`, `test_e_qa_p1.py`), mỗi chỗ ghi lý do trong commit | **`common-maker`** | `AC-P3-06` |
| **`AC-P3-10`** | **CHANGELOG** breaking change (kho đếm → kho cá thể, cách cập nhật fixture) | **`common-maker`** | `AC-P3-02` |
| **`AC-P3-11`** | **Smoke `--mode day --days 1`**, regression P1-P2, `docs/verification/phase-3.md`, retro, ghi chú tag gắn trễ vào verification P1/P2 | **`common-maker`** | `AC-P3-03`..`09` |
| `AC-P3-12` | DoD: bằng chứng khớp commit gắn tag, `ai-usage-log`, `clarify`, tag `phase-3` trên `main` trước 2:30 | cả nhóm | tất cả |

- **Mốc phối hợp (35 phút):** `1:55–2:02` tag P1/P2, ADR, plan; `2:02–2:07` A đẩy nền v1.2 hai phiên bản (**đã vào `main`, PR #20**); `2:07–2:20` B, C, D chuyển lát, E làm HUD; `2:15` smoke bàn giao kho + standup; `2:20–2:22` A bật `contract_version 1.2`; `2:22–2:27` smoke file + day, regression, CHANGELOG, verification, tag.

- **Rủi ro và giảm thiểu:**
  - *Test bàn giao v1.2 không thể xanh khi các lát B/C/D chưa gộp:* test v1.2 trong `test_p3_hud_qa.py` tự bỏ qua khi manifest còn 1.1 (không báo xanh giả); khi A bật 1.2 thì chạy thật. Nếu đỏ thì đó là tín hiệu thiếu lát, không sửa test cho xanh.
  - *HUD phụ thuộc định dạng snapshot chưa chốt hẳn:* client đọc cả hai dạng (chuỗi/số đếm và `{id,kind,fresh}`), ngưỡng 30 đặt một chỗ (`SPOILED_BELOW`), có chế độ `?demo=fresh` để QA xem HUD khi sim chưa có độ tươi (mặc định tắt, không đụng headless).
  - *Tag `phase-1`, `phase-2` gắn trễ:* ghi trung thực vào `docs/verification/phase-1.md`, `phase-2.md` kèm phần chưa đạt tại tag.
  - *`TEAM.md` vẫn là mẫu (`check_team.py` mã 1):* nhóm phải điền tên thật và handle; E không tự bịa tên.
