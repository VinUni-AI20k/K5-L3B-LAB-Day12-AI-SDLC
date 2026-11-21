# nguyenhung1901 — phản tư cá nhân ( ≤ 200 từ)

- **Tôi đã làm:** Lát 4 Quán: nấu, nhặt, phục vụ, thanh toán, boa, uy tín và kiểm tra scenario. Ở Phase 2, bổ sung kiểm thử AC-P2-05/06/08/12 cho hai bếp, bốn bàn, sáu món, quy tắc cháy và giữ tiền/uy tín qua ca. **Link commit/PR:** *bổ sung link thật sau khi push*.
- **Tôi đã review:** *chưa review*.
- **AI sai ở đâu:** Có lúc test lấy `burn_s: null` trực tiếp từ cấu hình cũ, sẽ sai khi bật mở rộng. Tôi kiểm tra lại PRD và tách tuning lõi với tuning Burn. Lần khác test trên Windows lỗi `python3` trong subprocess, cần phân biệt lỗi môi trường với lỗi gameplay.
- **Điều tôi học được:** Test xanh trên một snapshot chưa chứng minh đã bật extension trên manifest tích hợp. Cần kiểm tra thứ tự tick, điều kiện biên, nguồn cấu hình và giữ bằng chứng đúng commit.

