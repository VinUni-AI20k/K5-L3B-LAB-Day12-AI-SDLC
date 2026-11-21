# Phase 2 — Bàn giao backend của Vũ Văn Chủ (chur04)

Ngày: 21/11/2026. Baseline sau merge: `2ae7f6e`, nhánh hiện tại `2A202603873_VuVanChu`. Phân công: [phase-2.md](../../../plan/phase-2.md), nguồn: [TICKET-02](../../../prd-phase-2.md).

## Đã thực hiện

- Input v1.1, CLI day/days, vòng gather → quan → Shop trong 1–5 Ngày, kế hoạch và tính mục tiêu theo công thức, tiền/earned/uy tín xuyên Ngày.
- Shop oxygen/hp theo dữ liệu, mua đủ đúng giá, cấp tiếp theo, lỗi funds/max_level/unknown, mua trước đóng Shop, hết 600 tick hoặc shop_done, active_upgrades từ Ngày kế, bỏ kho dư.
- Pause ở cả ba mode: tick ngoài tăng, sim_tick/phase_tick/vị trí/timer/lịch khách đứng yên; resume chạy gameplay ngay, giữ nút không sinh cạnh mới, buy không bị giữ sang frame sau.
- Event/snapshot đúng ngữ cảnh day/phase, snapshot đổi pha ngay với phase_tick=0, chỉ tính Ngày khi Shop đóng. Ngất vẫn mở quán với kho rỗng.
- Quán chọn bàn trống id nhỏ nhất; dùng dữ liệu 2 bếp/4 bàn/6 món, trong day chỉ chọn id món của kế hoạch, không giới hạn số suất bán.
- Mở rộng burn có logic và test: >1200 tick mới cháy, nhả bếp, thử giữ nguyên liệu lại, không hoàn hàng, vẫn chờ nếu unfulfillable. Chưa bật trong manifest chung.

## Kiểm chứng thực tế

Chạy lại từ gốc repo bằng một lệnh:

```powershell
python tools/verify_chur04_phase2.py
```

Tool tạo bản sao package trong thư mục tạm và ghép [fixture dữ liệu chuẩn](../../../../tests/fixtures/phase2-day-data.json) vào manifest của bản sao. Không đổi game.contract.json trong repo. Các đầu ra JSONL dùng đuôi .txt để lưu được theo .gitignore hiện tại. Đây là kiểm chứng lát backend với random_fish=false và khách fixture/tắt tự sinh ở ca đo thời gian; chưa kiểm engine cá/quái v1.1.

- **104/104 test đạt**: 70 test baseline sau merge, 34 test mới. [Log đầy đủ](tests.txt).
- Hai tiến trình day cùng seed/input cho output giống từng byte. [Run 1](day-run1.txt), [run 2](day-run2.txt). SHA-256: `56b42d48b76d961fd6b2b526300ef3840e082c16fd87ea73f630e880db9cae4f`.
- Smoke 2 Ngày: dùng ca sáng/quán fixture mỗi pha 1 tick, mua oxygen với đúng 200, đóng Shop sớm; cấp có hiệu lực ở Ngày 2, kết thúc sau Shop thứ hai. money=0, earned=200, reputation=3, score=500, days_completed=2.
- Ca đủ **22.200 tick**, không pause, hoàn thành 1 Ngày: **dưới 20 giây**, có ghi JSONL qua CLI; thời gian đo chính xác nằm trong [summary.json](summary.json) và [log lệnh/thời gian](full-day.log). [Output](full-day.txt). Con số này chỉ đo fixture backend nêu trên, không đại diện hiệu năng toàn engine Gather sau tích hợp.
- Hai tiến trình gather → file kho → quan: kho tick 0 khớp `{"bong_sung":2,"ca_loc":1}`. [Kho](inventory.json), [gather](integration-gather.txt), [quan](integration-quan.txt).
- Skill nhóm [check-contract](../../../../.agents/skills/check-contract/SKILL.md) chạy `--local-python`: gather/quan output giống từng byte, PASS trên cấu hình gốc hiện tại.
- Windows vẫn có alias python3 không hoạt động. Tool thay đúng launcher đó sang sys.executable trong tiến trình chạy test cũ; không sửa assertion/test P1. Các smoke CLI trên bản sao dùng Python hiện có, không tuyên bố headless_cmd nguyên văn đã được xác nhận.
- Tóm tắt máy đọc được: [summary.json](summary.json). `git diff --check` đạt khi rà bàn giao.

## File và giao diện bàn giao

- day.py điều phối runtime, day_config.py kiểm tiền/cấp/kế hoạch/template; runner.py quản tick/pause/vỏ event; inputs.py và headless.py nhận giao diện v1.1.
- contract.py/scenario.py chỉ thêm các điểm nối cần cho day/Shop và nguyên liệu theo dữ liệu; vẫn cần Nhung ghép validation Gather v1.1 đầy đủ.
- gather.py chỉ thêm day=1 và self.day cho bố trí quái theo Ngày. Luật bơi/oxy/bắt cá/quái còn thuộc Khải/Nhung.
- Các chi tiết giao tiếp với Nhung/Đạt nằm ở [clarify Phase 2](../../../clarify.md).

## Chưa xác nhận / cần tích hợp

- Manifest chung vẫn v1.0, nên CLI thật ở gốc repo tiếp tục trả mã 2 cho mode day. Không tự thay cấu hình Nhung đang phụ trách. Bản sao kiểm chứng dùng [fixture-contract.json](fixture-contract.json).
- Gather v1.1 (fish_initial số 8, bơi/sinh cá, Cá Sấu và validation monsters/age_ticks), cập nhật inventory.py cho 6 nguyên liệu và UI/live day/Shop/pause phải được ghép trước khi chạy mặc định. Ca kiểm chứng tắt cá tự động, chưa có quái để kiểm.
- Chưa kiểm GUI/FPS, chưa xác nhận tag/DoD toàn nhóm, chưa có human review hoặc trao đổi giảng viên. Không sửa test gather P1 đang lệch PRD; Khải phụ trách chuẩn hóa và ghi lý do thay test.
- Chưa commit/push/tag mới; bằng chứng mô tả working tree, không giả nhận đây là kết quả trên commit gắn phase-2.
