---
name: ui-contract-sync
description: Synchronize and verify chonoi.live web HUD, input handling, and optional visual/audio assets against the Phase 1 simulation snapshot contract.
---

# Skill: `ui-contract-sync`

Use this skill whenever modifying `chonoi/web/index.html`, `chonoi/live.py`, `chonoi/web/assets/`, or `docs/ui-contract.md`.

## Rules & Checklist

1. **Read-Only Snapshot Principle**:
   - The browser client (`chonoi/web/index.html`) must **only read** state from `GET /state` and send player commands via `POST /input` (`{"move": [dx, dy], "interact": bool, "catch": bool}`) or `POST /restart`.
   - Never mutate simulation state outside `Session.step()` and never introduce wall-clock or UI randomness into `chonoi/sim/`.

2. **Graceful Degradation for Partial Sim & Missing Assets**:
   - If a snapshot field is `undefined` or `null` (while M1–M4 are still implementing features), the HUD must fall back safely using nullish coalescing (`??`) or default values without throwing a JavaScript exception inside `requestAnimationFrame`.
   - External images, spritesheets, and music files placed in `chonoi/web/assets/` must be loaded asynchronously; if an asset file is not yet present (HTTP 404), the canvas renderer must automatically draw procedural 2D shapes.

3. **Coordinate & HUD Contract Alignment**:
   - **`gather` mode**: `[x, d]` where `x` increases East (right) and `d` increases downward (depth). Moving down (`S` / `ArrowDown`) sends `move[1] = +1`.
   - **`quan` mode**: `[x, z]` where `x` increases East (right) and `z` increases North (up). Moving up (`W` / `ArrowUp`) sends `move[1] = +1`.
   - **Available Stock Calculation (`quan`)**:
     $$\text{available}[k] = \max\left(0,\ \text{stock}[k] - \sum_{c \in \text{customers}} (c.\text{reserved}[k] \ ?? \ 0)\right)$$

4. **Verification Command**:
   Always run the live server test suite after editing `chonoi/live.py` or `chonoi/web/index.html`:
   ```bash
   PYTHONPATH=tests:. python3 -m unittest tests.test_live -v
   ```
