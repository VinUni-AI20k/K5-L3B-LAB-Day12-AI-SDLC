# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| Phase 1 | Người 4 (QA) | Antigravity / Gemini 3.8 Flash | Xây dựng công cụ kiểm tra tất định (`tools/check_determinism.py`), skill `determinism-check`, bộ test QA (`tests/test_qa_determinism.py`), và lưu bằng chứng baseline. | ~15k tokens | AI ban đầu dùng `cmp` của Linux; đã hiệu chỉnh sang script Python `filecmp` và băm SHA256 để tương thích đa nền tảng (Windows/Linux). |
