# Bằng chứng Phase 1

Sinh bằng `python3 tools/proof_p1.py` ở commit **`7b1c895`**, lúc 2026-11-21 11:52. Code game, test và contract **giống hệt tag `phase-1`**.

| Kiểm chứng | File | Kết quả |
|---|---|---|
| Toàn bộ test (`unittest discover -s tests -v`) | [`tests-full.txt`](tests-full.txt) | Ran 88 tests in 7.763s · OK |
| Smoke dock → quán (PRD-0 G) | [`smoke/`](smoke/) | kho `{"bong_sung": 2, "ca_loc": 1}`, quán tick 0 `stock` `{"bong_sung": 2, "ca_loc": 1}` → ĐẠT |
| Chơi thật sáng (preset mặc định) | [`play/gather.jsonl.txt`](play/gather.jsonl.txt) | t148 gather, t161 dive, t239 fish_caught, t422 surface, t439 gather_end; end `docked`; kho `{"bong_dien_dien": 1, "ca_linh": 3}` |
| Quán đọc kho thật, trọn ca, không điều khiển (không ai nấu nên earned = 0, khách bỏ về) | [`play/quan.jsonl.txt`](play/quan.jsonl.txt) | end `time`, earned 0, uy tín 2.0, điểm 200 |
| Tất định: chạy lại cùng seed | `play/*-rerun*` | sha256 JSONL b66a796f31a0… = b66a796f31a0…, kho 453e124126ab… = 453e124126ab… → GIỐNG TỪNG BYTE |
| HUD sáng: thời gian, oxy, Máu, giỏ 12/12, `hold_full` ở N4 | [`hud-gather.png`](hud-gather.png) | có |
| HUD tối: thời gian, tiền, uy tín, điểm, kho, món khách gọi + thanh kiên nhẫn, bếp B1 đang nấu, log `customer_arrived`/`cook_started` | [`hud-quan.png`](hud-quan.png) | có |

## Ghi chú trung thực về HUD (chơi thử)

- HUD tối: nhãn món trên bếp B1 hiện `[object Object]`. `chonoi/web/index.html` in thẳng `stove.dish`, mà theo PRD-0 mục D đó là payload `{order_id, dish_id, base_price}`; cần in `dish.dish_id`.
- HUD tối in `stock` (tồn vật lý, gồm phần khách giữ chỗ) chứ chưa phải "kho khả dụng" theo PRD-0 §2.
- Cả hai lỗi chỉ ở hiển thị (file khung `chonoi/web/index.html`); luật, snapshot và JSONL vẫn đúng contract.
