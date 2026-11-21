# Kế hoạch Phase 1

Mục tiêu là chơi được buổi sáng và buổi tối qua cùng lớp mô phỏng, bàn giao nguyên liệu bằng file kho và kiểm tra cả hai tiến trình theo Test Contract v1.0. [Spec Phase 1](../../TEAM.md#phase-1)

| Module | Người phụ trách | Bàn giao và phụ thuộc |
|---|---|---|
| `sim/gather` | Nguyễn Trung Dũng | Bơi, oxy, hái, bắt cá và xuất kho cho Quán. [PR #4](https://github.com/lam2121/K5-L3B-LAB-Day12-AI-SDLC-NhomBaKhi/pull/4) |
| `sim/quan` | Nguyễn Văn Lâm | Chạy với kho mẫu, xử lý vòng đời khách và tiền, phát snapshot cho UI và QA. [PR #1](https://github.com/lam2121/K5-L3B-LAB-Day12-AI-SDLC-NhomBaKhi/pull/1) |
| `client/ui` | Nguyễn Duy Hưng | Dùng snapshot mẫu sớm, sau đó nối input, HUD và chuyển ca với live adapter. [PR #2](https://github.com/lam2121/K5-L3B-LAB-Day12-AI-SDLC-NhomBaKhi/pull/2) |
| `qa` | Đặng Nguyễn Nhật Minh | Dựng fixture, kiểm ca biên và đối chiếu file kho giữa hai tiến trình trên bản tích hợp. [PR #3](https://github.com/lam2121/K5-L3B-LAB-Day12-AI-SDLC-NhomBaKhi/pull/3) |

Rủi ro chính là sai thứ tự ở tick cuối, nhầm tồn vật lý với kho khả dụng và ghi kho khi chưa kết thúc Gather. Chạy `python3 tools/phase1.py smoke` sau thay đổi giao diện kho và `python3 tools/phase1.py verify` trước bàn giao. [Kết quả nghiệm thu](../verification/phase-1.md)
