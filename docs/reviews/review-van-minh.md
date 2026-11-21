# Hướng Dẫn & Biểu Mẫu Review PR của Nguyễn Văn Minh (`@vm140205-collab`)

> **Người thực hiện review:** Tào Quang Vinh (`@qvinhh2312` — UX + Demo lead)  
> **Người được review:** Nguyễn Văn Minh (`@vm140205-collab` — QA lead / `sim/quan_customers.py` & `tests/`)  
> **Nhánh cần review:** `feat/van-minh`  
> **Vùng file liên quan:** `chonoi/sim/quan_customers.py`, `tests/test_*.py`, `docs/proof/`

---

## 1. Quy trình thực hiện review (Reviewer Workflow)

1. **Lấy mã nguồn mới nhất từ nhánh của Văn Minh:**
   ```bash
   git fetch origin feat/van-minh
   git checkout -b review-van-minh origin/feat/van-minh
   ```
2. **Chạy toàn bộ test kiểm thử:**
   ```bash
   python3 -m unittest discover -s tests -v
   ```
3. **So sánh diff mã nguồn:**
   ```bash
   git diff main..review-van-minh --stat
   git diff main..review-van-minh chonoi/sim/quan_customers.py
   ```

---

## 2. Checklist Đánh Giá Chất Lượng (Review Checklist)

### A. Về Luật Khách & Giữ Chỗ (`sim/quan_customers.py` - Ticket 04)
- [ ] Khách đến đúng lịch (`first_customer_tick`, `customer_interval_s * 60`).
- [ ] Giữ chỗ nguyên liệu chính xác theo công thức món ăn ngay khi khách bước vào bàn.
- [ ] Nếu không đủ nguyên liệu khả dụng trong kho (tồn trừ giữ chỗ), phát event `no_dish` và không nhận khách.
- [ ] Thanh kiên nhẫn giảm đúng từng tick; khi cạn kiên nhẫn, phát event `customer_left` với lý do `patience` và trừ uy tín đúng `left_reputation_delta`.
- [ ] Đóng ca (`closing`): Khách còn chờ rời bàn với lý do `closing` mà không bị trừ điểm uy tín.

### B. Về Test & Bằng Chứng (`tests/`, `docs/proof/` - Ticket 07)
- [ ] Toàn bộ các test ca biên trong PRD §6 được hiện thực và pass xanh.
- [ ] Không sửa đổi các file contract cốt lõi (`game.contract.json`, `docs/contracts/`).
- [ ] Có file bằng chứng thực tế tại `docs/proof/phase-1/...`.

---

## 3. Mẫu bình luận phê duyệt PR (Approve Comment Template)

```markdown
### Review from @qvinhh2312 (UX Lead): LGTM! ✅

- [x] Đã kiểm tra diff của `chonoi/sim/quan_customers.py`: logic sinh khách, trừ tồn kho và giữ chỗ nguyên liệu bám sát đặc tả PRD-0.
- [x] Đã chạy toàn bộ unit tests: Tất cả các bài kiểm tra đều pass xanh.
- [x] Đã xác thực event payload khớp hợp đồng: `customer_arrived`, `customer_left`, `no_dish`.
- [x] Không xung đột với module `client/ui` và HUD hiển thị an toàn.

Sẵn sàng merge vào `main`!
```
