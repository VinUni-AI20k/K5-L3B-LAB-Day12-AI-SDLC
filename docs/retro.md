# Retro nhóm

## Phase 2 (nhanh)
Bản nháp của D (Integrator); TuHoAnh và Cuongngucuteee đã thêm phần của mình, A bổ sung hoặc sửa.
- Điều tốt:
  - Khóa contract v1.1 trước (P2-02) nên A, B, C làm song song ở file riêng (`fish.py`, `monsters.py`, `shop.py`, `quan.py`) mà ít đụng nhau; `main` luôn chạy được sau mỗi PR.
  - Phá thử code bằng cách sửa có chủ đích (mutation) bắt được lỗi test bỏ sót: ở `day.py` một cách phá sống sót (không lọc món theo kế hoạch) dẫn tới test mới; ở `monsters.py` kẽ hở "phát hiện khi đang nổi" được C vá sau review.
  - Smoke hộp đen (`smoke_phase2.py`) và `check_determinism.py` gồm `day` cho bằng chứng chạy thật, không chỉ test trong tiến trình.
  - **Cuongngucuteee:** P2-04 qua review của D chỉ sau một vòng (thêm test mặt nước); P2-08 có ảnh chụp trình duyệt thật làm bằng chứng và nhờ đó tìm ra lỗi ghi đè lệnh mua.
  - **TuHoAnh:** Hoàn thành `P2-05` đúng Test Contract v1.1 (2 bếp, 4 bàn, 6 món, lọc `allowed_dishes`), pass 193/193 test và `check_no_hardcode.py` sạch.
