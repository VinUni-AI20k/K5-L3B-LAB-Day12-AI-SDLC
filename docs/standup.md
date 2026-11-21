# Standup giữa phase (mỗi người một dòng, 2–3 phút)

> Phase 1: standup lúc ~0:30, TV6 bấm giờ. Mỗi người tự thêm dòng của mình (pull → thêm → push ngay). Ai vướng > 10' thì người dự phòng nhận ngồi cặp.

| Phase | Người | Đã xong | Sắp làm | Vướng gì |
|---|---|---|---|---|
| 1 | thanhhale288 (TV6) | Plan phase 1, thỏa thuận nhóm trong `TEAM.md`, danh sách câu hỏi `clarify.md`; chạy smoke test (32/32 OK) và `chonoi.live` (HUD đọc được oxy, Máu, giỏ) | Hỏi Anh Năm các câu `CHỜ HỎI`; kiểm HUD khi luật gather/quan xong; gom nhật ký AI; kiểm mỗi người có commit | Lab board (PRD-0) chưa đọc được bằng AI, phải đọc tay |
| 1 | thanhhale288 (TV6) — cập nhật | Spec Kit `specs/001-phase-1-core/` (spec, plan, tasks 36 task, analyze 0 CRITICAL); `docs/research/phase-1.md`; HUD gather/quan (32/32 test OK) | Đối chiếu giả định clarify #12–#22 với PRD-0; HUD T028–T032; kiểm mỗi người có commit | `team_size`=4 trong contract ≠ 6 người (TV1 sửa); TV1–TV5 chưa điền tên/handle trong `TEAM.md`; tên + `data` sự kiện chưa chốt (TV1 chép `specs/.../contracts/events.md` sang `docs/contracts/`) |
| 4 | thanhhale288 (TV6) | Brief + task P4, cảnh báo 3 loại + tương phản cao (`?demo=warn` / `?demo=warnq`, phím C), retro P4, member TV6 | TV1: `bench_cmd`/`soak_cmd` + tag `phase-4` + Release `v1.0.0`. TV5: chạy bench/regression. Mọi người: `docs/members/<handle>.md` | Contract chưa v1.3; T331 id xuyên Ngày chưa có; token AI chưa ai điền |
