# Changelog
## Unreleased

- P3-03 chuẩn bị schema v1.2 cho Quán. File kho dùng `{"items":[{"id":"I1","kind":"ca_loc","fresh":100}]}`. Scenario `quan.stock` dùng mảng tương tự, và `customers[].reserved` dùng mảng ID như `["I1"]`. Mỗi ID đại diện một cá thể. Khi bật v1.2, thay fixture kho đếm bằng schema này. Preset chung hiện vẫn là v1.1 trong lúc tích hợp đầu ghi ở buổi Lặn.
