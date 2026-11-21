---
name: mekong-dive-ui
description: >
  Implement and polish Dave-the-Diver-inspired (not copied) Mekong river
  gathering/fishing gameplay HUD and visual feedback in an existing
  Three.js/WebGL frontend while strictly preserving the Quán Ăn Chợ Nổi
  Python headless simulation and its DEV 2 gathering/catching test contract.
---

# Mekong Dive UI & Graphics — Quán Ăn Chợ Nổi

## When to invoke

When editing the UI/UX, rendering, water visuals, underwater environment, flower harvesting, fish-catching visual feedback, inventory HUD or read-only event integration for **Quán Ăn Chợ Nổi**.

## Required reading

1. Read the project's DEV 2 specification (user-provided `Pasted markdown.md`) and `Quan_An_Cho_Noi_Dave_Diver_UIUX_Research.md` (copy this research file into the repo).
2. Inspect current frontend, core snapshot API, `chonoi/sim/gather.py`, `game.contract.json` and headless tests. Never assume the file layout.
3. Consult `threejs-game-ui-designer` in https://github.com/majidmanzarpour/threejs-game-skills/blob/main/skills/threejs-game-ui-designer/SKILL.md and UI reference. Use optional graphics skill only for scene polish.

## Non-negotiable guardrails

- **Do not edit** `chonoi/sim/gather.py`, `game.contract.json`, fixed-tick core simulation, or test assertions to make visuals pass.
- Do not import DOM/Three.js/WebGL into the Python core. Preserve CLI/headless test contract.
- Treat core snapshots/events as authoritative. Frontend can animate and interpolate but never award items, choose a different target or change cooldown.
- `pos = [x,d]`, where `d` is positive downward. A 2.5D side view is the preferred visual interpretation: `(x, waterY-d, visualZ)`.
- Do not invent O2/health/weights/weapon stats merely because Dave the Diver has them.
- Dave the Diver is a UX/art **reference**; do not copy copyrighted sprites, logos, screenshots or audio into the game.

## Exact DEV 2 contract

| Setting | Value |
|---|---|
| `surface_depth` | `0.5` |
| `interact_radius` | `2.0` |
| `catch_radius` | `2.0` |
| `node_yield` | `1` |
| `regrow_s` | `20.0` = `1200` ticks at 60 Hz |
| `catch_cooldown_s` | `0.5` = `30` ticks at 60 Hz |
| `fish_yield.ca_linh` | `3` (capacity capped) |
| `fish_yield.ca_loc` | `1` |
| `hold_capacity` | `12` items, LIFO |

Edge states: d=0.5 is surface; d=0.5001 underwater. Dock forbids harvest. Full bag does not consume flower or fish. At 11/12, a successful ca_linh catch adds only one item but removes the caught fish entity. Regrow exactly at tick +1200. Tie-break by core's ID rule.

## Visual deliverables

1. **HUD:** a compact depth indicator, 12-slot basket/hold, catching cooldown, contextual E-harvest/Space-catch, pause help if available. Clear responsive typographic scale.
2. **Scene:** Mekong river waterline and bank, floating flowers, reeds and submerged vegetation, schools of cá linh, solitary cá lóc, caustic ripples, sun shafts and sediment particles; render at low/medium/high tiers.
3. **Feedback:** `gather` (+1), `node_regrown` (flower blossom), `fish_caught` (bubble + actual hold delta), `hold_full` (basket warning), miss (no false reward), fish despawn only when it disappears from authoritative state.
4. **Architectural boundary:** existing Python→frontend adapter / transport drives TS presentation state; use Three.js + CSS HUD read-only. No shadow game rules in JS.
5. **QA:** screenshots 1920x1080 and 1366x768, core headless CLI tests, all 10 DEV 2 edge cases, browser smoke tests and FPS/draw call measurements.

## Recommended implementation

- Main UI skill: `threejs-game-ui-designer`.
- HUD: https://github.com/threejsassets/game-hud (`npm install game-hud`, custom Mekong styling; remove unused health/mana widgets).
- Three.js built-ins: `Water`, `FogExp2`, `InstancedMesh`, `CSS2DRenderer`.
- Optional underwater rendering examples: https://github.com/wayneyip/fishtank and https://github.com/jamisonhill/aquarium (visual techniques only).
- Optional bloom: https://github.com/pmndrs/postprocessing (after profiling).

## Workflow

1. Audit and record which files/APIs already exist, show before screenshot.
2. Implement HUD first with snapshot data; prove the exact `0.5/0.5001` boundaries and 11/12 basket delta.
3. Add only the existing gameplay scene meshes; preserve simulation-to-visual mapping by ID.
4. Map core event names to animations and toasts without mutating core or inventing results.
5. Add scene atmosphere and quality tiers, benchmark and inspect at gameplay viewport sizes.
6. Run and report actual headless/browser tests; list every changed file and any known blocker.

**Never deliver just a static screenshot or generic dashboard. The goal is a playable, live gameplay UI integrated with the existing source of truth.**
