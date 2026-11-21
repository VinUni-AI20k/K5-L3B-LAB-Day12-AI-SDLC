# Kiểm chứng Phase 3 · P3-05

Người 5 · UI/UX & Verification · 2026-11-21

| Hạng mục | Kết quả |
|---|---|
| HUD Gather và Quán | Hiển thị từng ID, tên và độ tươi. I2 ở 30% không có nhãn ươn, I9 ở 29,99% có nhãn **Ươn**. Hàng ươn vẫn chiếm một ô giỏ. [Ảnh Gather](../proof/phase-3/p3-05-gather.png). |
| Giữ chỗ | Chrome mở Quán thật với kho v1.2, kiểm tra nhãn **Đã giữ** trên đúng ID I7 khi khách đặt món và **Ươn** trên I8. |
| Chrome trên localhost | Đạt ở 1440, 1024, 768 và 390 px. Đã chạy WASD, Space, E cập bến và R trên Gather thật. Gather và Quán đọc kho cá thể từ `/state` thật. Snapshot mẫu kiểm tra ranh giới 30, giỏ rỗng rồi nhận lại cùng danh sách, kho trống và màn bàn giao buổi tối. [Log Chrome](../proof/phase-3/p3-05-browser.txt). |
| Bếp và bàn trên màn Quán | Nền sạch và sáu sprite riêng. Chrome kiểm tra đủ B1–B2 và T1–T4 ở bốn kích thước. Đổi tọa độ B2 và T3 trong snapshot chỉ làm hai sprite tương ứng di chuyển. [Ảnh Quán sau khi tách](../proof/phase-3/p3-05-quan-sprites.png). |
| Gather → file kho → Quán | Hai tiến trình headless giữ nguyên ID, loại và độ tươi từ `gather_end` qua file tới snapshot Quán ở tick 0. |
| Day Mode | Headless chạy hai ngày, kiểm tra kho ở tick đổi pha và ID tiếp tục tăng. Preview web dùng Gather/Quán thật, kiểm tra bắt cá, bàn giao kho, phục vụ, thanh toán và ca ngất. Tại màn bàn giao, hàng dưới 30 vẫn hiện trong kho và không được tính vào món có thể nấu. |
| Mô phỏng và Headless | Đọc `/state` trước khi cập bến cho cùng snapshot mô phỏng và cùng event như chạy đối chứng. Các trường hỗ trợ HUD chỉ có trong JSON live. [Log tích hợp](../proof/phase-3/p3-05-integration.txt). |

Đã chạy hồi quy trên nền `main` tại `e41536b` sau khi tích hợp hao tươi Gather, kho Quán và giữ chỗ theo ID. **203/203 test đạt.** [Log v1.2](../proof/phase-3/p3-05-v12-tests.txt).

## Chạy lại

PowerShell, từ thư mục repo. Công cụ kiểm thử trình duyệt dùng Playwright và Chrome.

```powershell
$env:PYTHONPATH = 'tests;.'
$env:PYTHONUTF8 = '1'
python -m unittest discover -s tests -v
py -3.14 tools/verify_p3_05_browser.py docs/proof/phase-3
```

Chạy riêng các ca headless bàn giao và Day.

```powershell
python -m unittest tests.test_inventory_v12 tests.test_phase2_live_preview tests.test_live -v
```
