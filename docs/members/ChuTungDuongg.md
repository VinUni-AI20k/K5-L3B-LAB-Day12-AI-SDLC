# ChuTungDuongg — phản tư cá nhân

- **Phần thực hiện** — Oxy theo độ sâu cuối bước, sự kiện lặn/nổi, ngạt và mất giỏ LIFO khi ngất. Bằng chứng nằm trong các commit [oxy](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/51cde51ad15dcda5076e115623a8bb0ddcce8e48), [ngạt và ngất](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/3b0c59ed557fb44fdba46273e8ba60fe9f4cfcf1) và [test](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/8f2d46224897d1a865521cb0dc06fcd360687834).
- **Phần rà soát** — Phiên Codex đối chiếu AC-P1-02/03 với JSONL và file kho thực tế. Suite chạy trên Windows với Python 3.13.9, đạt 44/44 test. Chưa có review của đồng đội tại thời điểm ghi.
- **Sai khác phát hiện khi dùng AI** — Ca nổi ban đầu đi qua ngưỡng, bỏ sót việc chạm đúng `0.5 m`. Rà soát tái hiện ngạt nhầm ở điểm này, dẫn đến sửa phép cộng độ sâu và thêm hai ca sát ngưỡng.
- **Điều rút ra** — Việc đếm cả bước oxy vừa cạn quyết định mốc `t+59`. Kiểm cả tọa độ chạm ngưỡng và tọa độ vừa sâu hơn giúp phát hiện sai phân loại mà snapshot làm tròn có thể che khuất.
