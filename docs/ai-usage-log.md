# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|

| 1 | czx04 | Claude Code (Opus 5.5) | Chốt docs/contracts + docs/clarify (bản nháp từ code khung, sau đối chiếu PRD-0); viết tests/test_gather.py; sửa test_team_check; README nhóm; điều phối Codex, gộp thử nhánh và kiểm test | chưa đo | Contracts nháp đoán sai data sự kiện trước khi PRD mở; đã sửa theo PRD-0 mục E |
| 1 | czx04 | Codex CLI 0.169 (codex exec) | Viết tests/test_quan.py, ma trận truy vết docs/verification/phase-1.md, tools/smoke_p1.sh | chưa đo | Fixture test quan khai tip: 0 cho khách chờ, lệch quy ước của sim/quan |
| 1 | czx04 | Codex CLI 0.169 (codex exec, read-only) | Review PR #3, #4 so với contracts | chưa đo | Gợi ý sai về node_yield (PRD ghi thêm 1 nguyên liệu) |
| 1 | czx04 | Codex CLI 0.169 (codex exec) | Soạn khung docs/members/* và nhật ký này từ git log | chưa đo | — |
| 1 | ToanLee5433 | Antigravity (Gemini) | Triển khai sim/gather; chốt contracts/clarify phase 1; sửa hồi chiêu và node_yield | ~45k tokens | AI tự ý gán hồi chiêu 30 tick khi giỏ đầy và hardcode thu hoạch 1 món thay vì lấy từ cấu hình |
| 1 | Ishodayo | Claude Code (Opus) | Đọc PRD-0, viết `chonoi/sim/quan.py`, phần kiểm scenario quán trong `chonoi/scenario.py`, `tests/test_quan_p1.py` ([PR #3](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/pull/3)); sau review cho AI viết test quét ~140 fixture sai kiểu (35b237f) | chưa đo | AI siết luật chặt hơn PRD: khách chưa phục vụ có `tip: 0` bị mã 2; bỏ sót kiểm kiểu `dish_id: []` gây crash mã 1. Cả hai lộ ra khi QA review PR #3. Nguồn: mục "Phần AI đã làm" của PR #3, `docs/members/Ishodayo.md` |
| 1 | itsbra1vo | GitHub Copilot | Client UI: HUD, thông báo sự kiện, điều khiển, hiển thị dữ liệu hai buổi trong `chonoi/web/index.html` ([7190e56](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/7190e56), PR #5) | chưa đo | AI sinh fallback giả định khóa snapshot luôn có và tên món trùng id nội bộ; phát hiện khi đối chiếu `/state` với hợp đồng. Nguồn: `Co-authored-by: Copilot` trong 7190e56, `docs/members/itsbra1vo.md` |
