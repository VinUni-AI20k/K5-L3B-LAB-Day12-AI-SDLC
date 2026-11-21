# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| | 2026-11-21 Phase 2 | `fish_initial` "là số 8": 8 đàn đầu ca đặt cố định hay theo seed? | Giả định: `fish_initial` là số đàn; đầu ca chạy đúng thủ tục sinh cá 8 lần (loài theo trọng số, điểm đều, hướng theo seed, cách nhau > 1 m), id F1–F8, không phát `fish_spawned`. Vì chọn theo trọng số nên một seed có thể không có đủ 3 loài lúc đầu ca. | qavu2407-lang (chờ PO hỏi Anh Năm) |
| | 2026-11-21 Phase 2 | "Đổi hướng theo seed": chọn hướng mới thế nào? | Giả định: góc đều trong [0°, 360°) từ luồng RNG `fish_turn`; hướng ban đầu khi sinh lấy từ luồng `fish_spawn`. | qavu2407-lang |
| | 2026-11-21 Phase 2 | "Tới mép" có tính đúng mép không? | Có: vị trí sau bước ≥ mép trên hoặc ≤ mép dưới thì phản xạ phần còn lại và đảo thành phần vận tốc (đúng mép thì phần còn lại = 0). | qavu2407-lang |
| | 2026-11-21 Phase 2 | Scenario khai cá ngoài miền bơi của loài? | Khi `random_fish` bật (cá có bơi): ngoài `fish_x` hoặc dải độ sâu của loài → mã 2. Khi `random_fish: false` cá đứng yên nên chỉ cần ở dưới nước như v1.0. | qavu2407-lang |
