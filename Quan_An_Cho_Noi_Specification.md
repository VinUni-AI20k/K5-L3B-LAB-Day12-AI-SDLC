# Quán Ăn Chợ Nổi — Game Specification and Team Guidelines

- **Team size:** 5 members
- **Scope:** Phase 1 baseline
- **Reference:** Supplied PRD-0 and Test Contract v1.0
- **Status:** Working specification; open decisions are listed at the end.

Requirements below come from the supplied PRD and Test Contract. Team assignments and workflow are proposed guidelines. If this summary omits an exact protocol detail, the supplied Test Contract is authoritative.

## 1. Game scope

| Area | Required specification |
|---|---|
| Genre | 2D gathering and restaurant management |
| Setting | A floating market in southwestern Vietnam |
| Main character | Út Sen |
| Story | Út Sen gathers ingredients and operates Má Tư’s floating restaurant while Má Tư has back pain. |
| Morning view | Side view of the river, including underwater depth |
| Evening view | Top-down view of the floating restaurant |
| Core loop | Gather ingredients → transfer inventory → cook → serve → earn money and reputation |
| Morning ending | Dock, time expires, or faint |
| Evening ending | Shift timer expires |
| Score | `earned + 100 × floor(reputation)` |
| Five-person requirement | Complete the core and at least one extension across the entire lab |

Phase 1 must include two playable modes and a verified inventory transfer between two separate headless processes. A seamless graphical transition may be added but cannot replace this requirement.

## 2. Required gameplay

Use the supplied preset initially. Change permitted tuning only after the core works, and keep `game.contract.json` synchronized with the running game.

| System | Required behavior and preset |
|---|---|
| Movement | Directional movement; normalize diagonal input; respect world boundaries; speed 4 m/s |
| Morning duration | 180 seconds |
| River | Horizontal position `x: 0–100`; depth `d: 0–30` |
| Starting position and dock | `[2,0]`; dock radius 3 m |
| Surface | `d ≤ 0.5` |
| Oxygen | Maximum 1,800 ticks; underwater subtract 1 tick per step; surface adds 6 ticks per step, capped at maximum |
| Health | 3 HP; only suffocation causes damage |
| Suffocation | Lose 1 HP per 60 consecutive steps ending underwater with zero oxygen, including the step oxygen first reaches zero |
| Basket | Capacity 12; each ingredient occupies one slot |
| Plants | Surface interaction within 2 m; collect 1 item; regrow after 20 seconds |
| Fishing | Six stationary schools; explicit catch action underwater; 2 m radius; 0.5-second cooldown |
| Fish yield | Cá lóc: 1; cá linh: 3 per school |
| Catch capacity | Entire school yield must fit; partial catches are forbidden |
| Docking | Interact within dock radius to finish and transfer the basket |
| Fainting | End morning and transfer an empty inventory |
| Evening duration | 180 seconds |
| Restaurant bounds | `x: 0–16`; `z: 0–10`; starting position `[8,5]` |
| Restaurant equipment | One stove `B1` at `[2,8]`; one table `T1` at `[9,2]`; carry one dish |
| Restaurant interaction | Radius 1.5 m; choose by distance, then stove before table, then ID |
| Customers | First arrival opportunity at tick 120; subsequent opportunities every 15 seconds |
| Ordering | Uniform seeded choice among recipes possible with available stock; reserve ingredients immediately |
| Patience | 60 seconds; decreases while waiting |
| Cooking | Consume reserved ingredients when cooking starts |
| Serving | Carry the correct order to its customer |
| Eating | 10 seconds; payment occurs afterward |
| Burning | Disabled: `burn_s: null` |
| Closing | Eating customers pay immediately; waiting customers leave without a reputation penalty |

The exact tick order and boundary rules in Test Contract §F are mandatory. Serving on the tick patience reaches zero is valid. The selected nearest interaction target does not fall back to another target if it cannot be used.

## 3. Ingredients, recipes, and economy

Keep these ingredient identifiers unchanged:

| Ingredient ID | Name |
|---|---|
| `ca_loc` | Cá lóc |
| `ca_linh` | Cá linh |
| `bong_dien_dien` | Bông điên điển |
| `bong_sung` | Bông súng |

Keep these dish identifiers and recipes unchanged:

| Dish ID | Ingredients | Cook time | Price |
|---|---|---:|---:|
| `ca_loc_nuong_trui` | `ca_loc ×1` | 6 s | 60 |
| `goi_bong_sung` | `bong_sung ×2` | 4 s | 40 |
| `lau_ca_linh_dien_dien` | `ca_linh ×3` + `bong_dien_dien ×1` | 10 s | 120 |

Money uses integer units of **1,000 VND**.

