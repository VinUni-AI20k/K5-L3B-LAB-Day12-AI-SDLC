# Changelog
## Unreleased

## v1.2 — Phase 3

- **Breaking change:** kho đếm theo kind không còn hợp lệ (mã 2); file kho,
  gather.hold, quan.stock và snapshot chuyển sang mảng cá thể có id/kind/fresh.
  `customers[].reserved` chuyển từ lượng sang mảng id; món chốt giá theo độ tươi.
- Freshness dùng số nguyên 240 đơn vị/điểm, gather −2/tick, quan −1/tick;
  dưới 30 là ươn, phát spoiled một lần theo thứ tự id. Adapter ghi nguyên tử,
  theo id, sáu chữ số thập phân; bảo toàn đơn vị/ngưỡng khi đọc lại.
- Day bàn giao nguyên cá thể cùng tick, giữ id tăng xuyên Ngày; mẫu giỏ Ngày
  kế được cấp id mới theo thứ tự vào giỏ. Shop không hao tươi; vendor nếu có
  chọn bán tươi nhất và nhập hàng mua riêng vào kho quán Ngày kế ở fresh 100.
- Cập nhật fixture trước: `{"items":{"ca_loc":1,"bong_sung":2}}`;
  sau: `{"items":[{"id":"I1","kind":"ca_loc","fresh":100},
  {"id":"I2","kind":"bong_sung","fresh":100},
  {"id":"I3","kind":"bong_sung","fresh":100}]}`.
  Scenario dùng mảng trên cho hold/stock (không bọc items). Phần giữ trước
  `{"ca_loc":1}` thành `["I1"]`; không khai reserved để sim tự chọn tươi nhất.
  Đừng đổi fixture kho đếm âm tính: phải tiếp tục kiểm mã 2.
- Lát A đổi adapter/contract/scenario/runner/day vì PRD bắt buộc schema mới;
  không đổi luật gather/quan trong lát này. Kiểm riêng: 8 test FreshInventoryP3
  và 5 test DayAdapterP3 (double giao diện B/C); kiểm sim thật sau tích hợp.

  Kết quả tại worktree lát A: 13/13 test nền tảng/ranh giới qua; toàn bộ 176
  test có 59 fail, 11 error do phần sim/fixture còn schema trước tích hợp
  (ví dụ GatherSim chưa chuyển fresh sang fresh_u). Chưa xác nhận regression
  với sim B/C thật. PRD Phase 3 có sẵn được giữ nguyên; không commit/push.
