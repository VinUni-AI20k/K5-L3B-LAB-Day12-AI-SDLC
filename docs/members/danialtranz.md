# danialtranz — phản tư cá nhân (≤ 200 từ)

- Tôi đã làm (kèm link commit): Lát 1 trong `chonoi/sim/gather.py` — dive/surface, oxy, ngạt/choke, ngất/faint, API giỏ `can_hold`/`push_hold`; test `tests/test_gather_lat1.py`; Scrum cập nhật `CHANGELOG.md` / `docs/standup.md`.
- Tôi đã review (kèm link): sẽ review chéo Lát 2 với Phát khi có PR.
- AI sai ở đâu và tôi phát hiện thế nào: cần chốt timing ngạt (t+59) và nổi đúng bước ngạt thì không choke — đã khóa bằng test.
- Điều tôi học được: đọc số từ `game.contract.json`, không hard-code; chốt API giỏ sớm để Lát 2 ghép được.
