# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| Phase 1 | Vũ Huy Hiệu (`hieunhangia`) | Gemini 3.8 Flash (High) | Khởi tạo TEAM.md 6 người, cập nhật contract team_size, chốt hợp đồng tích hợp docs/contracts, thiết lập AI skills & quy tắc AGENTS.md | ~25,000 tokens | AI ban đầu tự động gợi ý các SOP cồng kềnh ngoài luồng; đã yêu cầu gác lại để bám sát Test Contract của giảng viên. |
| Phase 1 | Phạm Lý Ngọc Đức (`Ducbaynao`) | Codex / GPT-6 | Tôi dùng AI đọc repo và phân công TV2, triển khai Gather Core, bổ sung 13 test, chạy headless và soạn hồ sơ bàn giao. Tôi đối chiếu kết quả với contract, mã runner và log thực chạy. | Không có số liệu token/chi phí được cung cấp; tôi không tự ước lượng. | Lệnh test ban đầu vướng alias `python3` và mã hóa Windows. Tôi dùng launcher tạm cùng UTF-8 để chạy đúng suite, giữ nguyên contract và test hộp đen. Không ghi nhận lỗi luật còn tồn tại trong phạm vi đã kiểm chứng; tính năng TV3 chưa được coi là hoàn thành. |
