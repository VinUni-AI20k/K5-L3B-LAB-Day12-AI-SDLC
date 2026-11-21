# Quán Ăn Chợ Nổi — nhóm NgheAn

Game 2D nhỏ: buổi sáng Út Sen **lặn bắt cá, hái rau** trên sông (tránh Cá Sấu, canh oxy và Máu), buổi tối **mở quán** nấu và phục vụ khách, cuối Ngày ghé **Shop** mua nâng cấp. Nhóm làm trong bài lab Day 12 · AI SDLC (đề và luật lab: [`docs/LAB.md`](docs/LAB.md)).

## Chạy nhanh (clone sạch, 3 lệnh)

Cần Python 3 (CI chạy 3.12 trên Ubuntu). Không cần cài thêm gói nào: chỉ dùng thư viện chuẩn.

```bash
git clone https://github.com/luongvh2510/K5-L3B-LAB-Day12-AI-SDLC-NgheAn.git
cd K5-L3B-LAB-Day12-AI-SDLC-NgheAn
python3 -m chonoi.live
```

Lệnh cuối in một địa chỉ (mặc định `http://127.0.0.1:8000/`); mở bằng trình duyệt, chọn chế độ ở menu rồi chơi.

## Cách chơi

| Phím | Tác dụng |
|---|---|
| WASD / mũi tên | bơi (Lặn) hoặc đi (Quán) |
| E | cập bến, hái rau; nhận và nấu món, mang món ra bàn |
| Space | bắt cá (dưới nước) |
| P / Esc | tạm dừng / tiếp tục |
| 1 / 2 / Enter | Shop: mua oxy / mua Máu / sang Ngày mới |
| R / M | chơi lại / về menu |
| H | bật/tắt tương phản cao (hoặc mở `http://127.0.0.1:8000/?hc=1`) |

Khi chơi, băng cảnh báo hiện biểu tượng và chữ (không chỉ màu) lúc **oxy sắp hết**, **Cá Sấu ở gần** và **khách sắp giận**.

Menu có ba chế độ: **Chơi theo Ngày** (Lặn → Quán → Shop, 1–5 Ngày), **chỉ buổi sáng** và **chỉ buổi tối**. Chạy thẳng một chế độ: `python3 -m chonoi.live --mode day --days 3`.

## Lệnh cho người phát triển và chấm tự động

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v                       # toàn bộ test
python3 -m chonoi.headless --mode day --days 1 --seed 1 --ticks 600 --out out.jsonl # headless (Test Contract)
python3 tools/check_determinism.py                                                # cùng seed, output giống từng byte
```

Các lệnh khai trong [`game.contract.json`](game.contract.json) (`build_cmd`, `run_cmd`, `headless_cmd`). Chi tiết khung kỹ thuật: [`docs/STARTER.md`](docs/STARTER.md); hướng dẫn cho agent AI: [`AGENTS.md`](AGENTS.md).

Chạy thử độ bền 10 Ngày liền bằng `python3 -m chonoi.soak --seed 7 --days 10 --out soak.json` (ghi `soak.json`; xem [cách chạy và kết quả](docs/proof/phase-4/p4-04-soak.md)).

## Cấu trúc

- `chonoi/sim/`: luật chơi của nhóm (`gather.py`, `fish.py`, `monsters.py`, `quan.py`, `shop.py`, `day.py`).
- `chonoi/web/index.html`, `chonoi/live.py`: cửa sổ chơi trên trình duyệt (chỉ đọc snapshot).
- `docs/`: kế hoạch (`plan/`), hợp đồng tích hợp (`contracts/`), câu hỏi PO (`clarify.md`), bằng chứng (`proof/`, `verification/`), retro, nhật ký AI, hồ sơ thành viên.

## Sáng tạo của nhóm

Chưa có mở rộng ngoài đề tính tới bản này. Mọi mở rộng sau này phải tắt ở headless và ghi tại đây (việc P4-03).

## Nhóm

Xem [`TEAM.md`](TEAM.md). Thay đổi theo phiên bản: [`CHANGELOG.md`](CHANGELOG.md). Nguồn và công cụ AI: [`CREDITS.md`](CREDITS.md). Giấy phép: [`LICENSE`](LICENSE) (MIT).
