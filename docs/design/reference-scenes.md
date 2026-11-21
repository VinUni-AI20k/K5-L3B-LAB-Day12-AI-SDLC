# Reference board: how Dave the Diver presents its scenes

This board supports our original game **Quán Ăn Chợ Nổi**: diving in a Mekong floating market by day and running a raft restaurant (nhà bè) by night. We study *Dave the Diver* (MINTROCKET, 2023) for composition, camera, UI placement and flow. We do not copy its assets, characters, layouts pixel-for-pixel, or its IP.

**Rules for this file**
- Links only. All images are © MINTROCKET / NEXON or the site that captured them. Nothing is downloaded into the repo.
- Quotes are at most 15 words each and attributed.
- I viewed every screenshot described below (thumbnails opened outside the repo, 2026-11-21). Where a source's file name or caption does not match what the image shows, the description follows the image and the mismatch is flagged.
- Our canvas is **480 × 270** (`client/src/engine.js`), the same 16:9 ratio as DtD's 1920 × 1080. Percentages below map directly: 10% of height = 27 px and 10% of width = 48 px.

**Link bases used below**
- Steam: `https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1868140/ss_<id>.1920x1080.jpg`. The `.600x338.jpg` suffix gives a thumbnail. Store page: https://store.steampowered.com/app/1868140/DAVE_THE_DIVER/
- Nintendo eShop: `https://assets.nintendo.com/image/upload/w_800/f_jpg/q_auto/store/software/switch/70010000060372/<hash>`. Page: https://www.nintendo.com/us/store/products/dave-the-diver-switch/
- teemo.dev media: `https://teemo.dev/game-design/dave-the-diver/media/<file>`. Systems index: https://teemo.dev/game-design/dave-the-diver/design/

---

## Summary

| # | DtD scene | Our planned equivalent | Priority |
|---|---|---|---|
| 1 | Diving and exploration (reef, deep biomes, night dive, O2/depth/weight HUD) | `scene_gather.js` river dive + `deep.js` deep zone below 30 m; surface flower picking (bông điên điển, bông súng) | **P0** |
| 2 | Capture and combat (harpoon, net, sleep dart, bosses) | `catch` on fish schools; snake stun (`creatures.js`); optional big-fish set piece | **P1** |
| 3 | Boat, dock, return and expedition results | Sampan returns to the raft or landing; "Lặn & Hái" summary feeding the `kho` inventory file | **P1** |
| 4 | Restaurant SERVICE (side view, counter, kitchen, customers, HUD) | `scene_quan.js` night raft side view: the scene being rebuilt now | **P0** |
| 5 | Restaurant PREP (menu, ingredients, staff) | `scene_shop.js` mode `"evening"` (Thực đơn + Nâng cấp quán) | **P0** |
| 6 | Night settlement and daily results | `scene_shop.js` mode `"results"` (Kết sổ) | **P0** |
| 7 | Equipment, upgrade shop and weapon upgrades | `scene_shop.js` mode `"morning"` (Đồ lặn tab) | **P1** |
| 8 | Farming and fish breeding | Optional: floating garden or fish cage (lồng bè) under the raft | P3 |
| 9 | Phone and app menus (catalog, missions, social) | Sổ tay cá tab; maybe a market-gossip "loa phường" or reputation card | P2 |
| 10 | Story cutscenes and character intro cards | `cutscene.js` + `story.js` (dawn/dusk/night river world) | **P1** |
| 11 | World map and biome selection | Not needed for v1. Depth bands and a river-reach choice can come later | P3 |
| 12 | Minigames and events | One service minigame (pouring nước mắm / cà phê sữa đá), market-day events | P2 |

---

## 1. Diving and exploration