- Điều tệ:
  - Đề Ticket-02 không đọc được nên nhiều luật là giả định (`clarify` #7 đến #12) vẫn chờ PO; nếu đề khác thì phải sửa `monsters.py`, kế hoạch Ngày và test.
  - P2-08 (menu, pause, HUD) về sau nhất nên `chonoi.live` chơi được chế độ `day` rất muộn; ghi chép của A và C (nhật ký AI, hồ sơ) vẫn thiếu, B vẫn dùng tài khoản GitHub khác `TEAM.md`.
  - **TuHoAnh:** Ở Phase 1 bị conflict khi merge `origin/main` do chưa kéo `main` trước lúc làm nhánh nối; đầu Phase 2 hơi chậm nhịp khi chờ `game.contract.json` v1.1.
  - **Cuongngucuteee:** P2-04 và P2-08 vào `main` muộn (sau smoke phút 20); test ban đầu của tôi có kẽ hở (chỉ kiểm tick cuối) nên phải sửa sau review; chưa chơi tay trọn một Ngày bằng bàn phím; hồ sơ và nhật ký AI để tới cuối phase mới ghi.
  - D vẫn nhận phần việc lớn nhất (đa số commit, `day.py`, smoke, ma trận); AI của D tự sai ở chi tiết pause (nhầm số sự kiện) và chỉ lộ khi chạy thật.
- 1 hành động cho Phase 3: Phase 3 đổi schema kho (breaking, contract v1.2), nên trước khi viết code cả nhóm chốt các câu hỏi còn mở ở `docs/clarify.md` với PO và mỗi người ghi nhật ký AI, hồ sơ trong chính PR của task mình (không để dồn cuối phase).
  - **Cuongngucuteee:** Mỗi test luật mới phải phá thử ít nhất một lần trước khi mở PR; HUD độ tươi (AC-P3-05) đẩy sớm, trước smoke phút 20.
  - **TuHoAnh:** Luôn `git fetch` + `merge origin/main` và chạy đủ `unittest` + `check_no_hardcode.py` trước mọi lần mở PR.

## Phase 3 (nhanh)
A gom và nộp (P3-10). Phần của A đã được đối chiếu và cập nhật theo PR #45, #46 và kết quả phá thử. Phần của B do D soạn từ lịch sử PR và review, chờ B đọc lại.
- Điều tốt:
  - **Cuongngucuteee:** HUD độ tươi (P3-06) làm song song với gather và quán nhờ D gộp schema kho cá thể (P3-02) trước và ghi dạng snapshot trong hợp đồng; test dùng thẳng adapter của P3-02 nên không tự bịa dữ liệu.
  - **NguyenDucNhat3006 (A):** P3-03 đưa giỏ cá thể và kiểm tick cá vừa xuống dưới ngưỡng ươn. P3-05 nối kho Lặn → Quán cùng tick, giữ ID và độ tươi khi bàn giao. Shop giữ độ tươi, Ngày mới cấp ID mới. [PR #45](https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn/pull/45), [PR #46](https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn/pull/46)
  - **TuHoAnh (B, D soạn từ PR):** P3-04 có đủ luật quán v1.2 (hao kể cả hàng đang giữ, giữ chỗ theo id, nhả và giữ lại đúng một lần, `unfulfillable`, giá theo độ tươi); đã đổi tên hồ sơ thành `TuHoAnh.md` đúng yêu cầu.
  - **luongvh2510 (D):** Gộp schema, adapter và `freshness` vào `main` trước (P3-02) nên A, B, C làm song song mà ít xung đột; phá thử mỗi PR bắt được các chỗ test chưa chặt; bật 1.2 giữ hồi quy Phase 1-2 xanh (27/27, 15/15) nhờ chạy chúng với bản 1.1.
- Điều tệ:
  - **Cuongngucuteee:** Mã việc trên Sheet lệch 1 so với kế hoạch nên tôi đặt nhầm tên hai PR (#39, #42); chưa thử HUD với sim v1.2 thật vì quán chưa xong.
  - **NguyenDucNhat3006 (A):** Lúc mở #46, tôi mới kiểm bàn giao với Quán giả lập vì P3-04 chưa gộp. Lương phá thử và tìm được hai chỗ test còn lọt là sức chứa giỏ lúc dựng sim và việc sao chép kho khi mở Shop. Tôi cũng để dồn hồ sơ và nhật ký AI sang Phase 4. [Ma trận Phase 3](verification/phase-3.md)
  - **TuHoAnh (B, D soạn từ PR):** Đẩy nhánh P3-04 nhưng chưa mở PR nên Sheet ghi Xong sớm hơn thực tế; test lọt ba cách phá thử (`spoiled` phát lại mỗi tick, giữ chỗ chọn cũ nhất, nấu cả hàng ươn); báo lệch tên khóa `freshness` với đề muộn; chưa có nhật ký AI Phase 3.
  - **luongvh2510 (D):** Tôi đặt tên khóa `freshness` sai so với đề (P3-02) vì không đọc được Ticket-03; B phát hiện muộn nên phải sửa lại ở #48 và đổi code của B và C. Sheet và PR cũng lệch nhau (P3-04 ghi Xong khi chưa có PR); test của A và B còn lọt vài cách phá thử; payload `spoiled` của gather và quán khác nhau.
- 1 hành động cho Phase 4:
  - **Cuongngucuteee:** Trước khi làm, đối chiếu mã việc trên Sheet với commit đã gộp; khi A, B gộp v1.2 thì mở cửa sổ chơi chụp lại HUD độ tươi.
  - **NguyenDucNhat3006 (A):** Chạy đúng lệnh và tham số trong Ticket-04 trước khi mở PR benchmark. Ghi nhật ký AI ngay khi kết thúc từng việc để lưu được nhận xét từ review.
  - **TuHoAnh (B, D soạn từ PR):** Mở PR (kể cả bản nháp) ngay khi đẩy nhánh, và báo D ngay khi thấy đề khác với contract hay hợp đồng.
  - **luongvh2510 (D):** Trước khi khóa contract (v1.3, bench và soak), nhờ người đọc được Ticket-04 đối chiếu tên khóa và trường từng chữ; mỗi PR ghi rõ chỗ nào là giả định.

## Phase 4 (cuối)
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
  - **luongvh2510 (D):** Hành động tôi chốt cho Phase 3 là "chốt câu hỏi còn mở với PO và mỗi người ghi nhật ký AI, hồ sơ trong chính PR của task mình". **Chưa làm đủ:** không có kênh PO nên các dòng `clarify` vẫn là giả định (riêng Ticket-04 đã đối chiếu khi đọc được đề); A và B vẫn nộp nhật ký AI và hồ sơ dồn cuối. C đã làm đúng hành động của mình (HUD độ tươi đẩy sớm). Hành động của TuHoAnh (gộp `main` trước khi mở PR) cũng chưa thành thói quen: nhánh P3-04 của B phải được D gộp `main` hộ.
- Điều tốt / điều tệ:
  - **luongvh2510 (D):** Tốt: khóa contract và schema vào `main` trước để làm song song; phá thử mỗi PR; smoke hộp đen và CI Ubuntu cho bằng chứng ngoài máy Windows; mở đề Phase 4 trong trình duyệt giúp đối chiếu đúng và sửa kịp. Tệ: không đọc được Ticket-02 và Ticket-03 nên nhiều luật là giả định, tên khóa `freshness` sai một lần; tôi vẫn ôm 8 việc riêng cùng việc soạn thay và sửa nhánh của A và B, nên cân tải vẫn lệch.
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
  - **luongvh2510 (D):** Commit trên `main` (gồm cả commit gộp PR do GitHub tạo): D 115 (hai tên `luongvh2510` và `luongvh`, cùng email), C 23, A 11, B 8 (`HoAnhTu245` 7 và `TuHoAnh` 1), 9 của `Hai Duong` chưa rõ thuộc ai. Đọc code của nhau: D gộp thử và phá thử hầu hết PR; chưa thấy nhận xét review của A, B, C trên GitHub (C ghi review miệng). Token chưa đo.
- Một lần AI sai và cách nhóm phát hiện:
  - **luongvh2510 (D):** AI đặt tên khóa `freshness` theo trí nhớ (`fresh_max`, `units_per_point`, ...) vì không đọc được Ticket-03; B đọc đề và báo đúng 4 khóa khác tên, nên phải đổi ở #48 và sửa code của B và C. Phá thử không phát hiện được lỗi này vì test viết theo tên AI đã chọn; chỉ người có đề mới thấy.
- Nếu làm lại, đổi gì:
  - **luongvh2510 (D):** Xin hoặc dán đề của từng ticket vào repo ngay từ đầu để đối chiếu từng chữ; mỗi người ghi nhật ký AI và hồ sơ trong PR của mình; chia việc tích hợp đều cho cả nhóm thay vì dồn vào Integrator.

### Nguyễn Đức Nhật (A)

- **Rà hành động Phase 2:** Khi đổi kho ở Phase 3, phần Lặn và bàn giao được tách PR và có bằng chứng kiểm thử. Phần ghi chép cá nhân được bổ sung muộn hơn các PR tính năng.
- **Điều tốt:** Hai PR giỏ cá thể và bàn giao gộp đúng thứ tự. Lần chạy thử P4-10 gửi phím qua Chrome, kiểm được cá bắt ở Lặn sang Quán, nấu và bán món rồi mua oxy và đóng Shop. [PR #45](https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn/pull/45), [PR #46](https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn/pull/46)
- **Điều cần sửa:** Codex thử benchmark với `--seconds` theo kế hoạch nội bộ. Lương chạy lệnh đề, thấy `--duration` bị từ chối, rồi bổ sung cờ, 3 giây làm nóng và đo lại trước khi gộp. Lần sau tôi sẽ chạy đúng lệnh chấm như hộp đen trước khi mở PR. [Bản sửa P4-03](https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn/commit/e2a3b64)
