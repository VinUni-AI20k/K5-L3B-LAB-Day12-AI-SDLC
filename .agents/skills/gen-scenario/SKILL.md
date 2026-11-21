---
name: gen-scenario
description: Hướng dẫn tạo kịch bản (scenario fixture) đúng chuẩn contract v1.0 để kiểm thử điểm biên cho Gather và Quán.
---

# Skill: gen-scenario

Dùng khi cần tạo file kịch bản JSON (`scenario`) kiểm tra các trường hợp biên:

### 1. Kịch bản Gather (Buổi sáng)
- File chỉ chứa khóa gốc `{"gather": {...}}`
- Các trường hợp biên thường dùng:
  - Kiểm tra gần hết oxy: `{"gather": {"player": {"pos": [20, 5], "oxygen_ticks": 10}}}`
  - Kiểm tra ngạt thở: `{"gather": {"player": {"pos": [20, 5], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 1}}}`
  - Kiểm tra đầy giỏ: `{"gather": {"hold": ["ca_loc", "ca_linh", "bong_dien_dien", "bong_sung", "ca_loc", "ca_loc", "ca_loc", "ca_loc", "ca_loc", "ca_loc", "ca_loc", "ca_loc"]}}` (đúng 12 món = hold_capacity)

### 2. Kịch bản Quán (Buổi tối)
- File chỉ chứa khóa gốc `{"quan": {...}}`
- Các trường hợp biên thường dùng:
  - Kho ban đầu: `{"quan": {"stock": {"ca_loc": 2, "bong_sung": 4}}}`
  - Khách định trước: `{"quan": {"customers": [{"id": "C1", "table_id": "T1", "dish": "ca_loc_nuong_trui", "patience_ticks": 100}]}}`
- Lưu ý: Không dùng đồng thời `stock` trong scenario và cờ `--inventory` khi chạy lệnh.
