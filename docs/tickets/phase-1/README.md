# Tickets — Phase 1

Spec: `docs/specs/phase-1.md` · Đặc tả khóa/payload: `docs/plan/phase-1-conformance.md` · Hợp đồng: `docs/contracts/README.md`.

Tracker dự kiến là GitHub Issues (mỗi file = 1 issue). Chưa tạo được từ máy này (không có `gh`/token):
mỗi người mở issue mới, dán nguyên nội dung file tương ứng, gắn nhãn `phase-1` + `ready-for-agent`.

| # | Ticket | Blocked by | Người |
|---|---|---|---|
| 01 | Prefactor + fixture contract | None | Cao Minh |
| 02 | Gather core | 01 | Cao Minh |
| 03 | Gather actions | 01 | Nhật Minh |
| 04 | Quan customers | 01 | Văn Minh |
| 05 | Quan service | 01 | Đức Minh |
| 06 | HUD hai buổi | None | Vinh |
| 07 | Verification pack | None (xanh sau 02–05) | Văn Minh |

Làm theo frontier: 01, 06, 07 mở ngay; xong 01 thì 02–05 mở cùng lúc.

**Nhịp tích hợp:** PR đợt 1 lúc **0:25**, đợt 2 lúc **0:40**, đợt 3 lúc **0:50** — không đợi tới cuối phase.
Merge theo thứ tự 01 → 02 → 03 → 04 → 05 → 06 sau mỗi đợt chạy lại toàn bộ test trên `main`.
