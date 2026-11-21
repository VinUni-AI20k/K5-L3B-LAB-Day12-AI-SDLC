# 01: Adapter kho cá thể + contract v1.2

**What to build:** Một lớp kho duy nhất mà sim nói chuyện, đọc/ghi được cả schema đếm (v1.0/1.1) và schema cá thể (v1.2), để đổi schema mà main vẫn xanh và không phải sửa hàng loạt fixture cùng lúc.

**Blocked by:** —

**Status:** ready-for-agent

- [ ] `contract_version: "1.2"` + `freshness {initial: 100, gather_decay_per_s: 0.5, quan_decay_per_s: 0.25, spoiled_below: 30}`; kiểm dải hợp lệ.
- [ ] Lớp kho: thêm cá thể với id tự cấp (`I1`, `I2`, … xuyên pha và xuyên Ngày), lấy theo id, lấy cá thể tươi nhất của một kind (hòa theo id), đếm theo kind, xuất mảng theo id.
- [ ] Đọc file: chọn schema theo `contract_version`; v1.2 từ chối file đếm bằng mã 2 (và ngược lại); từ chối id trùng, kind lạ, `fresh` ngoài [0,100].
- [ ] Ghi file: đúng một lần khi `gather_end`, file tạm + thay thế nguyên tử, ngất ghi `{"items":[]}`.
- [ ] Độ tươi lưu bằng **số nguyên đơn vị** (1 điểm = 240): hao 2 đơn vị/tick trong giỏ, 1 đơn vị/tick trong kho; ngưỡng ươn 7 200.
- [ ] `gather_end.data.inventory` và snapshot quán dùng cùng schema với file.
- [ ] Test migration: cùng một fixture chạy được ở v1.1 và bị từ chối ở v1.2 (và ngược lại); smoke hai tiến trình xanh trên schema mới.
