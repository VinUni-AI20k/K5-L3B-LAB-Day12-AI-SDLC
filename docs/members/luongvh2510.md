# luongvh2510 — phản tư cá nhân (≤ 200 từ)

**Thành viên D — Võ Hồng Lương.** Module: `qa` và tích hợp. Vai: PO, Integrator, QA lead, Release.

- Tôi đã làm (kèm link commit):
  - TEAM.md, hợp đồng tích hợp, kế hoạch Phase 1: [PR #1](https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn/pull/1)
  - Kiểm scenario và contract: [PR #2](https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn/pull/2), [#9](https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn/pull/9), [#11](https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn/pull/11)
  - Test gather và quán: [PR #7](https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn/pull/7), [#13](https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn/pull/13), [#16](https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn/pull/16)
  - Skill, hook, smoke, bằng chứng: [PR #4](https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn/pull/4), [#15](https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn/pull/15), [#17](https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn/pull/17), [#18](https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn/pull/18)
- Tôi đã review (kèm link): [PR #5](https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn/pull/5#issuecomment-7057037146), [#8](https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn/pull/8#issuecomment-7057258063), [#12](https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn/pull/12#issuecomment-7057531193)
- AI sai ở đâu và tôi phát hiện thế nào: lúc chưa có PRD-0, AI giả định `stoves[].dish` là id món nên từ chối nhầm scenario hợp lệ; sau khi đọc PRD-0 mục D tôi nhờ đối chiếu lại và sửa ở PR #9. Test gather lần đầu bỏ sót thứ tự rơi giỏ LIFO; tôi hỏi lại "đã check kỹ chưa" nên AI chạy thêm phá thử và bổ sung.
- Điều tôi học được: đọc đề gốc trước khi để AI đoán; test chỉ đáng tin khi cố ý phá code mà test vẫn đỏ; việc dồn vào một người (tôi làm thay P1-10, P1-15) nên chia lại sớm.
