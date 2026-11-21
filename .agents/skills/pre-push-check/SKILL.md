---
name: pre-push-check
description: Kiểm trước khi push hoặc gắn tag trong repo Quán Ăn Chợ Nổi — chạy toàn bộ unittest, smoke headless gather/quan/day (một Ngày ≤ 20 s), kiểm game.contract.json, danh sách thành viên, cú pháp JS của client/ và file nhạy cảm bị commit; in tóm tắt để dán vào mô tả commit. Dùng mỗi khi sắp git push, sắp gắn tag phase-n, hoặc khi agent báo "xong" một lát.
---

# pre-push-check — kiểm trước khi đẩy

Nhóm đã từng: test headless xanh nhưng client vỡ, agent báo "xong" khi chưa chạy đủ, đẩy lên khi chưa chạy test.
Skill này gom mọi bước kiểm tự động vào **một lệnh** và nhắc bước phải làm bằng tay.

## Khi nào dùng
- Ngay trước `git push` lên `main` hoặc trước khi gắn tag `phase-n` / `v*`.
- Khi agent (hoặc người) báo xong một lát — "xong" chỉ tính khi lệnh này thoát mã 0.

## Cách chạy (từ gốc repo)
```bash
python3 .agents/skills/pre-push-check/check.py              # đủ bước (bắt buộc trước khi push)
python3 .agents/skills/pre-push-check/check.py --no-tests   # bỏ unittest, chỉ khi đang sửa lặp nhanh
```
Windows: thay `python3` bằng `python`.

## Lệnh này kiểm gì
| Bước | Đạt khi | Hỏng thì |
|---|---|---|
| contract | `chonoi.contract.load_contract()` đọc được `game.contract.json` | FAIL — sửa contract trước, báo cả nhóm |
| team | `tools/check_team.py` đạt | WARN (CI cũng chỉ cảnh báo) — commit của người không có trong `TEAM.md` không được tính |
| unittest | `PYTHONPATH=tests:. python3 -m unittest discover -s tests` OK | FAIL — sửa luật, **không** sửa test cho xanh |
| headless | gather/quan 600 tick và day 1 Ngày (22.200 tick) thoát 0, dòng cuối là `end`, day ≤ 20 s | FAIL |
| client-js | `node --check` mọi `client/src/*.js` (bỏ qua nếu máy không có node) | FAIL — client sẽ đứng ở "Đang tải…" |
| git | không track `.env`, khóa, `__pycache__`, `*.pyc`; không có chuỗi giống token; không file > 10 MB | FAIL/WARN |

Cuối cùng lệnh in một dòng **"Kiểm trước khi đẩy: …"** để dán vào mô tả commit (AGENTS.md yêu cầu ghi kết quả test).

## Bước tay (lệnh không làm thay được)
1. **Nếu đổi `client/`:** chạy `python3 -m http.server 8099` ở **gốc repo** (không chạy trong `client/`,
   không dùng cổng 8000 vì `chonoi.live` chiếm), mở `http://127.0.0.1:8099/client/`, nhấn Ctrl+F5,
   chơi hết vòng lặn → quán → chợ. Mở F12 → Console: không có lỗi đỏ, không có 404.
2. Đọc lại `git diff --staged`: chỉ có phần việc của mình, không lẫn file người khác đang sửa.
3. Commit bằng tài khoản của chính người làm (commit từ máy ai thì tính cho tài khoản người đó).

## Quy tắc
- Lệnh thoát mã 1 thì **không push**. Ghi lý do vào `docs/clarify.md` nếu nghi ngờ test sai so với ticket.
- Không dùng `--no-tests` cho lần chạy cuối trước khi push.
- Agent chỉ commit/push khi người phụ trách yêu cầu rõ.
