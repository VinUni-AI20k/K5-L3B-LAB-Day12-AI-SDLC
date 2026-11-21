---
name: qa-verify-phase
description: Kiểm chứng một phase (test, smoke headless, nối kho, tất định) tại đúng commit sẽ gắn tag, lưu bằng chứng vào docs/proof/phase-N/ và cập nhật docs/verification/phase-N.md. Dùng trước khi Integrator gắn tag phase-N hoặc khi review PR đổi contract.
---

# QA: kiểm chứng phase N

Người giữ: `hungdt31` (QA Lead). Mọi bước đều chạy được trên Linux/macOS; Windows thay `python3` bằng `python -X utf8`.

## 1. Chọn đúng commit
- Kiểm tại commit **sẽ gắn tag**, không phải "main lúc này". Nếu `main` đang có việc dở của phase sau, dựng worktree riêng:
  `git worktree add --detach ../qa-pN <commit>` rồi làm các bước dưới trong đó.
- Ghi hash commit vào đầu `docs/verification/phase-N.md`.

## 2. Test tự động
```
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v > docs/proof/phase-N/unittest.log 2>&1
tail -3 docs/proof/phase-N/unittest.log      # phải là OK
python3 tools/check_team.py
```
Đỏ → **không** sửa test cho xanh; báo chủ lát (xem TEAM.md) và ghi vào mục "Phát hiện".

## 3. Smoke headless + tất định
```
for m in gather quan; do
  python3 -m chonoi.headless --mode $m --seed 1 --ticks 600 --out docs/proof/phase-N/smoke-$m.jsonl
  python3 -m chonoi.headless --mode $m --seed 1 --ticks 600 --out /tmp/again.jsonl
  cmp docs/proof/phase-N/smoke-$m.jsonl /tmp/again.jsonl && echo "$m tất định"
done
```
Từ Phase 2 thêm `--mode day --days 1..5`.

## 4. E2E nối kho (vòng chơi thật, không chỉ --ticks 0)
```
python3 -m chonoi.headless --mode gather --seed 42 --ticks 10800 --snapshot-every 60 \
  --inputs docs/proof/phase-N/e2e-gather-inputs.json --inventory-out docs/proof/phase-N/e2e-kho.json \
  --out docs/proof/phase-N/e2e-gather.jsonl
python3 -m chonoi.headless --mode quan --seed 42 --ticks 10800 --snapshot-every 60 \
  --inventory docs/proof/phase-N/e2e-kho.json --inputs docs/proof/phase-N/e2e-quan-inputs.json \
  --out docs/proof/phase-N/e2e-quan.jsonl
grep -o '"name":"[a-z_]*"' docs/proof/phase-N/e2e-quan.jsonl | sort | uniq -c
```
Kiểm: gather `reason: docked`, kho khớp giỏ, quan có `served`/`paid`/`quan_end`. Nếu contract đổi vị trí nút/cá, sinh lại file inputs (Phase 1 dùng planner đi lần lượt N1 → F1 → N3 → N4 → F4 → bến).

## 5. Commit bằng chứng
- `.gitignore` chặn `*.jsonl` → **bắt buộc** `git add -f docs/proof/phase-N/*.jsonl`, nếu không link trong bảng sẽ chết.
- Cập nhật ma trận `docs/verification/phase-N.md`: mỗi AC một dòng gồm cách kiểm, link bằng chứng và kết quả trung thực (đạt / chưa đạt).
- Thêm một dòng vào `docs/ai-usage-log.md`.
