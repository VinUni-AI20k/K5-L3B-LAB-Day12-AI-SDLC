# Bằng chứng cảnh báo, tương phản cao và phụ đề SFX (Phase 4)

Người làm: tiepnnk01-10 · AC-P4-04 (3 cảnh báo), AC-P4-05 (tương phản cao), AC-P4-10 (phụ đề SFX khi tắt tiếng).
Chụp ở cửa sổ 1280×720 từ `python3 -m chonoi.live` thật (không phải mô phỏng), trình duyệt Chrome.

| Ảnh | Cho thấy | AC |
|---|---|---|
| [canh-bao-sang-binh-thuong.png](canh-bao-sang-binh-thuong.png) | Cảnh lặn: **"Thủy quái!"** (biểu tượng tam giác tím + viền tím quanh màn hình) và **"Oxy sắp hết!"** (biểu tượng oxy đỏ), thanh oxy "6s" | P4-04 |
| [canh-bao-sang-tuong-phan-cao.png](canh-bao-sang-tuong-phan-cao.png) | Cùng trạng thái, bật tương phản cao: chữ đậm có viền, khung dày, nền cảnh báo đen, nước và bến rõ hơn; gợi ý "H tương phản BẬT" | P4-05 |
| [canh-bao-quan-binh-thuong.png](canh-bao-quan-binh-thuong.png) | Cảnh quán: **"Khách sắp giận! T1"** (biểu tượng mặt giận) và biểu tượng mặt giận ngay cạnh khách T1 (còn 11 s, thanh kiên nhẫn đỏ) | P4-04 |
| [canh-bao-quan-tuong-phan-cao.png](canh-bao-quan-tuong-phan-cao.png) | Cùng trạng thái, tương phản cao: nhãn bếp B1/B2 và bàn T1–T4 đọc rõ, thanh kiên nhẫn viền trắng | P4-05 |
| [phu-de-sfx-tat-tieng.png](phu-de-sfx-tat-tieng.png) | Tắt tiếng bằng phím M (biểu tượng 🔇), phụ đề **"[Píp píp] hết hơi!"** và **"[Khụ] ngạt nước"** vẫn hiện, khớp nhật ký sự kiện thật `t430 oxygen_empty`, `t489 choke` | P4-10 |

Cả ba cảnh báo đều đã chụp ở chế độ tương phản cao (P4-05): thủy quái + oxy ở ảnh cảnh lặn, khách sắp giận ở ảnh cảnh quán.

## Cách chụp (ghi để người sau kiểm lại được)
- Tình huống dựng bằng `--scenario`: cảnh lặn đặt người chơi ở `[48, 20]` với `oxygen_ticks: 430` (Cá Sấu M1 ở `[60, 24]`, cách khoảng 12,6 m); cảnh quán có khách T1 kiên nhẫn 700 tick và khách T2 3000 tick.
- **Để cùng một trạng thái xuất hiện ở cả hai chế độ, tôi đóng băng một snapshot thật của server** (thay `fetch("/state")` trong trang bằng bản sao snapshot đã lấy) rồi bật/tắt phím H. Snapshot là dữ liệu thật từ `/state`, nhưng khi chụp hình không chạy tiếp.
- Ảnh phụ đề: sự kiện `oxygen_empty` và `choke` do sim thật phát; tôi chỉ kéo dài thời gian hiển thị phụ đề (mặc định 1,8 s) để kịp chụp.

## Lỗi tìm thấy nhờ xem ảnh
Lần chụp đầu ở tương phản cao, nhãn bếp **B1/B2 thành hai cục đen** (chữ tối `#111` bị vẽ viền đen). Đã sửa: chữ tối viền **trắng**, chữ sáng viền đen, và thêm test `test_ac_p4_05_chu_toi_co_vien_trang_khong_thanh_cuc_den`. Ảnh trong thư mục này là sau khi sửa.

## Chưa làm / hạn chế
- Chưa nghe âm thanh thật (chỉ kiểm logic và phụ đề); cần một người bật loa thử.
- Cảnh báo thủy quái chỉ ở buổi sáng. `live.py` chưa có `--mode day` nên chưa thử trong vòng ngày đầy đủ.
- Khi `oxygen_ticks` bằng 0 mà người chơi vẫn dưới nước, cảnh báo đổi từ "Oxy sắp hết!" sang "Hết hơi!" (không hiện cả hai).
