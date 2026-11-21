# Media — Quán Ăn Chợ Nổi

Marketing screenshots (1280×720 PNG) and a short fast-play demo video, captured from the real game in headless Chrome.

| File | Caption |
|---|---|
| `screenshots/01-title-key-art.png` | Title screen: key art, logo and the main menu |
| `screenshots/02-splash-video.png` | Splash video (~4 s in), loaded without `?debug` / `?novideo` |
| `screenshots/03-intro-cutscene-dialogue.png` | Opening cutscene at sunrise: Bà Tư's dialogue box |
| `screenshots/04-character-intro-ut-sen.png` | Character intro card: ÚT SEN, "Nhân vật chính" |
| `screenshots/05-day-intro-ma-tu-list.png` | Ngày 1 card: Má Tư's shopping list (Cần lấy) |
| `screenshots/06-dive-surface-fish-hud.png` | Diving near the surface: fish schools, O₂/HP HUD, today's needs list |
| `screenshots/07-harpoon-in-flight.png` | Harpoon in flight toward a fish school |
| `screenshots/08-deep-zone-40m.png` | Deep zone (~35 m): rocks, current warning, O₂ ×1.5 |
| `screenshots/09-ca-sau-chase-warning.png` | Cá Sấu Năm Chèo on the hunt, "Thủy quái!" warning border, empty basket (Giỏ 0/120) |
| `screenshots/10-inventory-overlay.png` | Inventory (I): catches with freshness bars |
| `screenshots/11-dusk-cutscene-lanterns.png` | Dusk cutscene: "Chiều tà", heading back to the raft |
| `screenshots/12-preopen-raft-mo-quan.png` | Pre-open raft: lanterns, Bà Tư, tonight's menu, "Mở quán ▶" |
| `screenshots/13-menu-board-dac-san.png` | Menu board pop-up: dishes, portions, plan tags |
| `screenshots/14-busy-service.png` | Service rush: several guests served and eating, coins flying, order bubbles, stove cooking |
| `screenshots/15-ba-tu-dialog.png` | Bà Tư dialog: talk, decorate, chores, hire staff |
| `screenshots/16-phone-overlay.png` | Sen's phone (T): chores, notebook, staff, décor, messages, market |
| `screenshots/17-shop-popup-dock.png` | Night dock: Chợ Chú Sáu shop pop-up (Mua / Bán / Nâng cấp) |
| `screenshots/18-high-contrast-dive-warning.png` | High-contrast mode (H) in the dive with the monster warning |
| `screenshots/19-hire-staff-dialog.png` | Bà Tư dialog → Thuê người: Bé Tí (chạy bàn) and Chú Bảy (phụ bếp) just hired |
| `screenshots/20-decorated-raft.png` | Pre-open raft after the décor purchases: bảy màu lanterns, hoa sen tablecloths, giàn bông, sơn mài sign |
| `screenshots/21-staff-working.png` | Service with staff: Chú Bảy cooking at a stove, Bé Tí carrying a dish while Út Sen serves |
| `demo.mp4` | ~90 s fast playthrough (≈3×): title, intro, Ngày 1, dive, deep zone, Cá Sấu chase with the "Thủy quái!" warning, dock, dusk, pre-open + menu board, Thuê người (hire Bé Tí + Chú Bảy) and Trang trí quán (lanterns, tablecloth, flowers, sign) in Bà Tư's dialog, the decorated raft, "Mở quán", service rush with staff, serves and coins, early close → DayResult, night dock shop pop-up |

## How it was made

`node tools/capture_media.mjs` (add `--stills` or `--video` for one part, `--base http://127.0.0.1:8096` to use a server
that is already running; otherwise the script starts `python3 -m http.server` on a free port).

- Launches system Chrome headless and drives it over the DevTools Protocol (Node ≥ 21, no npm packages).
  The viewport is 1200×675 CSS px at DPR 1.0667, so the game's 2.5× fit fills an exact 1280×720 frame.
- The game is opened with `?debug` and driven only through `window.__chonoi` (`go`, `step`, `input`, `phone`) and
  synthetic `KeyboardEvent`s. The game code is unchanged. Before load the script injects a seeded `Math.random` and a
  holdable `requestAnimationFrame`, so each captured frame comes from `__chonoi.step(n)` and runs are repeatable.
- Diving, harpoon shots, flower picking and walking come from small key-steering helpers. The quán service bot reads
  the live state every step: it cooks a dish a seated guest ordered at a free stove (E, arrow keys to that dish's index
  in the cook menu, E), waits, picks it up (E), walks to that guest's table and serves (E). It never presses Esc outside
  a menu (Esc pauses the quán). Closing early is C twice within 3 s; the raft's closing panel then leads to the DayResult
  pop-up and the night dock (`go("night")` is no longer needed).
- One video run records in this order: title → demo dive `go("gather")` (deep zone, Cá Sấu chase + stun; recorded
  before `go("new")` because a new game resets the save; during this unsaved demo dive only, a capture-side guard keeps
  HP and O₂ topped up so the chase never ends in "Ngất xỉu") → the real campaign (intro → Ngày 1 → dive → dusk → pre-open →
  Bà Tư dialog: hire + décor → Mở quán → the evening played off camera by the bot → early close → DayResult → night dock shop) → demo quán `go("quan")` (demo stock, so the service rush never
  runs out; the staff and décor bought in the campaign carry into it, so Bé Tí and Chú Bảy work the rush). The
  edit puts the segments back in story order. The hire / décor scenes drive Bà Tư's real dialog with arrow keys + E
  (`__navGo(label)`); the only setup is a 2000k wallet (`progress.save.money`) so the purchases go through. Screenshots 09, 14, 19, 20 and 21 are written by this run
  (`--video`); `--stills` writes the others.
- Video: segments are recorded as JPEG frames, mostly 5–6 game frames per 30 fps video frame (≈2.5–3× speed; dialogue
  and pop-ups 2×, the croc chase 1.5×). Frames are converted with `scale=out_range=tv,format=yuv420p`. Caption cards are
  rendered by Chrome (this ffmpeg build has no `drawtext`). ffmpeg joins everything with `xfade` cross-fades into
  H.264 yuv420p, CRF 23, `+faststart`, 30 fps, no audio (game audio is synthesized live and is not captured headless).
