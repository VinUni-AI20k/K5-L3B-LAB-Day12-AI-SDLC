# TEAM

**Tên nhóm:** 439  **Số người:** 5  (khớp `team_size` trong `game.contract.json`)

| Thành viên | GitHub handle | Module chính | Vai quy trình | Người dự phòng cho |
|---|---|---|---|---|
| TV1 (Lead) | phong | `sim/gather` | Team Lead, PO/Integrator | TV2 |
| TV2 (Gather) | thangdktd | `sim/gather` | Developer Gather | TV1 |
| TV3 (Quán) | daohiep2903 | `sim/quan` | Developer Quán | TV4 |
| TV4 (Quán) | NTLam108 | `sim/quan` | Developer Quán | TV3 |
| TV5 (QA/HUD) | vuhieuvh | `qa` | QA Lead + HUD | TV1 |

**Vai quy trình:** PO (đầu mối hỏi giảng viên, giữ `docs/clarify.md`) · Integrator (giữ `docs/contracts/`, gắn tag) · QA lead · Scrum/Release. Có thể kiêm.

## Thỏa thuận làm việc nhóm (chốt T+0–15)

- Kênh liên lạc: Discord / Zalo 439.
- Khi bất đồng về thiết kế: Trao đổi nhanh ≤ 2 phút; nếu chưa thống nhất thì Integrator (TV1) quyết định theo Test Contract và ghi lại lý do.
- Khi ai đó trễ hoặc vướng quá 10 phút: Báo ngay lên kênh chung, người dự phòng lập tức nhận việc hỗ trợ.
- Giờ standup: T+20 rà soát blocker giữa Phase 1.
- Phân chia quyền sở hữu file: TV1/TV2 phụ trách `gather.py`, TV3/TV4 phụ trách `quan.py`, TV5 phụ trách test/HUD/docs.
- Cách làm việc với Git: Mỗi người code trên lát của mình, rebase/merge vào `main`, TV1 kiểm tra tích hợp và gắn tag `phase-1` trước T+60.
