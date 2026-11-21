# Retro nhóm

## Phase 1

- **Điều tốt.** Kho mẫu và snapshot mẫu giúp Quán, UI và QA làm song song. Cả bốn module đã vào `main` qua bốn PR. Smoke seed 42 xác nhận hai tiến trình dùng chung đúng kho.
- **Điểm phát hiện muộn.** Suite tích hợp ban đầu xanh dù fixture rút ngắn ca làm khách đến sớm và món có thể kẹt sau khi khách rời. Một ca kiểm `TEAM.md` mẫu cũng phụ thuộc file đang chạy và lộ ra khi điền đủ handle.
- **Hành động cho Phase 2.** Khi thay đổi luật theo tick, thêm fixture cho đúng bước kết thúc và bước liền trước. Chạy `tools/phase1.py verify` trên bản tích hợp trước khi gắn tag.

## Phase 2

- **Điều tốt.** Gather và Quán chạy được trên preset tích hợp. Smoke bàn giao kho và hồi quy Phase 1 vẫn đạt. Preview cho phép UI kiểm luồng D1–D5 trong lúc chờ runner thật.
- **Điểm phát hiện khi gộp.** Manifest đã lên v1.1, còn CLI, parser input và validator giỏ vẫn có phần dùng quy ước v1.0. Chạy suite trên `main` phát hiện ba sai lệch ở `day`/Shop, pause và `keo_neo`. [Bằng chứng](proof/phase-2/integration.md#các-ca-chưa-đạt)
- **Hành động cho Phase 3.** Thêm smoke xuyên CLI → runner → live trên cùng commit khi đổi contract. Lượt kiểm đầu tiên chạy đúng ba ca đỏ Phase 2, rồi kiểm campaign qua `/config` và `/state`.

## Phase 4 (cuối)
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
- Điều tốt / điều tệ:
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
- Một lần AI sai và cách nhóm phát hiện:
- Nếu làm lại, đổi gì:
