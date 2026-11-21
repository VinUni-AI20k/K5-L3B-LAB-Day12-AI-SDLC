# Kế hoạch Phase 4 — Phát hành v1.0.0 (TICKET-04, contract v1.3)

Hạn: tag `phase-4` + GitHub Release v1.0.0 cùng một commit trên `main`, 3:00. Điều kiện trước: phase 3 trên main + tag `phase-3`.
**Quy tắc:** mỗi người chỉ sửa file mình giữ (AGENTS.md "Nên tránh").

| Người | Vai | Việc | File giữ |
|---|---|---|---|
| itsbra1vo (Thái) | Bench + cảnh báo | `bench_cmd` cảnh lặn 1280×720, seed 42, làm nóng 3 s, đo 30 s → `bench.json` (avg_fps, p1_low_fps, frames, measured_s, load_ms); 3 cảnh báo chữ/biểu tượng (thủy quái gần, oxy sắp hết, khách sắp giận); chế độ tương phản cao, chơi thử, ảnh vào `docs/proof/phase-4/` | `chonoi/web/index.html`, `chonoi/live.py`, `tools/bench.py` |
| ToanLee5433 (Toan) | Contract + soak + Release | `contract_version "1.3"`, `bench_cmd`, `soak_cmd`; soak bot tất định 10 Ngày (D1–D5 lặp) → `soak.json`; release notes, tag `phase-4`, GitHub Release v1.0.0 kèm gói | `game.contract.json`, `chonoi/contract.py`, `tools/soak.py`, `CHANGELOG.md` |
| Ishodayo (Nam) | Đóng gói + QA regression | Thử clone sạch ≤ 3 lệnh, sửa README; gói zip; CREDITS + LICENSE; regression P1–P3; `docs/verification/phase-4.md` | `README.md`, `LICENSE`, `CREDITS.md`, `docs/verification/phase-4.md`, `docs/proof/phase-4/` |
| czx04 (Hùng) | PO + retro + review | Hỏi Anh Năm, clarify; retro rà hành động P2/P3 + 1 lỗi AI và cách xác minh; review PR | `docs/clarify.md`, `docs/retro.md`, `docs/ai-usage-log.md` |
| Cả 4 | | `docs/members/<handle>.md` (≤ 200 từ) + dòng ai-usage-log phase 4 của mình | file của mình |

**Lịch:** 0–15' Toan đẩy contract v1.3 sớm · Thái bench + cảnh báo · Nam clone sạch + regression. 15–25' merge vào dev · Nam smoke + bench trên bản tích hợp · Hùng chốt retro · phản tư. 25–30' dev → main · Nam bench + test trên đúng commit, commit bằng chứng · Toan tag `phase-4` + Release v1.0.0 sau commit bằng chứng.

Mở rộng (leaderboard, phụ đề SFX): không làm (nhóm 4 người không bắt buộc).
