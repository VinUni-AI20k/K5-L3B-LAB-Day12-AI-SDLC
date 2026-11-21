---
name: pre-push-check
description: Kiểm tra trước khi push. Dùng trước MỌI lần push, trước khi gắn tag phase-N, và ngay sau khi một agent sửa code (luật sim, test, contract). Chạy unit test, kiểm tra tất định của headless và mã thoát 2 khi đầu vào sai.
---

# pre-push-check

## Kiểm tra gì
1. **Unit test**: `PYTHONPATH=tests:. python3 -m unittest discover -s tests`.
2. **Tất định**: đọc `headless_cmd` từ `game.contract.json`, chạy mỗi mode `gather`, `quan` hai lần cùng seed (`--ticks 600`) rồi so byte bằng `cmp`. Khác nhau = có nguồn ngẫu nhiên/đồng hồ lọt ra ngoài `Streams`.
3. **Đầu vào sai**: `--ticks -1` phải trả **exit 2**.

## Lệnh (chạy từ gốc repo)
```bash
.agents/skills/pre-push-check/check.sh                         # chỉ in ra màn hình
SEED=7 .agents/skills/pre-push-check/check.sh                  # đổi seed (mặc định 1)
.agents/skills/pre-push-check/check.sh --save docs/proof/phase-1   # lưu bằng chứng
```

## Đọc kết quả
- Cuối output có mục **Tổng kết**: mỗi bước `[PASS]`/`[FAIL]`.
- `KẾT QUẢ: PASS` và exit 0 → được push. Bất kỳ `[FAIL]` nào → exit 1, **không push**.

## Khi FAIL
- Đọc log của bước lỗi (traceback unittest, dòng `cmp` khác byte, hoặc mã thoát thực tế).
- **Sửa luật** (`chonoi/sim/...`), **không sửa test cho xanh** (AGENTS.md). Nếu test thật sự sai, ghi lý do đổi test trong commit.
- Chỗ yêu cầu mơ hồ → ghi `docs/clarify.md`, hỏi PO.
- Chạy lại cho tới khi PASS.

## Bằng chứng
Trước khi push/tag phase-N, chạy với `--save docs/proof/phase-<n>/` để lưu `pre-push-check.txt` (kèm thời điểm, nhánh, commit) làm bằng chứng.
