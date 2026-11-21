# Kế hoạch Phase 3 (TV3)

- Mục tiêu: AC-P3-03 — kho cá thể quán, hao tươi, spoiled, giữ chỗ theo id, thử giữ lại / unfulfillable.
- Việc: `chonoi/freshness.py` · dual-mode `QuanSim` · `tuning.freshness` · test/proof `tv3-fresh-stock`.
- Phụ thuộc: TV1 adapter file + bump 1.2; TV4 chốt boa/day trên giá đã chốt; TV2 gather hold cá thể.
- Rủi ro: đụng `quan.py` / `scenario.py` với TV4; JSONL làm tròn fresh 3 chữ số.
