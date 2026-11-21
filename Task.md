# Phân công công việc nhóm

> Phạm vi: Phase 1 (PRD-0), theo README và `docs/STARTER.md`. Chia theo bốn lát độc lập; tên thành viên chưa có trong `TEAM.md`, nên tạm gọi Thành viên 1–4. Hãy thay bằng GitHub handle sau kickoff và cập nhật module/vai trong `TEAM.md`.

## Thành viên 1 — Gather: sinh tồn, di chuyển và giỏ

- **Phạm vi:** `chonoi/sim/gather.py`, TODO lát 1.
- Cài oxy theo độ sâu ở cuối tick; sự kiện lặn/ngoi lên, oxy cạn, ngạt; HP và kết thúc `fainted` với giỏ bị mất; xử lý sức chứa và thứ tự LIFO của giỏ.
- Giữ nguyên luật di chuyển/ranh giới có sẵn, dùng số liệu từ tuning trong contract.
- **Bàn giao:** thay đổi code và ghi kiểm chứng liên quan trong `docs/verification/phase-1.md` hoặc `docs/proof/phase-1/`.

## Thành viên 2 — Gather: hái, bắt cá và cập bến

- **Phạm vi:** `chonoi/sim/gather.py`, TODO lát 2; phối hợp với Thành viên 1 để tránh sửa chồng cùng đoạn `step`.
- Hái nút khi ở mặt nước, bắt cá khi ở dưới nước và hết hồi chiêu; phát đúng event, xử lý giỏ đầy; ưu tiên cập bến trước hành động hái; cập nhật kho qua giao diện runner hiện có.
- **Bàn giao:** thay đổi code và bằng chứng kiểm chứng. Chốt thứ tự tick/event với Thành viên 1 trước khi ghép.

## Thành viên 3 — Quán: khách và vòng đời phục vụ

- **Phạm vi:** `chonoi/sim/quan.py`, TODO phần khách/lịch.
- Xử lý khách đến theo lịch, giữ chỗ, chọn món có nguyên liệu, kiên nhẫn và khách rời/no_dish; duy trì thứ tự xử lý theo PRD-0. Dùng `Streams`/`IdAllocator` cho ngẫu nhiên và ID nếu luật yêu cầu.
- **Bàn giao:** thay đổi code và kiểm chứng sự kiện/trạng thái khách; thống nhất event/interface với Thành viên 4 trước khi ghép.

## Thành viên 4 — Quán: bếp, bàn, thanh toán và tích hợp

- **Phạm vi:** `chonoi/sim/quan.py`, TODO tương tác và kết thúc ca; kiểm tra tích hợp các module.
- Thực hiện tương tác bếp/bàn, nấu và lấy món, phục vụ, ăn xong, thanh toán/boa/uy tín, hết ca; phối hợp dữ liệu kho từ gather.
- Sau khi ghép, rà soát `TEAM.md`, bằng chứng `docs/verification/phase-1.md`, rồi chạy lệnh test và headless dưới đây; ghi kết quả trung thực.
- **Bàn giao:** code và kết quả tích hợp cho nhóm review.

## Quy ước phối hợp

- Trước khi code, cả nhóm chốt `docs/contracts/README.md` (schema kho mẫu, giao diện sim/UI, tên event) và điền người/handle, vai trò trong `TEAM.md`.
- Contract `game.contract.json` là nguồn số liệu; không đổi contract, schema kho hay framework nếu chưa báo cả nhóm. Không dùng RNG toàn cục hoặc đồng hồ hệ thống; sắp entity bằng `ids.sort_by_id` và cấp ID bằng `IdAllocator`.
- Mỗi người tạo ít nhất 3 commit có nội dung theo README; commit làm cặp ghi `Co-authored-by:`. Review lát kế bên trước khi tích hợp.
- Việc nào chưa rõ yêu cầu: ghi vào `docs/clarify.md` để PO chốt, không tự đặt luật.

## Kiểm chứng Phase 1

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out out.jsonl
python3 -m chonoi.headless --mode quan --seed 1 --ticks 600 --out out.jsonl
```

Ghi kết quả và bằng chứng vào `docs/verification/phase-1.md` và `docs/proof/phase-1/`. Chạy headless riêng theo từng mode để giữ output dễ truy vết. Không sửa test chỉ để làm xanh; nếu test mâu thuẫn luật, sửa luật hoặc ghi rõ lý do thay đổi test.
