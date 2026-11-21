# thangdktd — phản tư cá nhân (≤ 200 từ)

TV2, Developer Gather.

- **Tôi đã làm (kèm link commit):** Phase 1: hái/bắt cá, test hành động và handoff kho ([38e08b2](https://github.com/Hphong2305/K5-L3B-LAB-Day12-AI-SDLC-439/commit/38e08b2), [24ef32f](https://github.com/Hphong2305/K5-L3B-LAB-Day12-AI-SDLC-439/commit/24ef32f), [fb5a133](https://github.com/Hphong2305/K5-L3B-LAB-Day12-AI-SDLC-439/commit/fb5a133)); Phase 2: cá bơi/spawn và test ([9d7d6a1](https://github.com/Hphong2305/K5-L3B-LAB-Day12-AI-SDLC-439/commit/9d7d6a1)); Phase 3: test handoff độ tươi v1.2 ([5252728](https://github.com/Hphong2305/K5-L3B-LAB-Day12-AI-SDLC-439/commit/5252728), merge [c146914](https://github.com/Hphong2305/K5-L3B-LAB-Day12-AI-SDLC-439/commit/c146914)). Không thấy commit Phase 4 của tôi trong refs đã fetch; không nhận phần việc này.
- **Tôi đã review (kèm link):** Không thấy review commit đứng tên tôi. Phối hợp TV1 `phong` (Gather/Integrator), TV5 `vuhieuvh` (QA): [TEAM](../../TEAM.md), [ma trận Phase 2](../verification/phase-2.md).
- **AI sai ở đâu và tôi phát hiện thế nào:** Nhật ký nhóm ghi GitHub Copilot hỗ trợ Phase 1–2. AI tính sai phản xạ cá ở góc hai biên; kiểm chứng bằng test `test_reflection_preserves_remaining_distance_at_edges_and_corner` trong [test_gather_fish.py](../../tests/test_gather_fish.py), đối chiếu vị trí và hướng sau va chạm.
- **Điều tôi học được:** Test riêng cho ca biên giúp kiểm tra hành vi phản xạ cụ thể, không chỉ đường đi thông thường.
