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
| `screenshots/22-upgrades-shop.png` | Night dock, Chợ Chú Sáu "Nâng cấp" tab: Bình oxy bought, "có hiệu lực từ ngày mai" |
| `screenshots/23-day2-deep-dive-upgraded.png` | Day 2 deep dive with the upgrades (O₂ 45 s, 4 Máu, Lao ×5): hunting a big cá lóc bông in the deep zone |
| `screenshots/24-premium-dish-served.png` | Day-2 evening: Cá lóc bông hấp bầu (Đặc sản) served for +220k, trained Chú Bảy at the stove, Bé Tí on the floor |
| `demo.mp4` | Two-day story (≈3×): title, intro, Ngày 1 dive (big haul), deep zone + Cá Sấu (demo dive), dusk, pre-open + menu board, Bà Tư: hire Bé Tí + Chú Bảy and decorate, the real Day-1 evening with staff (many serves, coins, tips, queue), early close → KẾT SỔ NGÀY 1, night market upgrades (Bình oxy, Áo phao, Mũi lao ×3, Chân vịt), train Chú Bảy ★★, hammock → Ngày 2 card → morning dock → deeper dive (big cá lóc bông speared, Cá Sấu fought and defeated for thịt cá sấu) → Day-2 evening with an Đặc sản dish |

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
- Two-day story: the Day-1 dive fills the basket off camera (7 cá lóc, cá linh, bông súng twice, bông điên điển) so
  the real Day-1 quán runs a long evening with the bot and the hired staff. At the night dock the script drives the
  shop pop-up (`__shopGo(id)`: Tab to "Nâng cấp", arrows, E) and Bà Tư's dialog (train Chú Bảy), sleeps in the hammock
  and plays Day 2 with the upgrades. Setup values: wallet 2000k before hiring, 3000k before the night market. On both
  campaign dives a capture-side guard only stops fainting (HP ≥ 1, O₂ ≥ 2 s); damage and the 45 s O₂ bar stay real.
- One video run records in this order: title → demo dive `go("gather")` (deep zone, Cá Sấu chase + stun; recorded
  before `go("new")` because a new game resets the save; during this unsaved demo dive only, a capture-side guard keeps
  HP and O₂ topped up so the chase never ends in "Ngất xỉu") → the real campaign (intro → Ngày 1 → dive → dusk → pre-open →
  Bà Tư dialog: hire + décor → Mở quán → the evening with the bot and staff → early close → DayResult → night market upgrades → train → hammock) → Day 2
  (morning dock → deeper dive → Day-2 evening). The edit puts the segments back in story order. The hire / décor scenes drive Bà Tư's real dialog with arrow keys + E
  (`__navGo(label)`); the only setup is a 2000k wallet (`progress.save.money`) so the purchases go through. Screenshots 09, 14 and 19–24 are written by this run
  (`--video`); `--stills` writes the others.
- Video: segments are recorded as JPEG frames, mostly 5–6 game frames per 30 fps video frame (≈2.5–3× speed; dialogue
  and pop-ups 2×, the croc chase 1.5×). Frames are converted with `scale=out_range=tv,format=yuv420p`. Caption cards are
  rendered by Chrome (this ffmpeg build has no `drawtext`). ffmpeg joins everything with `xfade` cross-fades into
  H.264 yuv420p, CRF 23, `+faststart`, 30 fps, no audio (game audio is synthesized live and is not captured headless).
