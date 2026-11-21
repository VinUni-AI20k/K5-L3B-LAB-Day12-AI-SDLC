
# Menu Contract – Quán Ăn Chợ Nổi

## 1. Nguyên liệu

| ID | Tên nguyên liệu |
|---|---|
| ca_loc | Cá lóc |
| ca_linh | Cá linh |
| bong_dien_dien | Bông điên điển |
| bong_sung | Bông súng |

## 2. Thực đơn

| ID món | Tên món | Công thức | Giá bán | Thời gian nấu |
|---|---|---|---:|---:|
| ca_loc_nuong_trui | Cá lóc nướng trui | ca_loc x1 | 60 | 6s |
| goi_bong_sung | Gỏi bông súng | bong_sung x2 | 40 | 4s |
| lau_ca_linh_dien_dien | Lẩu cá linh bông điên điển | ca_linh x3 + bong_dien_dien x1 | 120 | 10s |

## 3. Quy tắc

- Chỉ được nấu món khi kho đủ nguyên liệu.
- Khi khách đặt món, nguyên liệu được giữ chỗ.
- Mỗi món có thời gian nấu và giá bán cố định theo game.contract.json.
- Không tự ý thay đổi ID nguyên liệu và ID món.
- Các thông số vận hành phải thống nhất với game.contract.json.

## 4. Inventory Sample

File: inventory.sample.json

{
  "items": {
    "bong_sung": 2,
    "ca_loc": 1
  }
}
