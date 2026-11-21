# Chợ Nổi (chonoi) Constitution

## Core Principles

### I. Contract-First (NON-NEGOTIABLE)
Mọi số liệu cân bằng đọc từ `game.contract.json` hoặc dữ liệu, không hard-code trong luật chơi.
`docs/contracts/`, `game.contract.json` và schema kho chỉ đổi khi báo cả nhóm và ghi lý do (ADR hoặc `docs/clarify.md`).

### II. Deterministic Simulation
Mọi số ngẫu nhiên đi qua `Streams` (`chonoi/rng.py`). Không dùng `random` toàn cục, không dùng đồng hồ hệ thống.
Sắp thực thể bằng `ids.sort_by_id`, cấp id bằng `IdAllocator`. Cùng seed phải ra cùng kết quả.

### III. Headless-First
Mỗi tính năng phải chạy được qua `python3 -m chonoi.headless --mode gather|quan` theo Test Contract.
Phần sáng tạo thêm phải tắt được ở headless và không phá phần cố định. Làm lõi đúng trước.

### IV. Test-First & Evidence
Mỗi Acceptance Criterion (`AC-P<phase>-<nn>`) có ít nhất một test hoặc scenario.
Test chạy: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`.
Không sửa test cho xanh khi luật sai. Nếu phải đổi test, ghi lý do trong commit.
Bằng chứng ghi ở `docs/verification/phase-<n>.md` và `docs/proof/`, trung thực kể cả phần chưa đạt.

### V. No Invented Requirements
Chỗ mơ hồ thì ghi `docs/clarify.md` và hỏi PO. Không tự bịa yêu cầu.
Khi spec còn `[NEEDS CLARIFICATION]` thì chưa được qua bước plan.

### VI. Small Verified Slices
Mỗi task/PR nhỏ (≤ ~400 dòng), một việc, một module. Người đọc lại diff trước khi đẩy.
Việc dùng AI ghi vào `docs/ai-usage-log.md`, kể cả chỗ AI làm sai.

## Ràng buộc bổ sung
- Công nghệ tự do. Starter Python trong `chonoi/` chỉ là gợi ý, hạn chế sửa khung của giảng viên.
- Asset ngoài chỉ dùng CC0/CC-BY/MIT hoặc tự tạo, ghi nguồn trong `CREDITS.md`. Không commit API key, token, `.env`.

## Quy trình phát triển
- Mỗi phase là một vòng SDLC đầy đủ: specify → clarify → plan → tasks → implement → verify. Kết thúc bằng tag `phase-<n>` chạy được.
- Cổng chất lượng trước khi gắn tag: test xanh, headless chạy được, ma trận AC↔bằng chứng đã điền.
- Phase sau phải kiểm tra lại phase trước (test ẩn có hồi quy).
- Chi tiết ánh xạ: `docs/sdlc-speckit.md`.

## Governance
Constitution này ưu tiên hơn mọi thói quen khác. Sửa constitution cần cả nhóm đồng ý, tăng version và ghi vào `CHANGELOG.md`.
Mọi plan và PR phải kiểm tra tuân thủ các nguyên tắc trên.

**Version**: 1.0.0 | **Ratified**: 2026-11-21 | **Last Amended**: 2026-11-21
