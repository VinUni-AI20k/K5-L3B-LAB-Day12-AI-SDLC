# Changelog
## Unreleased

## [1.2.0] - Phase 3 (TICKET-03)

- **Breaking change — file kho JSON:** `items` chuyển từ map đếm số lượng như `{"items":{"ca_loc":2}}` sang mảng cá thể như `{"items":[{"id":"I1","kind":"ca_loc","fresh":100.0}]}`. Mỗi nguyên liệu có ID duy nhất và độ tươi riêng; kho rỗng là `{"items":[]}`.
- `--inventory` từ chối file kho định dạng cũ hoặc cá thể sai schema với exit code `2`. Gather ghi `--inventory-out` nguyên tử; Day chuyển nguyên `id`, `kind`, `fresh` sang Quán.
