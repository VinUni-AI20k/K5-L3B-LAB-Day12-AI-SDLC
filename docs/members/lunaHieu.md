# lunaHieu — phản tư cá nhân Phase 1 (Người 2)

- **Tôi đã làm:** Đặc tả Lát 2 ([b51820a](https://github.com/miao1114/K5-L3B-LAB-Day12-AI-SDLC-CodexGemini/commit/b51820a7a490180a7369caa7c59a0d9d96a07188)), triển khai hái/bắt/giỏ đầy ([79d3e92](https://github.com/miao1114/K5-L3B-LAB-Day12-AI-SDLC-CodexGemini/commit/79d3e92f2e289694c326fc029ae6d13ac6929fd5)), viết test và bằng chứng ([47e33c7](https://github.com/miao1114/K5-L3B-LAB-Day12-AI-SDLC-CodexGemini/commit/47e33c75605a33d907b25ad629eeb05e6156c005)). Link hoạt động sau khi push. Bổ sung README.
- **Tôi đã review:** Đọc PRD-0, Test Contract, `AGENTS.md`, hợp đồng kho và kiểm `git diff chonoi/sim/gather.py`: code chỉ đổi hai khối TODO Lát 2. Chưa review PR của người khác.
- **Kết quả kiểm chứng:** Lượt chạy toàn suite có 47 test, 46 đạt, 1 thất bại (`$LASTEXITCODE = 1`); 14/15 test Lát 2 đạt. Output thật ở [`../proof/phase-1/gather-collection-test.txt`](../proof/phase-1/gather-collection-test.txt).
- **Cần phối hợp:** Người 1 xử lý `choke`/`faint`, lưu `lost` theo LIFO và xóa giỏ trước `gather_end`. Chạy lại suite sau khi tích hợp.
- **AI sai ở đâu:** Codex từng thêm helper `_nearest()` ngoài hai khối TODO được giao; tôi phát hiện qua `git diff` và đã hoàn tác trước khi triển khai. Tôi học được cách chốt ranh giới sửa file và kiểm chứng cả event, file kho lẫn mã thoát.
