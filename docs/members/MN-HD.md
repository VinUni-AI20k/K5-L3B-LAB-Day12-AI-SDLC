# Đặng Nguyễn Nhật Minh · `MN-HD`

**Phase 1 · Bản nháp từ bằng chứng repo**

- **Đóng góp.** Thêm test ngất ở tick biên, kiểm fixture sai giữ nguyên đầu ra và ghi kết quả trên hai bản tích hợp. [Commit 6157804](https://github.com/lam2121/K5-L3B-LAB-Day12-AI-SDLC-NhomBaKhi/commit/6157804), [commit 7a3292b](https://github.com/lam2121/K5-L3B-LAB-Day12-AI-SDLC-NhomBaKhi/commit/7a3292b), [PR #3](https://github.com/lam2121/K5-L3B-LAB-Day12-AI-SDLC-NhomBaKhi/pull/3)
- **Kiểm chứng.** Ca ngất ban đầu thất bại trên nhánh QA và đạt sau khi chạy với Gather đã triển khai. [Bằng chứng QA](../proof/phase-1/qa.md)
- **Phản tư cá nhân.** Chờ Minh bổ sung phần đã review, công cụ AI đã dùng và bài học về chọn fixture.
# MN-HD — phản tư cá nhân

- **Tôi đã làm:** Viết hai ca QA hộp đen cho ngất đúng tick biên (`6157804`) và fixture sai giữ nguyên file đầu ra (`7a3292b`). Chạy full suite trên `main` tại `fdc986b`, đạt 45/45. [PR kiểm thử](https://github.com/lam2121/K5-L3B-LAB-Day12-AI-SDLC-NhomBaKhi/pull/3) · [PR bằng chứng](https://github.com/lam2121/K5-L3B-LAB-Day12-AI-SDLC-NhomBaKhi/pull/5).
- **Tôi đã kiểm chứng:** Chạy lại hai ca QA trên nhánh gather `cecbe8e`, rồi kiểm tra chúng trên `main` sau khi tích hợp. [PR gather](https://github.com/lam2121/K5-L3B-LAB-Day12-AI-SDLC-NhomBaKhi/pull/4).
- **AI sai ở đâu và tôi phát hiện thế nào:** AI hướng dẫn cập nhật ma trận trên nhánh PR #3. Khi đối chiếu SHA trên GitHub, PR đã merge ở commit trước bản cập nhật, nên ma trận cần PR #5.
- **Điều tôi học được:** Ghi rõ SHA và môi trường chạy để nhóm biết kết quả thuộc bản nào. Ca ngất từng fail trên bản cũ, sau đó pass trên nhánh gather và trên bản tích hợp.