- Initial reputation: **3**, bounded to **0–5**.
- Tip: `floor(price × 0.2)` when remaining patience is at least **50%** at service, after that step’s timer decrement.
- Positive tip: **+0.2 reputation when payment is collected**.
- Departure because patience expires: **−0.5 reputation**.
- Available stock equals physical stock minus reservations.
- Reserved stock cannot be promised to another order.
- Cancelled orders release unused reservations and discard any associated dish; ingredients already consumed by cooking are not refunded.

## 4. Controls and interface

Recommended keyboard mapping:

| Action | Input |
|---|---|
| Swim or walk | WASD / arrow keys |
| Interact, gather, dock, cook, pick up, serve | E |
| Catch fish | Space |

Holding E or Space must not repeat actions automatically: buttons activate on a false-to-true transition.

Required displays:

| Screen | Information |
|---|---|
| Morning | Time remaining, oxygen, HP, basket contents and capacity |
| Evening | Time remaining, available stock, order, patience, stove state, carried dish, money, reputation |

Provide clear visual feedback for successful actions, full baskets, unavailable ingredients, ready dishes, and departing customers. Keep decorative effects separate from simulation logic.

### Visual direction

- Morning: sediment-colored water, nipa palms, stilt houses, and soft sunrise colors.
- Evening: warm string lights and kitchen smoke.
- Út Sen: áo bà ba, khăn rằn, homemade diving goggles, and a mesh basket.
- Simple 2D shapes are acceptable for the initial playable build.
- Respect local culture and record asset sources and licenses in `CREDITS.md`.

## 5. Technical guidelines

1. Share one simulation between graphical and headless modes. Rendering reads state and sends commands; it does not independently calculate gameplay.
2. Run the simulation at a fixed **60 ticks per second**. Rendering speed must not change outcomes.
3. Produce deterministic runs: the same executable, machine, seed, arguments, and inputs must produce byte-identical logs and inventory.
4. Preserve the CLI, fixture validation, snapshot fields, events, sorting, and exit codes from Test Contract §§A–G.
5. Use the exact inventory schema:

   ```json
   {"items":{"bong_sung":2,"ca_loc":1}}
   ```

6. Inventory contains only `items`, with known ingredient IDs and nonnegative integer counts. Omit zero-count entries when writing; missing ingredients count as zero.
7. Write inventory atomically only when morning gameplay ends. Reaching an early headless tick limit must not create or overwrite it.
8. Keep graphical randomness and real-time clocks outside simulation decisions.
9. Keep `build_cmd`, `run_cmd`, and `headless_cmd` accurate in `game.contract.json`.
10. Reject invalid flags or fixtures with exit code **2**, report runtime/output failures with **1**, and return **0** for normal completion or tick limit. Report diagnostics on stderr.

### Required headless interface

```text
<headless_cmd> --mode gather|quan --seed <int>
  [--scenario <file.json>] [--inputs <file.json>]
  [--inventory <file.json>] [--inventory-out <file.json>]
  --ticks <N> --out <file.jsonl> [--snapshot-every <N>]
```

- Required flags: `--mode`, `--seed`, `--ticks`, `--out`.
- `--inventory` applies only to `quan`; `--inventory-out` applies only to `gather`.
- `--ticks 0` initializes a fixture without advancing gameplay.
- Snapshot interval defaults to 10 ticks; emit the initial and final snapshots, with at most one per tick.
- Emit events in processing order before the corresponding snapshot; `end` is the final JSONL record.
- Follow the original contract for the full fixture schema, snapshot schema, event payloads, and exact event boundaries.

## 6. Proposed division for five members

| Member | Main ownership | Required handoff |
|---|---|---|
| 1 — Movement and survival | Swimming, boundaries, oxygen, suffocation, basket capacity | Morning player state and movement behavior |
| 2 — Gathering and inventory | Plants, fish, docking, morning ending, inventory export | Valid inventory file and gathering events |
| 3 — Customers and orders | Arrivals, dish selection, reservations, patience, departures | Order states and available-stock calculation |
| 4 — Kitchen and economy | Cooking, carrying, serving, payment, tips, reputation | Complete restaurant service cycle |
| 5 — UI and integration | HUD, input mapping, shared entry points, smoke verification, release coordination | Playable integrated build and verification evidence |

Everyone tests their own module. Member 5 coordinates verification and integration; each module owner remains responsible for fixing their module. Rebalance assignments according to team skills and blockers.

## 7. Collaboration rules

