# LeBao403 - phản tư cá nhân (≤ 200 từ)

- Tôi đã làm (kèm link commit), vai Integrator:
  - P1: lát 1 oxy, ngạt, ngất ([53a6d4e](https://github.com/common-maker/K5-L3B-LAB-Day12-AI-SDLC-CSCD/commit/53a6d4e)), hợp đồng tích hợp ([2457180](https://github.com/common-maker/K5-L3B-LAB-Day12-AI-SDLC-CSCD/commit/2457180)).
  - P2: nền v1.1 ([8b4af41](https://github.com/common-maker/K5-L3B-LAB-Day12-AI-SDLC-CSCD/commit/8b4af41)), Cá Sấu ([2345c62](https://github.com/common-maker/K5-L3B-LAB-Day12-AI-SDLC-CSCD/commit/2345c62)), mở rộng Rắn Hổ Mây ([46a7e82](https://github.com/common-maker/K5-L3B-LAB-Day12-AI-SDLC-CSCD/commit/46a7e82)).
  - P3: ADR-0001 ([075e8d8](https://github.com/common-maker/K5-L3B-LAB-Day12-AI-SDLC-CSCD/commit/075e8d8)), nền v1.2 hai phiên bản ([b241174](https://github.com/common-maker/K5-L3B-LAB-Day12-AI-SDLC-CSCD/commit/b241174)), bật v1.2 ([8e94104](https://github.com/common-maker/K5-L3B-LAB-Day12-AI-SDLC-CSCD/commit/8e94104)).
  - P4: v1.3, `soak_cmd`, khung `bench_cmd` ([04fb719](https://github.com/common-maker/K5-L3B-LAB-Day12-AI-SDLC-CSCD/commit/04fb719), [a1a672c](https://github.com/common-maker/K5-L3B-LAB-Day12-AI-SDLC-CSCD/commit/a1a672c)).
- Tôi đã review: đọc và merge PR #10, #11, #12, #14, #21, #23, #25, #26 của các bạn. Sửa 3 test cũ của C, D, E khi số liệu v1.1 đổi, có ghi lý do ([b8703e6](https://github.com/common-maker/K5-L3B-LAB-Day12-AI-SDLC-CSCD/commit/b8703e6)).
- AI sai ở đâu và tôi phát hiện thế nào:
  - AI viết luôn phần của B, C khi làm nền v1.1. Tôi phát hiện khi đọc diff theo bảng phân công, trả phần Shop về khung rỗng.
  - Khung bench tính `measured_s` thiếu một khung; test của chính nó bắt được.
- Điều tôi học được: đổi hợp đồng thì làm nền hai phiên bản trước, chỉ bật khi các lát đã chuyển xong. PR #22 bật v1.2 sớm làm `main` đỏ 47 test.