**Images**
- Dive HUD in play (shallows, early game): https://www.gamepressure.com/dave-the-diver/gfx/word/1542161828.jpg (on https://www.gamepressure.com/dave-the-diver/how-to-increase-oxygen-supply/z210d58)
- Shallow reef, bright: Steam `ss_6eac5a3b59e181d1ffa26757b041be521bfe1779`, Steam `ss_ffa38dcd56c15a949178cf7074c9b044ade9c3a4` (used on https://teemo.dev/game-design/dave-the-diver/systems/procedural-reef-and-fishing-harpoon/)
- Chasm with pixel Dave between 3D cliffs: Steam `ss_7c86a17d545b6260ecdcfdd62622e49dcc9011bd`; Nintendo hash `dd989bb47f20731d114ca4060d5f8ae31ba51ce1d067e2132c22174fe52be5e3`
- Mid-depth teal terraces, wreck and weapon crate: Steam `ss_a7fc1cb93030e790706ac85645034c844fd04c05`. Two teemo pages caption this image differently. The image shows the wreck and crate.
- Dark cave with headlamp cone (deep or night look): Steam `ss_3a459e9ea8b54c3864379fcad38bff3ae7fe4e8c`
- Glacier zone (inverted value key): Steam `ss_9f8cb11c51ef285b43f0eb908c586d81fe57573a`
- Article on art direction for these frames: https://teemo.dev/game-design/dave-the-diver/systems/art-direction-and-visual-language/

**Composition**
- **Camera:** A side-on 2.5D view. Dave is a small hand-drawn pixel sprite, about 4–6% of screen height, near the centre. Terrain is flat-shaded, low-poly 3D in stacked terraces. Fog fades the far layers, and that fade is the main depth cue (teemo.dev, art direction).
- **Colour by depth:** The shallows are saturated cyan with pink and purple coral. Mid-depth turns teal and desaturated. The deep or night look is near-black with a single cone of light from Dave's lamp. The glacier zone flips the value key: a pale cyan field with a dark diver.
- **HUD (screenshot 1542161828):**
  - **Bottom-left cluster:** a circular O₂ gauge showing a number (134), and beside it the depth ("12.8m") and weight ("0.4/19.0kg") on one dark plate labelled "Normal Depth".
  - **Bottom-right:** three item and weapon slots (melee, gun, harpoon with "Lv.1"), each with its button glyph.
  - **Mid-left:** a quest tracker card.
  - **Top-centre:** a world-space objective marker (a green pin with a distance, "120m").
  - **Centre-bottom:** a pickup tooltip card.
  - The top-right and the whole centre stay clear for the playfield.
- **Pressure and warnings:** Guides say the depth readout turns red past the suit's limit, and O₂ drains faster there. Oxygen is the only element with an escalating multi-channel warning (teemo.dev, UX/UI page).

**Lessons for Quán Ăn Chợ Nổi**
1. **Group survival stats in one corner.** Put breath, depth and basket weight in one bottom-left plate, and keep the top of the screen clear so the surface line, sky and boats stay visible. At 480 × 270 that is a plate about 90 × 30 px at (6, 234).
2. **Let colour carry depth.** Do not add more UI for it. Shift from warm, silty brown-green near the surface (phù sa) to dark olive, then to near-black with a lamp cone in `deep.js`. The muddy Mekong palette should be our own identity, not DtD's tropical cyan.
3. **Do not copy** the circular O₂ dial or the low-poly terrace look. Our river is shallow, murky and full of roots and hyacinth (lục bình), not a coral reef.

## 2. Capture and combat

**Images**
- Shark at mid-depth, harpoon aim arc toward the target, a lit crate in the foreground: Nintendo hash `2470dfe45d4cb30ffa663766865cef17cbe6be190242966b1ea3f4d09529bb6f`
- Boss, Giant Mantis Shrimp, in a dark wreck: Nintendo hash `9209ba8000327d8e8d10f21c1a0ff17fc957a3a7905a4b8d597626dd84e1d21d`. A letterboxed version with a motion-blur punch is Steam `ss_52b5730f94d6a6cfab5491faa125497f4e63209e`.
- Giant eel boss closing on a tiny lit Dave: Steam `ss_dad710e3c4e6b818fa0a935b25a1fc31e73188a5`
- Marlin charge with speed lines in darkness: Steam `ss_92a713e2f0ce374a446367c57f962ef942b2c173`
- Weapon icons (harpoon tiers, net gun, Hush Dart) on https://teemo.dev/game-design/dave-the-diver/systems/diving-controls-oxygen-weapons/, for example `media/weapon-small-net-gun.png` and `media/weapon-hush-dart.png`
- Feel breakdown: https://teemo.dev/game-design/dave-the-diver/systems/game-feel-and-juice/

**Composition**
- **Boss scale:** Bosses fill 40–60% of the frame and are usually offset right, with Dave small on the left. The only light comes from the creature's own glow (eye, lure, fins) and Dave's lamp.
- **Takeover moments:** Letterbox bars mark camera takeover.
- **Shared effects vocabulary:** motion blur for strikes, bubble spray, speed lines for charges, and a white flash for criticals (teemo.dev, game feel).
- **Harpoon sequence:** wind-up, a visible dragged spear arc (not a hitscan line), a hit-stop freeze, a bubble burst, a star-grade badge, then the catch slides into a cargo slot.
- **Grading:** Catch grade depends on *how* the fish is caught. Netting or sedating gives ★★★, harpooning alive ★★, killing ★.

**Lessons**
1. **A small, reusable effects set** (speed lines, bubble burst, hit-stop, flash) makes every encounter read as dramatic. `cutscene.js` already exports `speedLines`. Reuse it for the snake lunge and the big cá lóc escape instead of drawing bespoke effects.
2. **Reward the gentle method.** "Catch alive = better ingredient" fits our river theme (net or trap, not spear), and it gives the restaurant a reason to care how the player gathered.
3. **Do not copy** the gun arsenal or the boss roster. Keep combat light: stun or avoid a snake, and outlast a big fish. Off-screen threats need a screen-edge marker, which DtD lacks (teemo.dev notes this as a weakness).

## 3. Boat, dock, return and expedition results

**Images**
- The boat in a sunlit bay with the restaurant hut on the far shore: Steam `ss_bc9150385c6fcd41ac7195be36597469f54a792c` (on https://teemo.dev/game-design/dave-the-diver/systems/core-loop-day-dive/)
- Boat on bright water, side view: https://www.ludo.guide/images/screenshots/dave-the-diver/shot-3.webp (on https://www.ludo.guide/guide/dave-the-diver/diving-mechanics-explained)
- The boat as the backdrop for the upgrade popup and Cobra's shop: https://www.gamepressure.com/dave-the-diver/gfx/word/1542161781.jpg and https://www.gamepressure.com/dave-the-diver/gfx/word/1542161796.jpg
- The night boat behind a phone overlay: https://nfapi.noobfeed.com/storage/media/47489/Dave-the-Diver-Guide_-9-Essential-Tips-and-Tricks-for-Beginners-5-56-screenshot.jpg

**Composition**
- **The boat scene:** The boat sits low-left at the waterline. The horizon is around 55–60% of the height, with karst cliffs left and right and the restaurant hut small on the far right shore. Morning means a bright sky and sun glare. Night means a dark sky, a lit boat and a lit restaurant across the water.
- **One bay, no loading screen:** The boat and restaurant share one bay, so moving between them is a walk across one scene (teemo.dev, core loop).
- **Popups over the boat:** Upgrades, shops and the phone appear as centred cards over a *live, dimmed* boat scene, never on a separate blank screen.
- **No dive results screen:** DtD shows no separate expedition-results screen. The catch goes into cargo during the dive, and the day's real ledger is the nightly results (§6). If air runs out, Dave is rescued and loses part of his cargo.

**Lessons**
1. **Keep the raft visible from the dive start.** Put the restaurant raft in the background of the gather scene's surface view. Our `story.js` `riverWorld` side cross-section can do this, so the player always sees where the catch is going.
2. **Overlay menus on a dimmed world.** Shops and summaries should sit on a 60–70% dark scrim over the current scene. Do not cut to a black menu.
3. **Do not copy** the ocean, the karst bay or the boat design. Use a Mekong sampan (xuồng ba lá) with river banks, coconut palms and stilt houses.

## 4. Restaurant SERVICE view (most important)

**Images**
- Full house at night, with HUD and bottom bar: Steam `ss_783e1f6c2d4c358fb494d055c47c0e888922abd5`. This is the frame measured in the final section. Used on https://teemo.dev/game-design/dave-the-diver/systems/ux-ui-and-accessibility/, which calls it "The densest UI frame in the game" (teemo.dev).
- Earlier, busy service: Nintendo hash `caab0d00fa4c704b1f86ad6f19212b4c9bb55d8f65dae97d0fc1a690282256b4`
- Early game, few customers, Dave carrying an order, kitchen window at right: https://nfapi.noobfeed.com/storage/media/47491/Dave-the-Diver-Guide_-9-Essential-Tips-and-Tricks-for-Beginners-5-16-screenshot.jpg (on https://noobfeed.com/articles/dave-the-diver-restaurants-essential-tips)
- Diamond rank, full room with staff: https://teemo.dev/game-design/dave-the-diver/media/cooksta-diamond-rank.jpg (on https://teemo.dev/game-design/dave-the-diver/systems/restaurant-management-menu-staff/)
- Bancho Grill (DLC), a wider multi-direction layout, for contrast: hero image on https://www.gamebrief.net/blog/dave-the-diver-bancho-grill-recipes-jungle-2026. GameBrief says base Bancho Sushi "runs on one long counter".

**Composition (measured on `ss_783e…`)**
- **Camera:** Strict side view at eye level, from the *customer side*. Customers sit on stools with their backs to us. Dave works behind the counter facing the camera, and the back-bar shelves sit behind him.
- **Open structure:** There is no front wall and no side walls, only roof beams, posts, hanging lanterns and a roof valance. Through the gap between the back-bar and the roof you see the dusk sea and cliffs. The restaurant is a lit stage set inside a dark landscape.
- **One horizontal service lane:** The counter runs almost the full width, about 13% to 100%. All seats are on one row, Dave moves left and right only, and the kitchen is a bright, cyan-lit window at the right end where the chef works.
- **Order bubbles:** These float in one horizontal band just above the customers' heads (y about 57–68%). Each is a white circle with a dish icon. The current target is enlarged and glows, and it shows a button prompt. Short reaction captions ("This looks good!") sit under the bubbles in small white text.
- **HUD framing:**
  - **Top band (0–10%):** gold (top-left), the social/rank card (left-centre), an "OPEN" neon sign (top-centre, diegetic), and the date with a weather icon (top-right).
  - **Upper-left (11–22%):** the quest tracker.
  - **Upper-right (10–30%):** a big clock dial showing the evening segment, with "Time Skip" below it.
  - **Right edge, mid-height:** dish-stock and refill gauges, plus a vertical stamina or tool bar.
  - **Left edge (~55%):** an "EXIT" arrow.
  - **Bottom bar (87–100%), solid dark:** the phone icon far left; Menu, Research, Staff, Ingredients and Interior tabs centred, with numbered keys.
- **Light and colour:** A warm interior (lantern yellow, wood brown, magenta and pink neon) against a cool blue-violet exterior. The kitchen window is the one cool, bright cyan block. That contrast makes the kitchen the visual anchor.

**Lessons**
1. **Use one lane, read left to right:** door, seats, then kitchen pass. The player always knows where the food comes from (right) and where customers enter (left).
2. **Give orders a dedicated band** above the heads, at a fixed height. Mark the active order bigger with a glow and a key hint.
3. **Do not copy** the sushi counter, the neon "EAT DRINK LOVE" sign, the cherry blossoms, the Cooksta card, the pink and magenta palette, or the exact HUD shapes. Our version is a nhà bè with lanterns, low tables and stools on a wooden deck over the river. Detailed guidance is in the final section.

## 5. Restaurant PREP (menu, ingredients, staff)

**Images**
- The five-tab bottom bar (Menu / Research / Staff / Ingredients / Interior) during service: Steam `ss_783e…` and Steam `ss_391a1c5adf618fbcd1bec89e25e0ac54bb4d915f`
- Research tutorial card, with the bar scene on the left and a dish grid on the right: https://teemo.dev/game-design/dave-the-diver/media/research-artisans-flame.jpg
- Hire-staff tutorial card over the dining room: https://teemo.dev/game-design/dave-the-diver/media/recruitment-ads.jpg. The file name says recruitment ads, but the image is the "Hire employees" tutorial card.
- Text sources on menu setup, Auto Supply and enhancement: https://noobfeed.com/articles/dave-the-diver-restaurants-essential-tips, https://dotesports.com/dave-the-diver/news/what-is-auto-supply-in-dave-the-diver-answered, https://teemo.dev/game-design/dave-the-diver/systems/restaurant-management-menu-staff/
- **Gap:** I found no public, clearly captioned screenshot of the menu-selection panel itself.

**Composition and flow**
- **Prep lives inside the restaurant.** It is reached from the bottom bar, and the restaurant stays visible behind or beside the panel. Opening the menu pauses the shift, and the stock board behind Dave shows the remaining dishes (noobfeed).
- **Tutorial cards share one template:** a framed illustration on top, two or three lines of text below with key words highlighted in yellow, and a single magenta "OK" button.
- **Menu rules:** A fixed number of slots, which grows with rank. Each dish shows price, taste and servings. Ingredients are consumed when a dish joins the menu, and an Auto Supply toggle restocks a dish mid-service (teemo.dev, restaurant page).
- **Staff:** Two cooks and two servers can be active, with the rest in a waiting room. Stats are Cooking, Serving, Procure and Appeal (noobfeed).

**Lessons**
1. **Run prep as one panel over the dimmed raft.** Our `"evening"` mode should show the empty raft behind the Thực đơn panel so the player is literally "setting up the quán".
2. **Show per dish:** its icon, the ingredient cost from `kho` (for example 1 cá lóc + 1 bông súng), the price, and the servings you can make. Grey out dishes the kho cannot cover. That is the whole decision.
3. **Do not copy** five tabs, a research currency or staff stats for v1. One menu tab, plus an upgrade tab, is enough for a 3-hour lab.

## 6. Night settlement and daily results

**Images**
- Results screen: https://teemo.dev/game-design/dave-the-diver/media/nightly-wrap-score.jpg (on https://teemo.dev/game-design/dave-the-diver/systems/core-loop-day-dive/)
- Results with follower gauge and ledger: https://teemo.dev/game-design/dave-the-diver/media/cooksta-follower-gauge-and-ledger.jpg (on https://teemo.dev/game-design/dave-the-diver/systems/rebuild-blueprint/)

**Composition**
- **Top strip:** "Today's Score" with five stars and a big number ("5.0"), a flame-currency line ("You earned Artisan's Flame"), and the chef portrait cut in at top-right. The portrait gives the verdict a face.
- **Card columns below**, on a light paper-like background:
  - *Left:* the rank card with a follower bar, plus "New / Total" follower counts.
  - *Middle:* the "Top Sales" dish card (icon, level, price, taste, count) and a "Top Sales (Last 7 Days)" strip of three dish icons.
  - *Right:* the "Balance" chart (sales versus expenses bars by day, with today highlighted), a ledger table (Cooking, Others, Tips / Operation, Pay, Maintenance), and the "Net Profit" pill at the bottom.
- The score maps directly to the reward. A 5 requires that no customer left unhappy (teemo.dev, restaurant page).

**Lessons**
1. **Lead with one emotional number,** then the breakdown. Our Kết sổ should open with the stars (reputation, clamped 0–5) and today's score (`earned + 100 × floor(reputation)`), then itemise dish sales, tips and customers who left.
2. **Put a character portrait on the verdict.** Út Sen or the market auntie reacting turns a spreadsheet into a story beat.
3. **Do not copy** the multi-day bar chart for v1. At 480 × 270 it is unreadable. A three-line ledger plus "best dish of the night" is enough.

## 7. Equipment, upgrade shop and weapon upgrades

**Images**
- Diver Box loadout (Harpoon Gun, Melee Weapon, Gun and two Charm slots above a storage grid): https://teemo.dev/game-design/dave-the-diver/media/equipment-persistent-loadout.jpg. A second copy is at `media/idiver-equipment-panel.jpg`; despite the file name, that image also shows the Diver Box.
- Diver Box over the boat with an item detail card and a "Swap" button: https://www.gamepressure.com/dave-the-diver/gfx/word/1542161843.jpg
- iDiver "UPGRADE" popup (Air Tank Lv.3) as a phone overlay on the boat: https://www.gamepressure.com/dave-the-diver/gfx/word/1542161781.jpg
- Cobra's Premium Shop, with the vendor portrait at left and a three-item card: https://www.gamepressure.com/dave-the-diver/gfx/word/1542161796.jpg
- Weapon craft tree (TripleAxel / RedSniper / NetGun with % progress): https://teemo.dev/game-design/dave-the-diver/media/weapon-contents-guide.jpg
- Gear icons and tier ladder: https://teemo.dev/game-design/dave-the-diver/systems/gear-weapon-and-gun-upgrade/

**Composition**
- **Shop panels sit centre-screen** over the live boat scene, with gold at top-left. The vendor stands full-body beside the panel (Cobra at the left edge), which makes the shop a *person*, not a menu.
- **Each upgrade is a single big card:** an icon, the stat name, "Lv.3", one line of effect text ("You can dive longer."), and OK.
- **The loadout grid is dark teal with cyan borders,** the same palette as the dive HUD, so gear UI feels like it belongs to the underwater half.

**Lessons**
1. **Give every upgrade one card with one sentence of effect** (for example "Giỏ to hơn: mang thêm 2 con cá"), plus a big before-and-after number.
2. **Put the seller beside the shop.** A chibi or portrait of the seller (ông Ba bán đồ lặn) next to the panel costs one sprite and adds a lot of warmth.
3. **Do not copy** the weapon crafting tree, crate guns or charms. Keep a short flat ladder: basket size, breath, lamp, net.

## 8. Farming and fish breeding

**Images**
- "NEW FISH / 1 DAY" breeding card (fish list at left, arrow, newborn panel at right): https://teemo.dev/game-design/dave-the-diver/media/fish-farm-breeding-panel.jpg. `media/fish-farm-tanks.jpg` shows the same card.
- Eggs to fish-farm tank tutorial: https://teemo.dev/game-design/dave-the-diver/media/fish-farm-eggs.jpg
- "You can now visit the Farm" card (SUSHI / FARM signposts leading to crop rows): https://teemo.dev/game-design/dave-the-diver/media/ottos-farm-paddy.jpg
- System write-up: https://teemo.dev/game-design/dave-the-diver/systems/meta-systems-farms-breeding/

**Composition**
- **Unlock cards:** Each farm feature is introduced by a "before → arrow → after" illustration card in warm yellow and orange, with one big arrow in the middle. Tank screens show density as a percentage bar instead of a headcount.

**Lessons**
1. **Use "before → after" unlock cards.** They teach any new system in one image. Use one for "lồng cá dưới bè" (a fish cage under the raft) if we ever add it.
2. **Defer farming.** It is P3 for the lab. If added, it should fit the river: a fish cage tied under the nhà bè or a floating vegetable raft, not a land farm.

## 9. Phone and app menus

**Images**
- Phone home screen (yellow handset with an app grid: Cooksta, iDiver, Map/Tips, Calendar, Marinca, FishMon and others): https://teemo.dev/game-design/dave-the-diver/media/phone-home-screen.png
- Cooksta "Rank Up" app as a centred phone over the night boat: https://nfapi.noobfeed.com/storage/media/47489/Dave-the-Diver-Guide_-9-Essential-Tips-and-Tricks-for-Beginners-5-56-screenshot.jpg
- Cooksta tutorial (timeline feed plus a rank reward strip): https://teemo.dev/game-design/dave-the-diver/media/cooksta-app.jpg
- UX analysis: https://teemo.dev/game-design/dave-the-diver/systems/ux-ui-and-accessibility/

**Composition**
- **The phone is a diegetic container.** A portrait handset sits centred and fills about 85% of the height over the dimmed world, with Timeline, Rank Up and My Page tabs. Its pastel pink and white UI contrasts with the dark world behind it.
- **The home screen grew to 20+ icons** without any navigation restructure (teemo.dev). This works because new systems arrive as "one more app".

**Lessons**
1. **Use one diegetic container for all meta screens.** For us that could be Út Sen's notebook (sổ tay) or a market noticeboard: Sổ tay cá, today's orders, reputation. Adding a feature then means adding a page, not a new screen type.
2. **Do not copy** the smartphone or a social-media parody. A hand-written notebook or a chalkboard fits a floating-market setting better and avoids the DtD fingerprint.

## 10. Story cutscenes and character intro cards

**Images**
- Cold-open phone call in a split composition over a beach: https://teemo.dev/game-design/dave-the-diver/media/dtd-cobra-intro-call.jpg (on https://teemo.dev/game-design/dave-the-diver/systems/onboarding-and-first-session/)
- Grounded register (chef at the cutting board, letterboxed, single spotlight): Steam `ss_264faf6cbb2d4466c2a10f9e03fe1487e0615379`
- Absurd register (anime-parody glasses flash): Steam `ss_5c674ff5ae1969b21a1b4903dfd964298fad3017`. `media/dtd-duff-enhancement-ui.jpg` on teemo.dev also shows a comedic cutscene, not the Duff UI its name suggests.
- Mythic register (ceremony before a giant statue): Steam `ss_d1c0a418890d7dce6fc1ef88e0ab038c12ca69d7`
- Big reaction frame (character shocked in front of a pixel wave with glowing jellyfish): Nintendo hash `53855d5be28bd21cf36ef8e203eba73a2e16b699682a776a52256653b1f006ec`
- Ensemble group shot: https://teemo.dev/game-design/dave-the-diver/media/dtd-epilogue-friends.jpg
- Cast portraits used as intro cards: `media/dtd-portrait-cobra.png`, `media/dtd-portrait-bancho.png`, `media/dtd-portrait-duff.png`, `media/dtd-portrait-dr-bacon.png` (teemo.dev onboarding page)
- Key art: Nintendo hash `e77cbe3c83da8de952bce5bc0f0960092dbc2e08d377f0e082673239322301bb`

**Composition**
- **Higher-resolution art:** Cutscenes are drawn at a much higher resolution than gameplay sprites, with close-ups of faces and hands.
- **Framing:** Cutscenes are letterboxed. Lighting is either a single spotlight against a dark background (grounded) or a flat graphic background such as a wave pattern or a radial burst (comic).
- **Characters own systems:** Each character is introduced with the system they teach. Cobra brings the premise and the shop, Bancho the kitchen, Duff weapons, Dr. Bacon depth (teemo.dev, onboarding).

**Lessons**
1. **Tie each NPC intro to the mechanic they teach.** Example: bà Tư (market) introduces the menu, chú Năm (boatman) introduces diving, and a rival quán owner introduces reputation.
2. **Use three tonal registers on purpose:** grounded (cooking close-ups), comic (big reaction frame with speed lines), and mythic (river legend at night). Our `cutscene.js` comic effects already support the second.
3. **Do not copy** the parody gags or the cast archetypes, such as the Hawaiian-shirt boss. Use Mekong characters and humour (đờn ca tài tử, chợ nổi banter).

## 11. World map and biome selection

**Images (proxies; no map screen exists)**
- Sea People village hub (a pastel terraced town that breaks the desaturated palette): Steam `ss_168528c86261f98aeb64192dc34025a4b361ff4a` (on https://teemo.dev/game-design/dave-the-diver/systems/rebuild-blueprint/)
- The bay connecting boat and restaurant: Steam `ss_bc9150385c6fcd41ac7195be36597469f54a792c`
- Location write-ups: https://progameguides.com/dave-the-diver/dave-the-diver-map-all-underwater-locations and https://primagames.com/?p=321108 (night diving)

**What DtD does**
- **No world map:** I found no world-map or destination-select screen in any source. Guides note there is no map or minimap while diving.
- **Depth is the map:** Areas are gated by capability. Suit depth levels from 40 to 540 m unlock bands (Shallows, Medium, Depths, Glacier, Hydrothermal Vents).
- **Night dive:** A flag on the same terrain that swaps the species roster and lighting. It costs one third of that evening's service (teemo.dev; primagames).
- **Village hub:** The village is reached via a mirror, a diegetic portal back to the boat.

**Lessons**
1. **Use depth as progression.** Our deep zone in `deep.js` (below 30 m) already works like this. Gate it with a breath upgrade rather than a map.
2. **Night dive as a variant:** Same river geometry, new palette (lantern-lit, fireflies, different fish), with a cost paid out of restaurant time. It is a cheap content multiplier and fits our day/night theme.

## 12. Minigames and events

**Images**
- Cocktail pour ("Pour So That About 20% Is Foam", target glass beside player glass, "PERFECT" banner) shown on a screen above the bar during live service: Steam `ss_391a1c5adf618fbcd1bec89e25e0ac54bb4d915f`
- Wasabi or sauce pour ("Pour The Right Amount!", "PERFECT"), a framed panel over the live service: https://nfapi.noobfeed.com/storage/media/47490/Dave-the-Diver-Guide_-9-Essential-Tips-and-Tricks-for-Beginners-5-31-screenshot.jpg
- Mask-framed interaction minigame (the view clipped to a diving-mask shape, a reticle and a "Move" prompt): Nintendo hash `fe8afc6b0e1191c47bef1928d2bc01c82463c1f3722bbeb2da8274330dc9f6cb`. I could not confirm which minigame this is.
- Catch minigames per harpoon tip (mash, directional, timed bar, mouse rotation): https://teemo.dev/game-design/dave-the-diver/systems/procedural-reef-and-fishing-harpoon/

**Composition**
- **Service minigames never leave the restaurant.** They open as a framed panel over the top-centre or centre of the live scene, so the customers and HUD stay visible around it. Each has a one-line instruction strip on top, the target and the player's attempt side by side, and a large italic "PERFECT" stamp.
- **Changing the frame changes the mode.** Dive minigames swap the camera mask (the goggles shape) to signal a mode change without a scene change.

**Lessons**
1. **Run one minigame per night,** opened in-scene over the raft. For example: pour cà phê sữa đá to the line, or ladle nước mắm into a chén. The skeleton is target versus attempt plus a "NGON!" stamp.
2. **Reuse the stamp grammar** (PERFECT / GOOD / MISS) for catches and service, so the player learns one feedback language.
3. **Do not copy** the bar-screen framing or the cocktail itself.

---

## Restaurant: why the open side view works

### What the frame does (measured on Steam `ss_783e1f6c2d4c358fb494d055c47c0e888922abd5`, 10% grid)

```
 y%  0 ┌──────────────────────────────────────────────────────────────┐
       │ [gold] [rank/social]        (OPEN sign)         [date/weather]│  HUD band 0–10%
    10 │ [quest card]   ~~roof valance + lanterns~~       ( clock dial )│  10–22%
    22 │                                                  [time skip]  │
       │      open sky / sea / cliffs seen THROUGH the structure       │  scenic layer 22–60%
    33 │      ═══ back-bar shelf: bottles ═══      ▌                   │
    40 │      [dish stock board]                   ▌  [stock gauges]  ▐│  stamina bar at right edge
    55 │◄EXIT                                      ▌                   │
    57 │   (o) (o)  (O*) (o)   (o)  (o)   (o)                          │  order-bubble band 57–68%
    63 │   heads  heads  DAVE heads heads  heads    ┃ KITCHEN WINDOW ┃  │
    71 │ ══════════════ COUNTER (13% → 100%) ═══════╋════════════════╋═│  counter top 71–75%
    78 │   stool  stool  stool  stool  stool  stool  ┃  (chef, cyan)  ┃  │  stools 78–84%
    86 ├──────────────────────────────────────────────────────────────┤
       │[phone]        [Menu] [Research] [Staff] [Ingr.] [Interior]   │  bottom bar 87–100%
   100 └──────────────────────────────────────────────────────────────┘
```

### Why it works
1. **The whole loop sits on one line.** Door (left), seats, then kitchen pass (right). The service lane, the counter and the orders are all horizontal bands, so the eye scans left to right and never searches in depth. Our earlier attempts mixed several rows of tables in depth (z) and lost this.
2. **Open walls give context for free.** With no front wall, everyone is visible. With no back wall, the landscape is visible, so the restaurant feels *located* in the world the player dove in that morning. It also means the backdrop can change with the day or time without touching gameplay.
3. **Warm stage against a cool world.** Warm lantern light on the set, a cool night outside and one cool-bright kitchen window make the three things that matter pop: people, food source and orders.
4. **Orders float in one row,** separate from the bodies. Bubbles never overlap the counter or the HUD, and the active one is enlarged.
5. **The HUD frames the stage and does not cover it.** The top 10–22% and bottom 13% are HUD. The centre band of about 25–85% is pure scene. The only elements inside the stage are diegetic (the OPEN sign, the stock board) or sit at the very edge (the stock gauges and EXIT).

### Concrete layout for our 480 × 270 nhà bè (`scene_quan.js`)

| Band (y, px) | % of height | Content | Notes for us |
|---|---|---|---|
| 0–26 | 0–10% | **Top HUD:** coins (left), reputation stars 0–5 (left-centre), night clock (right) | Small plates with a 4 px margin. A diegetic "ĐANG BÁN" lantern sign at top-centre can replace "OPEN". |
| 26–60 | 10–22% | Roof edge (mái lá or tôn), lantern string, today's goal card at top-left (optional) | The roof must cut off at about y 60 so the sky shows below it. |
| 60–150 | 22–55% | **Scenic layer through the open raft:** night river, chợ nổi boats with bẹo poles and hanging produce, far bank lights, moon | Parallax only, with no gameplay in it. The menu board (bảng món, dishes left) hangs on a back post at about y 95–130. |
| 150–178 | 55–66% | **Order-bubble band** | Fixed y. Bubble about 18 px with a dish icon (`dishIcon`). The active one is 1.3× with a glow and the E key hint. Patience shows as a ring around the bubble, not a separate bar. |
| 170–200 | 63–74% | Customer heads and bodies seated at low tables (bàn thấp, ghế đẩu) in **one row**; Út Sen walks a lane just behind or in front of them | Pick one: (a) customers back-to-camera with Út Sen behind the counter (DtD style), or (b) customers in profile at low tables with Út Sen walking the front of the deck. Option (b) is more Vietnamese and less of a copy. |
| 200–215 | 74–80% | **Deck edge / table line** (the "counter"), spanning about x 40 → 400 | One continuous plank line. It is the eye's horizon for service. |
| 215–236 | 80–87% | Front of the raft: floats or barrels (thùng phuy), water lapping, a **sampan landing at the far left where customers arrive by boat** | This replaces DtD's EXIT arrow with a diegetic entrance: customers paddle in from the left and dock. It is unique to the Mekong setting. |
| 236–270 | 87–100% | **Bottom bar:** dark river band with 2–3 tab icons at centre (Thực đơn, Kho) and the notebook (sổ tay) at far left | Draw it as dark water rather than a black bar, so the HUD feels part of the river. |

**Horizontal split (x)**

| x (px) | % of width | Zone |
|---|---|---|
| 0–40 | 0–8% | Arrival: sampan landing and the queue of boats waiting (khách chờ). Patience is shown here before customers sit. |
| 40–380 | 8–79% | Seating: 5–7 seats, evenly spaced about 48 px apart, so one seat per 10% column. |
| 380–480 | 79–100% | **Kitchen (bếp):** clay stove (`clayStove`), pots, steam (`steam`), a pass counter (`passCounter`) and the cook. Light it as the brightest and warmest block, with fire orange, in the role DtD gives its cyan window. Stock and refill gauges go on the far-right edge at about y 110–160. |

**Sizes and readability at 480 × 270**
- **Characters:** about 28–34 px tall when seated (DtD's customers are about 10–12% of screen height). Út Sen should be about 2 px taller or carry a colour accent so she is never lost in the crowd.
- **Bubble icons:** at least 14 px. Text under bubbles should be very rare at our resolution. Use emoji-free pixel icons and save text for the top HUD.
- **Palette:** warm deck and lantern (amber, brown) versus a cool night river (indigo, teal). Keep one hot spot, the kitchen fire. Avoid DtD's magenta and pink neon.

**Five rules to keep while rebuilding**
1. One service row, read left to right: arrival, seats, kitchen.
2. No front or back walls. The river and the market are visible behind the action.
3. The order band sits at a fixed height above heads, and the active order is enlarged.
4. HUD only in the top ~10% and bottom ~13%. Everything else inside the frame is diegetic.
5. The kitchen is the single brightest block, at one fixed end.

**Do not copy:** the sushi bar, neon signage, cherry blossoms, the Cooksta or social card, the clock-dial art, the five-tab bar, the character designs, or any DtD sprite or colour scheme. Copy only the *principles* above.

---

## Source pages consulted
- teemo.dev Dave the Diver systems series: [rebuild blueprint](https://teemo.dev/game-design/dave-the-diver/systems/rebuild-blueprint/), [core loop](https://teemo.dev/game-design/dave-the-diver/systems/core-loop-day-dive/), [restaurant](https://teemo.dev/game-design/dave-the-diver/systems/restaurant-management-menu-staff/), [meta and farms](https://teemo.dev/game-design/dave-the-diver/systems/meta-systems-farms-breeding/), [UX/UI](https://teemo.dev/game-design/dave-the-diver/systems/ux-ui-and-accessibility/), [art direction](https://teemo.dev/game-design/dave-the-diver/systems/art-direction-and-visual-language/), [oxygen and weapons](https://teemo.dev/game-design/dave-the-diver/systems/diving-controls-oxygen-weapons/), [gear upgrades](https://teemo.dev/game-design/dave-the-diver/systems/gear-weapon-and-gun-upgrade/), [reef and harpoon](https://teemo.dev/game-design/dave-the-diver/systems/procedural-reef-and-fishing-harpoon/), [game feel](https://teemo.dev/game-design/dave-the-diver/systems/game-feel-and-juice/), [narrative](https://teemo.dev/game-design/dave-the-diver/systems/narrative-theme-and-worldbuilding/), [onboarding](https://teemo.dev/game-design/dave-the-diver/systems/onboarding-and-first-session/)
- [Nintendo eShop page](https://www.nintendo.com/us/store/products/dave-the-diver-switch/)
- [Steam store page](https://store.steampowered.com/app/1868140/DAVE_THE_DIVER/). It was not fetchable from here, so the screenshot IDs come from teemo.dev pages that embed them. All were checked as loading.
- [NoobFeed restaurant tips](https://noobfeed.com/articles/dave-the-diver-restaurants-essential-tips), [Gamepressure oxygen guide](https://www.gamepressure.com/dave-the-diver/how-to-increase-oxygen-supply/z210d58), [ludo.guide diving mechanics](https://www.ludo.guide/guide/dave-the-diver/diving-mechanics-explained), [GameBrief Bancho Grill](https://www.gamebrief.net/blog/dave-the-diver-bancho-grill-recipes-jungle-2026), [games.gg Bancho Grill guide](https://games.gg/dave-the-diver/guides/bancho-grill-guide-unlock-build-and-run-your-jungle-restaurant/), [Dot Esports Auto Supply](https://dotesports.com/dave-the-diver/news/what-is-auto-supply-in-dave-the-diver-answered), [Prima night diving](https://primagames.com/?p=321108), [ProGameGuides locations](https://progameguides.com/dave-the-diver/dave-the-diver-map-all-underwater-locations)
- Not reachable: the Dave the Diver Fandom wiki (HTTP 402) and the PC Gamer review (body not served).