- Work in **one shared fork** and set `team_size` to **5**.
- Record names, GitHub handles, responsibilities, and communication rules in `TEAM.md`.
- Agree on inventory and simulation/UI interfaces before parallel implementation.
- Recommended workflow: short feature branches and small changes for review. The PRD also permits direct pushes or other effective workflows.
- Assign one owner to each shared file to prevent conflicting edits.
- Report blockers early with a specific failing example; review workload at minute 20.
- Each member needs at least **three meaningful commits across the lab**, attributed to their account. Use `Co-authored-by:` for shared work.
- Record questions, answers, and assumptions in `docs/clarify.md`.
- Integrate continuously instead of waiting until the final minutes.
- Add creative work only after the core works. Disable additions in headless mode or demonstrate that contract outputs remain unchanged.

## 8. Verification and completion checklist

| Verification | Passing condition |
|---|---|
| Movement | Correct speed, diagonal normalization, acceleration limit, and boundary clamping |
| Oxygen | Correct depletion/refill and exact suffocation timing |
| Gathering | Correct distance checks, nearest-target selection, regrowth, and capacity behavior |
| Fishing | Correct school selection, full yield, and cooldown |
| Inventory | Dock/time transfers the remaining basket; faint transfers nothing; early tick limit does not write inventory |
| Reservations | Available stock excludes reserved quantities; cancellation releases only unused ingredients |
| Service | Correct cook → ready → carry → serve → pay sequence |
| Edge cases | Deadline, closing, and simultaneous actions match Test Contract §F |
| Fixtures and errors | Invalid inputs fail with the specified exit code before gameplay output is written |
| Determinism | Repeated identical runs produce identical output bytes |
| Process integration | The supplied two-process smoke test passes |
| Playability | Both modes work with readable HUDs |
| Delivery | Contract, instructions, evidence, and documentation match the tagged commit |

### Mandatory two-process smoke test

Create `dock.json`:

```json
{"gather":{"hold":["ca_loc","bong_sung","bong_sung"]}}
```

Create `dock-inputs.json`:

```json
{"frames":[{"tick":0,"interact":true}]}
```

Run:

```text
<headless_cmd> --mode gather --seed 42 --scenario dock.json --inputs dock-inputs.json --ticks 1 --out gather.jsonl --inventory-out catch.json
<headless_cmd> --mode quan --seed 42 --inventory catch.json --ticks 0 --out quan.jsonl
```

The restaurant snapshot at tick 0 must contain `stock:{"bong_sung":2,"ca_loc":1}`, matching the inventory written by the first process.

## 9. Required delivery files

| File or directory | Required contents |
|---|---|
| `game.contract.json` | Contract version, team, team size, accurate commands, and actual tuning |
| `TEAM.md` | Members, handles, module ownership, roles, and team agreement |
| `README.md` | Clean-clone setup in at most three commands on macOS or Linux, controls, scoring, and one-command team test instructions |
| `README.md` or `docs/contracts/` | Inventory schema, valid example, and agreed module interfaces |
| `docs/verification/phase-1.md` | Acceptance criterion → evidence → pass/fail, with verification instructions |
| `docs/proof/phase-1/` | Actual evidence from the delivered commit |
| `docs/clarify.md` | Questions, answers, decisions, and assumptions |
| `docs/ai-usage-log.md` | AI usage by member and phase; tokens/cost when measured |
| `docs/retro.md` | Team retrospective |
| `docs/members/<handle>.md` | Individual reflection |
| `CREDITS.md` | Asset sources and usage rights |

If creative features are implemented, document them under **“Sáng tạo của nhóm”** in `README.md`, including evidence that the contract core still passes.

The release tag `phase-1` must point to the delivered commit on `main` and be pushed before the lab deadline.

## 10. Suggested Phase 1 schedule

| Time | Milestone |
|---|---|
| 0–15 minutes | Establish shared fork, roles, team agreement, inventory schema, and simulation/UI interfaces; start parallel work |
| Minute 20 | Review blockers and move available help to delayed modules |
| Before minute 25 | Demonstrate a real morning inventory export |
| 15–45 minutes | Implement and continuously integrate the four gameplay slices and UI |
| 45–55 minutes | Run two-process smoke verification, playtest `main`, complete evidence, and prepare the release tag |
| 55–60 minutes | Buffer and push `phase-1` before the deadline |

## 11. Open decisions

- [ ] Confirm whether the delivery covers only Phase 1 or later phases too; obtain any later PRDs.
- [ ] Confirm the engine/language and whether the supplied Python starter will be used.
- [ ] Assign the five named members according to their skills and availability.
- [ ] Confirm the approved extension list; the supplied Markdown requires one extension for five members across the whole lab but does not enumerate options.
- [ ] Confirm whether the 60-minute phase limit applies and record the actual submission deadline.

Until these decisions are settled, use this document as the Phase 1 baseline. Later-phase features and the extension remain pending.
