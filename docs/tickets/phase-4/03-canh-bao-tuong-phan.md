# 03: Cảnh báo dễ nhận biết + chế độ tương phản cao

**What to build:** Ba tình huống nguy hiểm phải nhận ra ngay bằng chữ hoặc biểu tượng (không phụ thuộc màu): thủy quái gần, oxy sắp hết, khách sắp giận. Thêm chế độ tương phản cao và chơi thử cả ba cảnh báo trong chế độ đó.

**Blocked by:** P2-06 (HUD)

**Status:** done

- [x] "Thủy quái!" + biểu tượng + viền khi Cá Sấu trong bán kính phát hiện; tắt khi ra xa.
- [x] "Hết hơi!" + biểu tượng khi oxy dưới 25%; nhịp nhấp nháy nhanh dần khi gần 0.
- [x] "Khách sắp giận" + biểu tượng khi kiên nhẫn dưới 25% (đổi theo từng bàn ở HUD tối).
- [x] Chế độ tương phản cao (phím `C`): nền tối đặc, chữ viền, tắt hiệu ứng rườm; trạng thái được ghi nhớ trong phiên.
- [x] Ba cảnh báo đọc được **trong chế độ tương phản cao** — có bằng chứng tại `docs/proof/phase-4/canh-bao-tuong-phan.md`.
- [x] Không đổi `chonoi/`; headless giữ nguyên byte.
