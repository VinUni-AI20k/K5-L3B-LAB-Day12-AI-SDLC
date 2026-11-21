# Changelog
## Unreleased

### P3-04 — chuẩn bị tích hợp Test Contract v1.2

- Thêm helper bếp tiêu đúng cá thể đã giữ và chốt giá theo độ tươi trung bình, event `cook_started.items` là object sắp kind/ID. Giá được giữ qua phục vụ/thanh toán.
- Breaking change đích v1.2: `stock`/file `items` từ map đếm sang mảng `{id,kind,fresh}`, `reserved` thành mảng ID; khi bật v1.2 phải từ chối kho đếm với mã 2. Migration thuộc P3-02/P3-03 **chưa tích hợp**; manifest/CLI hiện vẫn v1.1, không âm thầm nhận schema mới.
- Không sửa/xóa test P1/P2; 17 test mới dùng mock ranh giới P3-03 có ghi nhãn. Chi tiết và giới hạn tại `docs/notes/P3-04.md`.
