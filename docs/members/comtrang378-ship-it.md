# Nguyễn Anh Tú — comtrang378-ship-it · MSSV 2A202604088

## Vai trò

Dev gather lát 1: oxy, ngạt, Máu, ngất; phụ trách `sim/gather.py`, `sim/monsters.py` và phần bàn giao kho cá thể khi ngất.

## Phase 1–4

- Hoàn thiện logic Gather Phase 1 gồm oxy, lặn/lên mặt, ngạt, Máu và ngất ([`7af1a49`](https://github.com/invzble-z/K5-L3B-DAY12-AI-SDLC-NhomF7/commit/7af1a49)).
- Hoàn thiện Cá Sấu, Máu, ngất và bất tử sau hit ([`8251ef0`](https://github.com/invzble-z/K5-L3B-DAY12-AI-SDLC-NhomF7/commit/8251ef0)); nối pha ngày đêm ([`6e5cd3c`](https://github.com/invzble-z/K5-L3B-DAY12-AI-SDLC-NhomF7/commit/6e5cd3c)).
- Tham gia mở rộng/luyện tập tích hợp kho và dữ liệu; kiểm tra cảnh báo, thủy quái và tương phản cao theo [AC-P4-04](../verification/phase-4.md).

## AI và bài học

Tôi đã phát hiện và sửa xung đột merge để giữ lại mô phỏng Cá Sấu thay vì làm mất logic hiện có. Trong quá trình làm, tôi học được cần chạy test sau mỗi merge, giữ contract/Streams/`sort_by_id` nhất quán và kiểm tra cả luồng headless lẫn giao diện.
