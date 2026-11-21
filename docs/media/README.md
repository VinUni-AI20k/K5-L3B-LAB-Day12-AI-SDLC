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
| `screenshots/09-ca-sau-chase-warning.png` | Cá Sấu Năm Chèo on the hunt, "Thủy quái!" warning border |
| `screenshots/10-inventory-overlay.png` | Inventory (I): catches with freshness bars |
| `screenshots/11-dusk-cutscene-lanterns.png` | Dusk cutscene: "Chiều tà", heading back to the raft |
| `screenshots/12-preopen-raft-mo-quan.png` | Pre-open raft: lanterns, Bà Tư, tonight's menu, "Mở quán ▶" |
| `screenshots/13-menu-board-dac-san.png` | Menu board pop-up: dishes, portions, plan tags |
| `screenshots/14-busy-service.png` | Service rush: guests seated with order bubbles, stove cooking |
| `screenshots/15-ba-tu-dialog.png` | Bà Tư dialog: talk, decorate, chores, hire staff |
| `screenshots/16-phone-overlay.png` | Sen's phone (T): chores, notebook, staff, décor, messages, market |
| `screenshots/17-shop-popup-dock.png` | Night dock: Chợ Chú Sáu shop pop-up (Mua / Bán / Nâng cấp) |
| `screenshots/18-high-contrast-dive-warning.png` | High-contrast mode (H) in the dive with the monster warning |
| `demo.mp4` | Fast playthrough: title, intro, day card, dive, deep zone, Cá Sấu, dock, dusk, pre-open + menu board, service, result, night shop |

## How it was made

`node tools/capture_media.mjs` (add `--stills` or `--video` for one part, `--base http://127.0.0.1:8096` to use a server
that is already running; otherwise the script starts `python3 -m http.server` on a free port).

- Launches system Chrome headless and drives it over the DevTools Protocol (Node ≥ 21, no npm packages).
  The viewport is 1200×675 CSS px at DPR 1.0667, so the game's 2.5× fit fills an exact 1280×720 frame.
- The game is opened with `?debug` and driven only through `window.__chonoi` (`go`, `step`, `input`, `phone`) and
  synthetic `KeyboardEvent`s. The game code is unchanged. Before load the script injects a seeded `Math.random` and a
  holdable `requestAnimationFrame`, so each captured frame comes from `__chonoi.step(n)` and runs are repeatable.
- Diving, harpoon shots, flower picking and walking come from small key-steering helpers. A simple bot plays the
  quán service (stove menu → carry → table). Deep-zone and Cá Sấu shots come from a separate demo dive (`go("gather")`),
  so fainting never loses the campaign haul. The shop shot uses the debug shortcut `go("night")`.
- Video: segments are recorded as JPEG frames with 2–6 game frames per video frame (2–6× speed). Caption cards are
  rendered by Chrome (this ffmpeg build has no `drawtext`). ffmpeg joins everything with `xfade` cross-fades into
  H.264 yuv420p, CRF 23, `+faststart`, 30 fps, no audio (game audio is synthesized live and is not captured headless).
