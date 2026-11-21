# ToanLee5433 — phản tư cá nhân (≤ 200 từ)

Le Quy Toan · `sim/gather` · Integrator.

- Tôi đã làm (kèm link commit):
  - Thêm nguyên liệu theo node_yield trong gather ([e7a34ae](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/e7a34aeb672a366965c70067c825d2443142eb4c))
  - Sửa cooldown hold_full và bật test gather ([28cf1a4](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/28cf1a4e437b0d9d5c1febffd26f567c664f0003))
  - Triển khai vòng đời khách, đặt nguyên liệu, nấu, phục vụ, thanh toán và test quan ([327a1a9](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/327a1a9afdbf8b0560af282ebbc999f0e392675c))
  - Cập nhật contracts, clarify và kế hoạch phase 1 ([d87b015](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/d87b0152dcb372bf28f8cdd96a20a433dc4f6aff))
  - Triển khai lặn, oxy, ngạt, thu hoạch, câu cá và test gather ([3e966f5](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/3e966f50e235bd6ba827bafdd585da02ebeedd78))
- Tôi đã review (kèm link): Xem trực tiếp và đối chiếu [PR #3](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/pull/3) (`sim/quan`) của Nam (dữ liệu kho bàn giao); xem [PR #5](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/pull/5) (`client/ui`) của Thái (hiển thị HUD).
- AI sai ở đâu và tôi phát hiện thế nào: AI tự gán cooldown 30 tick khi bắt cá hụt do đầy giỏ (trái clarify #5) và hardcode thêm 1 món thay vì biến `node_yield`. Phát hiện khi chạy test gather và review PR #4.
- Điều tôi học được: Bám sát clarify, không để AI đoán luật ngầm; làm đúng lát cắt, không lấn module khác; chuẩn hóa schema kho giúp nối 2 tiến trình mượt mà.
