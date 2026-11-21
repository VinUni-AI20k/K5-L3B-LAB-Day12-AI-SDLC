# Standup giữa phase (mỗi người một dòng, 2–3 phút)

| Phase | Người | Đã xong | Sắp làm | Vướng gì |
|---|---|---|---|---|
| 1 | Đỗ Triệu Đức Phương - TV4 | Hoàn thành luồng nấu → bưng → phục vụ → thu tiền, gồm tính boa và quyết toán cuối ca. Cả 6 test headless của TV4 đạt, bộ test toàn dự án đạt 41/41 tại lần kiểm chứng. [Bằng chứng](proof/phase-1/tv4-bep-thanh-toan.md) | Ghép lịch khách của TV3 vào `QuanSim.step` và chạy thử ca tối từ lúc khách tự đến đến lúc trả tiền. | Bản hiện tại còn chờ tích hợp lịch sinh khách của TV3. Luồng TV4 đã kiểm chứng bằng khách dựng sẵn. |
| 1 | Nguyễn Duy Mạnh - TV1 | Hoàn thiện sinh tồn ca sáng trong `chonoi/sim/gather.py` (lặn/nổi, oxy, ngạt, `choke`, `faint` bỏ giỏ LIFO và xuất kho rỗng), bổ sung 3 test headless `tests/test_gather_survival.py` (35/35 pass) và bằng chứng `docs/proof/phase-1/tv1-gather-survival.md` (commit `c8da6f5` trên `main`). | Ghép phần thu hoạch của TV2 vào `GatherSim.step`, phối hợp TV5 kiểm chứng smoke/HUD trên `main` cho mốc bàn giao Phase 1 và sẵn sàng sang Phase 2. | Không vướng; đang chờ hàm thu hoạch từ TV2 để ghép hoàn chỉnh ca sáng. |
