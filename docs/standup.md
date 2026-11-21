# Standup giữa phase (mỗi người một dòng, 2–3 phút)

| Phase | Người | Đã xong | Sắp làm | Vướng gì |
|---|---|---|---|---|
| Phase 1 | TV1 (Nguyễn Duy Mạnh) | Hoàn thiện sinh tồn ca sáng trong `chonoi/sim/gather.py` (lặn/nổi, oxy, ngạt, `choke`, `faint` bỏ giỏ LIFO và xuất kho rỗng), bổ sung 3 test headless `tests/test_gather_survival.py` (35/35 pass) và bằng chứng `docs/proof/phase-1/tv1-gather-survival.md` (commit `c8da6f5` trên `main`). | Ghép phần thu hoạch của TV2 vào `GatherSim.step`, phối hợp TV5 kiểm chứng smoke/HUD trên `main` cho mốc bàn giao Phase 1 và sẵn sàng sang Phase 2. | Không vướng; đang chờ hàm thu hoạch từ TV2 để ghép hoàn chỉnh ca sáng. |
