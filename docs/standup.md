# Standup giữa phase (mỗi người một dòng, 2–3 phút)

| Phase | Người | Đã xong | Sắp làm | Vướng gì |
|---|---|---|---|---|
| 1 | 7 thành viên | Chốt contract 7 người, hoàn thiện logic 4 lát, HUD khung và QA | Gộp, chạy smoke headless, gắn tag | Cần xác nhận giả định team_size 7 theo clarify #1 |
| 1 | Quoosc (Q3, draft by Codex) | Added Q3 reservation helpers, hydration safeguards, elapsed schedule, random-arrival flag and patience/departure handling; Q3 tests and Q4 finding are being verified | Finish focused/regression/headless proof and hand off open decisions | PRD-0/Test Contract unavailable locally; D-01..D-09 remain provisional/open where source dependent |
| 1 -> 2 | ttkien0710 (Trần Trung Kiên) | Hoàn thành Lát 4 sim/quan (bếp, bưng, phục vụ, tip, uy tín), 7 tests pass, giải quyết conflict, PR #3 merged vào main | Nhận Lát 3b Phase 2 (2 bếp + 6 món) theo docs/plan/phase-2.md | Không |
| 2 | nganhduong123 (Nguyễn Ánh Dương, PO) | Client web Ticket-02 (menu, intro, pause, Shop, HUD) và vẽ lại cảnh lặn/quán đã vào main. 2 skill + script kiểm chứng. Kế hoạch chia việc P1–P4. Chơi thử live trên `81b5aab`: cảnh lặn chạy với cá bơi mới, không lỗi console. 96/96 test đạt | Ghi ADR 0002 lúc chốt kho cá thể, làm HUD độ tươi (AC-P3-09) bằng mock, nháp CHANGELOG, điều phối retro | UI Shop/`day` chỉ chạy được với mock vì `sim/day.py` chưa có. Chưa tag `phase-2` (contract v1.1 vừa vào main ở `b85711d`) |
