# thanhhy98 — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm:** Phụ trách QA Lead Phase 1 — chạy toàn bộ `unittest`, chạy `check-contract` và `prepare-proof`, xác minh determinism byte-giống-byte của `gather`/`quan`, lưu báo cáo và log vào [`docs/proof/phase-1/harness/20261121-115821-788296/`](../proof/phase-1/harness/20261121-115821-788296/report.md), đồng thời đối chiếu matrix [`docs/verification/phase-1.md`](../verification/phase-1.md).
- **Tôi đã review:** Mặt QA của Phase 1 gồm test gather, quan, scenario, smoke/integration, UI và Test Contract; không sửa luật mô phỏng hoặc contract.
- **AI sai ở đâu và tôi phát hiện thế nào:** AI không thay số liệu hay khoanh vùng kết quả; mọi kết luận đều dựa trên mã exit thực tế, test log và SHA-256 trong thư mục proof.
- **Điều tôi học được:** Bằng chứng handover cần vừa xanh, vừa được truy vết: test output + snapshot determinism + liên kết matrix mới là phần bắt buộc.
