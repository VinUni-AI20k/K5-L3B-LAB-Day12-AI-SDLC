# Retro nhóm

## Phase 2 (nhanh)
- Điều tốt: Nền v1.1 của `LeBao403` vào `main` sớm nên `LaanLee`, `TheDLCrimson`, `baoduy2048` và `common-maker` làm song song trên cùng khung không phải sửa luật của nhau. Test sinh ra theo từng lát (213 test xanh) giúp phát hiện lỗi tích hợp rất nhanh. Smoke tích hợp `gather` -> `quan` và `--mode day` chạy dưới 1 giây, có bằng chứng trong `docs/proof/phase-2/`.
- Điều tệ: (1) 3 PR đầu của `TheDLCrimson` bị trùng với nền v1.1 của `LeBao403` (cùng làm lại hợp đồng) nên phải đóng và dựng lại. (2) `test_e_qa_p1` của `common-maker` đỏ trên `main` sau khi nền v1.1 vào vì còn đòi `contract_version` 1.0, và `common-maker` sửa chậm. (3) Tag `phase-1`, `phase-2` không được gắn đúng hạn (đến Phase 3 vẫn chưa có tag nào trên `origin`) và `TEAM.md` vẫn là bản mẫu. (4) Client web có lỗi cú pháp `continue` trong `forEach` làm màn hình đen cả hai chế độ, test Python không bắt được vì không có test chạy JS.
- 1 hành động cho Phase 3: **`common-maker`** thêm kiểm tra cú pháp JS cho `index.html` vào smoke (chạy trang bằng trình duyệt headless và đọc lỗi console) trước mỗi lần báo "xong HUD"; **`LeBao403`** gắn và đẩy tag `phase-1`, `phase-2` ngay đầu Phase 3 (đã ghi trong `PHAN-CONG-PHASE-3.md`); **cả nhóm** điền `TEAM.md` bằng tên thật trước khi gắn `phase-3`.

## Phase 3 (nhanh)
- Điều tốt: (ghi trong buổi retro sau khi gắn tag)
- Điều tệ: (ghi trong buổi retro sau khi gắn tag)
- Điều rút ra từ lần đổi kho đếm thành kho cá thể (`common-maker` ghi tạm, cả nhóm bổ sung): đổi schema kho ảnh hưởng mọi lát cùng lúc nên cách làm "hai phiên bản, manifest để 1.1 tới khi mọi lát chuyển xong" của `LeBao403` giữ `main` luôn chạy được. HUD đọc được cả hai dạng kho nên không bị chặn bởi tiến độ của lát khác. Test bàn giao v1.2 để dạng bỏ qua có điều kiện thay vì báo xanh giả khi sim chưa có độ tươi.
- 1 hành động cho Phase 4: (cả nhóm nhận khi retro)

## Phase 4 (cuối)
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
- Điều tốt / điều tệ:
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
- Một lần AI sai và cách nhóm phát hiện:
- Nếu làm lại, đổi gì:
