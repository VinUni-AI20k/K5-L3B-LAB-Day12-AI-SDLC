# Credits

Asset ngoài (nguồn, giấy phép) và công cụ AI nhóm đã dùng. Mã nguồn của nhóm theo [`LICENSE`](LICENSE) (MIT);
asset **không** thuộc MIT mà giữ giấy phép riêng ghi dưới đây.

## Nguồn sự thật cho asset

- [`client/assets/manifest.json`](client/assets/manifest.json) — từng file: nguồn, tác giả, giấy phép.
- [`client/assets/CREDITS-assets.md`](client/assets/CREDITS-assets.md) — bản dễ đọc, kèm dòng ghi công bắt buộc.

## Tóm tắt giấy phép (bản chơi GUI `client/`)

| Nhóm asset | Giấy phép | Ghi chú |
|---|---|---|
| Sprite, nền, UI, nhạc, phần lớn hiệu ứng âm thanh (OpenGameArt: ansimuz, Kenney, rubberduck, MintoDog…) | CC0 | Không bắt buộc ghi công, nhóm vẫn ghi trong `CREDITS-assets.md` |
| `sfx/cooking_boil.mp3`, `sfx/stove_on.mp3` — "Kitchen Ambience, SFX" của **DavidW** | **CC-BY 4.0** | Bắt buộc giữ dòng ghi công |
| Font Cozette (`fonts/cozette*.ttf`) | **MIT** | Phải đi kèm `fonts/LICENSE-cozette.txt` |
| `ui/title_key_art.webp` — ảnh bìa màn hình tiêu đề | Của nhóm Nhom001 | Nhóm cung cấp |
| `video/intro.mp4` — video mở đầu 10 s | Tạo bằng **Meta AI** (còn watermark Meta AI) | Nén lại bằng ffmpeg (H.264 CRF 25, ~4.3 MB); chỉ dùng cho lab phi thương mại, theo điều khoản của Meta AI |
| Nhạc nền tổng hợp, giọng bập bẹ, hiệu ứng cutscene | Mã của nhóm | WebAudio trong `client/src/music.js`, `voice.js`, `audio.js`, không dùng mẫu âm thanh ngoài |

Không dùng asset của Dave the Diver hay game thương mại nào. Bảng tham chiếu bố cục trong
[`docs/design/reference-scenes.md`](docs/design/reference-scenes.md) chỉ chứa liên kết, không chép asset.

## Công cụ AI

- **Claude Code** (Anthropic) — viết và review mã sim, test, client, tài liệu; mọi phiên ghi trong
  [`docs/ai-usage-log.md`](docs/ai-usage-log.md). Đầu ra AI được kiểm bằng test headless và chơi thử trên trình duyệt.
- **Meta AI** — tạo video mở đầu `client/assets/video/intro.mp4`.
- **ffmpeg** — nén video, cắt/chuyển âm thanh sang MP3 mono.

## Mã khởi đầu

Khung `chonoi/`, `docs/STARTER.md`, ticket và Test Contract trong `docs/contracts/` lấy từ repo lab của khóa học.
