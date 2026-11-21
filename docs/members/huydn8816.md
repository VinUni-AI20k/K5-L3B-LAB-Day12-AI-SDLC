# <github-handle> — phản tư cá nhân (≤ 200 từ)

- Tôi đã làm (kèm link commit): Tôi phụ trách UI và QA. Về QA, tôi viết test luật cho gather và quan (081d675), chuyển chúng sang schema kho cá thể (066a565), và viết test Phase 2 và Phase 4 (69b0efb, 1d37468). Về UI, tôi làm menu, tạm dừng, HUD sáng và tối, Shop, cảnh báo có biểu tượng và chế độ tương phản cao (9814e89, f1cd744). Tôi cũng viết chonoi/bench.py và chạy benchmark ba lần.
- Tôi đã review (kèm link): a515a0c (lát 1 gather, Vinh). Tôi đọc thứ tự xét dive/surface và ngất bỏ giỏ theo LIFO, và chạy test_rules_gather.py::Ngat (4 test đạt). Tôi chưa kiểm tra oxy kẹp biên.
- AI sai ở đâu và tôi phát hiện thế nào: AI viết test khi chưa đọc PRD-0, nên phải đổi nhiều test sau đó. Ảnh chụp đầu tiên cho thấy chữ đè nhau và cảnh báo khó đọc, tôi phát hiện bằng cách nhìn ảnh. Biểu tượng "🫧" hiện thành ô vuông trên máy tôi. Sau khi merge, dòng độ tươi đè danh sách đơn. Một test Cá Sấu đo quá lâu và báo đỏ sai.
- Điều tôi học được: Test xanh không đủ để biết giao diện đúng; phải nhìn thật. Đọc spec trước khi viết test tiết kiệm công sửa lại. Khi sửa test, phải ghi lý do và đối chiếu luật, không sửa cho xanh.
