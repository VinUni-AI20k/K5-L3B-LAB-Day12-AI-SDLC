# AGENTS.md

Lab Day 12 — Quán Ăn Chợ Nổi. Python thuần (stdlib), contract **v1.1**, `phase-1` đã tag.

## Trước khi viết

- Đọc spec của phase (`docs/specs/phase-<n>.md`) và ticket của lát mình (`docs/tickets/phase-<n>/`).
- Số liệu đọc từ `game.contract.json`. Ngẫu nhiên qua `Streams`. Danh sách thực thể sắp bằng `sort_by_id`.
- Sửa file của mình; file chia sẻ (`chonoi/contract.py`, `chonoi/scenario.py`, `chonoi/runner.py`) thì báo Integrator trước.

## Trước khi commit

- `python3 tools/run_checks.py` phải PASS: unittest, smoke hai tiến trình, tất định byte, bằng chứng.
- Test đổi vì luật đổi thì ghi lý do trong commit.
- Kết quả chạy ghi vào mô tả commit hoặc `docs/proof/phase-<n>/`.

## Khi cần tra

- Hợp đồng kho, tên event, giao diện sim↔UI: `docs/contracts/README.md`.
- PRD chỗ mơ hồ: `docs/clarify.md` trước, hỏi PO sau.
- Luật chơi: `chonoi/sim/` (gather, quan, quan_customers, quan_service, monsters, day, fish, shop).
- Trạng thái từng AC: `docs/verification/phase-<n>.md`. Claim "đạt" phải có file thật trong `docs/proof/`.

## Lệnh

- Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests`
- Chơi: `python3 -m chonoi.live --mode gather|quan|day` (WASD, E, Space, R, C tương phản, `?fx=0` tắt hiệu ứng)
- Headless: `python3 -m chonoi.headless --mode day --days 2 --seed 7 --out day.jsonl`
- Cổng kiểm: `python3 tools/run_checks.py` · Tiến độ nhánh: `python3 tools/team_progress.py`
- Bench: `python3 tools/bench.py --seed 42 --duration 30 --out bench.json` (cần Playwright hoặc obscura)

## Skill

`.agents/skills/gate/` (cổng kiểm + tag) · `.agents/skills/probe/` (dựng ca kiểm headless hoặc live UI).
