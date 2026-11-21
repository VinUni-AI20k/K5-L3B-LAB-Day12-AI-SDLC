# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | ttkien0710 (Trần Trung Kiên) | Gemini 3.8 Flash (High) | Viết logic sim/quan Lát 4 (bếp, phục vụ, thanh toán, tip, quan_end) và bộ test unit 7 cases | ~30k tokens | AI viết thiếu thả nút interact giữa 2 lần bấm trong test, phát hiện nhờ assertion error và đã sửa đúng cơ chế cạnh lên |
| 1 | NhomF7 / Copilot | Copilot SDK trong VS Code | Hoàn thiện Gather, Quán, test logic và verification | Không đo được | Đã đối chiếu contract trước sửa; test baseline và suite sau sửa đều xanh. |
| 1 | Quoosc (Q3 task, Codex) | Codex / GPT-6 | Local checkout/spec review; Q3 reservation, spawn and patience changes; outcome tests and proof draft | Không đo được | Baseline tests first failed because Windows lacked the contract command `python3`; a temporary PATH shim made the baseline reproducible. Q4 review found a cooking customer can leave and orphan a cooked dish; recorded as a finding, not an approval. |
