# trongnghia2304 — phản tư cá nhân (≤ 200 từ)

**Phần tôi làm:** lát 3 quán (khách, giữ chỗ, kiên nhẫn) và PO cả buổi.
- P1: kế hoạch, khung hàm theo lát ([`cb2e298`](https://github.com/trongnghia2304/K5-L3B-LAB-Day12-AI-SDLC-ChoNoiCaMau/commit/cb2e298)); lát 3 + 13 test ([`d2aa684`](https://github.com/trongnghia2304/K5-L3B-LAB-Day12-AI-SDLC-ChoNoiCaMau/commit/d2aa684)).
- P2: lọc món theo kế hoạch Ngày ([`cc56062`](https://github.com/trongnghia2304/K5-L3B-LAB-Day12-AI-SDLC-ChoNoiCaMau/commit/cc56062)); ma trận verification ([`9babe80`](https://github.com/trongnghia2304/K5-L3B-LAB-Day12-AI-SDLC-ChoNoiCaMau/commit/9babe80)).
- P3: giữ chỗ theo id cá thể ([`f386fe8`](https://github.com/trongnghia2304/K5-L3B-LAB-Day12-AI-SDLC-ChoNoiCaMau/commit/f386fe8)); bật v1.2 trên `main`, sửa 5 test làm `main` đỏ ([`4a747e6`](https://github.com/trongnghia2304/K5-L3B-LAB-Day12-AI-SDLC-ChoNoiCaMau/commit/4a747e6)).
- P4: `live --mode day` + giao diện Shop ([`e46a9a4`](https://github.com/trongnghia2304/K5-L3B-LAB-Day12-AI-SDLC-ChoNoiCaMau/commit/e46a9a4)); điều phối retro.

**Đã giúp ai:** chép ticket, chia việc, chốt clarify cho cả nhóm; đóng bằng chứng Phase 2 khi QA sang Phase 3; sửa `day.py`/`shop.py` (Tiệp) chạy được v1.2.

**AI sai ở đâu:**
- Khung `step()` quán ban đầu sai thứ tự PRD; tôi đối chiếu mục F rồi sửa.
- Gộp `gather.py` sinh hao giỏ hai lần; grep tên hàm và chạy smoke ticket mới thấy.
- Giao diện đè chữ; chỉ lộ khi chơi thử và chụp ảnh.

**Bài học:** đổi hợp đồng phải đi cùng việc chuyển test, và tự chơi thử trước khi tin test xanh.
