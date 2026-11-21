# SDLC ↔ Spec Kit trong dự án Chợ Nổi

## SDLC là gì
SDLC (Software Development Life Cycle) là vòng đời làm phần mềm: **Yêu cầu → Thiết kế → Lập kế hoạch/chia việc → Cài đặt → Kiểm thử/kiểm chứng → Phát hành → Rút kinh nghiệm**.
Spec Kit (Spec-Driven Development) làm cho *spec* là nguồn sự thật: spec sinh ra plan, plan sinh ra tasks, tasks sinh ra code. Với AI, việc này giúp agent không phải đoán yêu cầu.

## Mỗi phase của lab là một vòng SDLC

| Bước SDLC | Skill Spec Kit | Sản phẩm của Spec Kit | Đặt vào chỗ có sẵn của repo |
|---|---|---|---|
| Nguyên tắc / chuẩn | `/speckit-constitution` | `.specify/memory/constitution.md` | Nguồn của `AGENTS.md` (điểm Harness AI) |
| Yêu cầu | `/speckit-specify` | `specs/00N-*/spec.md` (user story, `FR-`, tiêu chí) | PRD của phase; AC đặt tên `AC-P<n>-<nn>` |
| Làm rõ | `/speckit-clarify` | mục Clarifications trong spec | Chép câu hỏi/đáp vào `docs/clarify.md` (PO giữ) |
| Thiết kế | `/speckit-plan` | `plan.md`, `data-model.md`, `contracts/` | Hợp đồng chốt ở `docs/contracts/`; quyết định lớn ghi `docs/adr/` |
| Chia việc | `/speckit-tasks` | `tasks.md` (có `[P]` = làm song song, theo story) | Mỗi task thành một issue (mẫu `.github/ISSUE_TEMPLATE/feature.md`); tóm tắt vào `docs/plan/phase-<n>.md` |
| Kiểm tra trước khi code | `/speckit-analyze`, `/speckit-checklist` | báo cáo nhất quán, checklist yêu cầu | Chạy trước `implement` |
| Cài đặt | `/speckit-implement` | code + test | PR nhỏ, mô tả theo `.github/pull_request_template.md` |
| Kiểm chứng | `/speckit-converge` + test | task còn thiếu so với spec | `docs/verification/phase-<n>.md` (ma trận AC → bằng chứng), `docs/proof/` |
| Phát hành | (git) | tag | `phase-<n>`, Release `v1.0.0` ở phase 4 |
| Rút kinh nghiệm | (tay) | | `docs/retro.md`, `docs/ai-usage-log.md` |

## Quy trình đề xuất trong 3 giờ
Mỗi phase dành khoảng 15–20% thời gian cho spec/plan, phần còn lại cho code và kiểm chứng.

1. **Kickoff (một lần, 15 phút):** chạy `/speckit-constitution` (đã có bản đầu), điền `TEAM.md`, chốt `docs/contracts/`.
2. **Đầu mỗi phase (~10 phút):** dán yêu cầu phase từ lab board vào `/speckit-specify`. Người PO chạy `/speckit-clarify`, ghi kết quả vào `docs/clarify.md`.
3. **Plan + tasks (~10 phút):** `/speckit-plan` với ràng buộc: "Python starter trong `chonoi/`, số liệu từ `game.contract.json`". Sau đó `/speckit-tasks` rồi `/speckit-analyze`.
4. **Chia việc song song:** mỗi thành viên nhận các task theo module (`sim/gather`, `sim/quan`, `client/ui`, `qa`). Task đánh `[P]` làm song song được. Chạy `/speckit-implement` cho từng nhóm task của mình.
5. **Cuối phase (~10 phút):** chạy test, `/speckit-converge`, điền `docs/verification/phase-<n>.md`, gắn tag `phase-<n>`. Việc chưa xong ghi trung thực.
6. **Yêu cầu đổi giữa chừng** (điểm "đổi yêu cầu"): sửa `spec.md` trước, chạy lại `/speckit-plan` và `/speckit-tasks`, rồi mới sửa code. Ghi vào `docs/clarify.md`.

## Cách chạy cho phase 1 (ví dụ)
```
/speckit-specify <dán PRD-0 phase 1: Út Sen lặn bắt cá, hái rau, kho ghi khi gather_end>
/speckit-clarify
/speckit-plan Python starter trong chonoi/, luật ở chonoi/sim/gather.py, số liệu từ game.contract.json
/speckit-tasks
/speckit-analyze
/speckit-implement
```

## Lưu ý
- Spec Kit mặc định tạo `specs/` và nhánh theo số. Repo này cho phép làm tự do về Git nên dùng được cả push thẳng lẫn nhánh ngắn.
- Đừng để spec dài như văn bản. Spec tốt ở đây là danh sách AC kiểm chứng được qua headless.
- Constitution là "luật" cho agent. Khi `AGENTS.md` đổi, cập nhật constitution cho khớp.
