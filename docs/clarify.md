# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 | PRD-0 mục E không đọc được (lab board yêu cầu đăng nhập, Phase 1 hiện "Chưa phát hành"). `data` của `oxygen_empty`, `choke`, `faint` lấy thế nào? | Giả định: `dive`/`surface` theo comment starter `{"pos":[x,d]}`; `oxygen_empty` và `faint` là `{}`; `choke` là `{"hp": máu còn sau khi trừ}`; `hold_full` là `{"kind": id món bị từ chối}`. Đủ `choke_interval_ticks` tick oxy = 0 dưới nước thì trừ Máu và đưa `zero_oxy_ticks` về 0. | TV1, chờ PRD hoặc Anh Năm xác nhận |
