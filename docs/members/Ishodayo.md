# Ishodayo — phản tư cá nhân (≤ 200 từ)

Nguyễn Thành Nam · module `sim/quan`

- Tôi đã làm (kèm link commit):
  - Luật Quán phase 1 theo PRD-0 mục D/E/F (khách, giữ chỗ, kiên nhẫn, bếp, bưng, phục vụ, tiền, uy tín, hết ca) và 13 test hộp đen: [d09e7e7](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/d09e7e7)
  - Sửa 2 lỗi chặn từ review, thêm test quét fixture sai kiểu: [35b237f](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/35b237f)
  - Cập nhật vai trong `TEAM.md`: [0f99a4b](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/commit/0f99a4b)
  - PR gộp vào `dev`: [#3](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/pull/3)
- Tôi đã review (xem trực tiếp, góp ý thẳng với người làm, không để lại review trên GitHub): [#4](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/pull/4) gather core (lát kế bên, đối chiếu file kho với quán), [#5](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/pull/5) client UI (trường snapshot quán), [#7](https://github.com/czx04/K5-L3B-LAB-Day12-AI-SDLC-6667/pull/7) bàn giao phase 1 lên main.
- AI sai ở đâu và tôi phát hiện thế nào:
  - AI tự đặt luật chặt hơn PRD: khách chưa phục vụ khai `tip: 0` bị trả mã 2, làm 16 test QA đỏ. Phát hiện qua review PR #3.
  - AI bỏ sót kiểm kiểu: `dish_id: []` làm crash (mã 1 thay vì 2). Review phát hiện; sau đó tôi cho AI viết test quét ~140 fixture sai kiểu và bắt thêm lỗi `stoves[].dish` sai kiểu.
- Điều tôi học được: chỗ PRD không nói thì không để AI tự siết luật, phải ghi vào `docs/clarify.md`; test quét đầu vào sai kiểu bắt được lỗi mà test theo ca thường bỏ sót; chốt hợp đồng sớm để tránh hai người cùng viết một module.
