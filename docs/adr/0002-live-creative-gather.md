# ADR-0002: Chế độ sáng tạo Live (Creative Mode) cho Gather

## Bối cảnh
Người chơi muốn trải nghiệm thử thách cao hơn khi chơi trực tiếp: có nhiều Cá Sấu Năm Chèo hơn (M1, M2, M3), vùng tuần tra rộng hơn khắp các dải độ sâu, và có thêm các bầy cá kèo đắt tiền ở tầng nước sâu $d \in [22, 28]$ để tăng tính mạo hiểm.

## Quyết định
1. **Tuyệt đối tuân thủ Test Contract v1.1:**
   - Tính năng này **TẮT HOÀN TOÀN ở chế độ Headless (`chonoi.headless`)** để giữ nguyên tính tất định byte-identical và pass 100% auto-grader của Lab Coach.
   - Không can thiệp vào `game.contract.json` khóa cứng.
2. **Kích hoạt qua `--creative` ở chế độ Live (`chonoi.live`):**
   - Lệnh chạy: `python3 -m chonoi.live --mode gather --creative`
   - Bổ sung 3 con cá sấu:
     * `M1`: Tuần tra mở rộng từ $[45, 24]$ đến $[70, 24]$.
     * `M2`: Tuần tra đông sâu từ $[75, 18]$ đến $[95, 18]$.
     * `M3`: Tuần tra tây sâu từ $[15, 22]$ đến $[40, 22]$.
   - Bổ sung 3 đàn cá kèo đắt tiền `FK1`, `FK2`, `FK3` ở tầng sâu $d \in [24, 27]$.
