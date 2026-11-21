# P4-10 · Demo một Ngày

Chạy từ gốc repo, mở địa chỉ mà lệnh in ra và nhấn **R** khi sẵn sàng. Kịch bản đặt Út Sen cạnh cá lóc, chuẩn bị một bông súng và 160 tiền ban đầu để có thể mua oxy sau khi bán món. Lặn giới hạn 20 giây, Quán 45 giây, Shop 10 giây. Luật chơi dùng contract v1.3.

```bash
python3 -m chonoi.live --mode day --days 1 --seed 42 --scenario docs/proof/phase-4/p4-10-day.scenario.json
```

| Thời lượng dự kiến | Người | Thao tác và nội dung |
|---|---|---|
| 0:00–1:15 | A (Nhật) | **Space** để bắt cá lóc, giữ **W+A** khoảng một giây để nổi về bến, thả phím rồi nhấn **E**. Chỉ ra cá lóc vừa bắt xuất hiện trong kho Quán. |
| Trong lượt Quán | A (Nhật) | Đứng sẵn ở bếp **B1**. Đợi khách gọi cá lóc nướng trui ở **T1**, nhấn **E** để nấu. Khi món chín, thả rồi nhấn **E** để lấy. Giữ **D+S** khoảng hai giây đến gần T1, thả phím rồi nhấn **E** để phục vụ. Chỉ ra tiền món và tiền boa sau khi khách ăn xong. |
| Khi Shop mở | A (Nhật) | Chỉ ra bông súng còn lại, nhấn **1** mua oxy rồi **Enter** kết thúc Ngày. Shop tự đóng sau 10 giây. |
| 1:15–2:30 | D (Lương) | Cho thấy kết quả test chạy sẵn, mở ma trận truy vết và chỉ từ một tiêu chí đến test tương ứng. [Ma trận Phase 3](../../verification/phase-3.md) |
| 2:30–3:45 | B (Tú), C (Cường) | B giải thích giữ nguyên liệu theo ID và tính giá theo độ tươi. C chỉ HUD độ tươi, cảnh báo và phím **H** bật tương phản cao. [Quán #49](https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn/pull/49), [HUD #44](https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn/pull/44), [cảnh báo #42](https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn/pull/42) |

Chuẩn bị kết quả kiểm thử trước giờ demo để D mở ngay sau lượt chơi.

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -q
python3 tools/smoke_phase3.py
```

## Chạy thử

Đã chạy một Ngày với server `chonoi.live` trên contract v1.3. Gửi thao tác qua `POST /input` và kiểm trạng thái qua `GET /state`. Cá lóc vào kho Quán giữ ID `I2`, được bếp B1 nấu và phục vụ cho T1. Khách trả 70, gồm 59 tiền món và 11 tiền boa. Shop còn bông súng `I1`, mua oxy cấp 1 hết 200 và còn 30. Lượt chơi kết thúc với `days_complete`. Lượt trình bày dùng phím theo hướng dẫn trên.
