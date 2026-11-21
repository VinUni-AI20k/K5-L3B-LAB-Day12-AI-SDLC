# Phạm Trấn Quốc — Quoosc (bản nháp factual)

Q3 Phase 1: đóng góp logic khách, giữ chỗ, kiên nhẫn, test và [bằng chứng](../proof/phase-1/q3/README.md); review và ghi nhận món mồ côi Q4.

Q3 Phase 2: bổ sung menu_filter, order_tick và test; PR #8 đã merge. Review Q4 và ghi Q4-F1; kiểm sau merge trên main `63f850e`, kết quả và giới hạn tại [proof](../proof/phase-2/q3/postmerge-baseline-63f850e.txt).

Quốc cần tự xác nhận và bổ sung phản tư, trải nghiệm, bài học cá nhân trước khi nộp.

Q3 Phase 2: triển khai `no_dish` theo quyết định PO #11 trên nhánh `Quoosc`; kiểm chứng fixture bàn trống/bàn đầy, kho thiếu/filter rỗng, không backlog và không tăng ID. Xem [proof](../proof/phase-2/q3/no-dish.txt).

Phase 3: triển khai decay kho Quán bằng `Fraction`, reservation nguyên liệu cá thể theo ID tươi nhất, phát `spoiled`, nhả và thử giữ lại một lần. Test độc lập và giới hạn schema ghi trong [Spec Kit](../../specs/002-p3-q3-freshness/handoff.md).

Phase 4: viết CLI Soak dựa trên DaySim thật; chạy 10 ngày seed 7 hai lần, không crash và replay trùng gameplay fields. Số liệu thật cùng giới hạn chiến lược bot ở [proof](../proof/phase-4/soak-run.txt). Quốc cần tự xác nhận hai phần phản tư cá nhân về AI và điều học được.

Commits: [Q3 customer/freshness](https://github.com/invzble-z/K5-L3B-DAY12-AI-SDLC-NhomF7/commit/4a89104), [Soak](https://github.com/invzble-z/K5-L3B-DAY12-AI-SDLC-NhomF7/commit/4b38c16).
