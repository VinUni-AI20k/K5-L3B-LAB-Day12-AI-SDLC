# Harness Verification — Phase 2

Run: `20261121-153002-657367`

- Contract version: `1.1`
- Launcher: `contract`

## Unit tests

- Status: PASS
- Evidence: `test-output.txt`

## Headless determinism

| Mode | Run 1 exit | Run 2 exit | Determinism and success |
|---|---|---|---|
| gather | 0 | 0 | PASS |
| quan | 0 | 0 | PASS |

### SHA-256

- gather run 1 SHA-256: `94a0c314ae510f0726c416fb1654ec3fb00e18d83e61322b932d4bf42415898d`
- gather run 2 SHA-256: `94a0c314ae510f0726c416fb1654ec3fb00e18d83e61322b932d4bf42415898d`
- quan run 1 SHA-256: `fe9778117a2646d6ed0ac3fcd911b2162d5c472786f923bcb8711e65b67d77eb`
- quan run 2 SHA-256: `fe9778117a2646d6ed0ac3fcd911b2162d5c472786f923bcb8711e65b67d77eb`

## Phase 2 — Full Day

| Run | Duration | Completed | Within 20s | Exit | Result |
|---|---|---|---|---|---|
| 1 | 0.487s | True | True | 0 | PASS |
| 2 | 0.472s | True | True | 0 | PASS |

- Day determinism: PASS
- Day run 1 SHA-256: `8fcabc2f601b00addce5cf21203850e10e9aac8eadeb7e7513b665b9699e870d`
- Day run 2 SHA-256: `8fcabc2f601b00addce5cf21203850e10e9aac8eadeb7e7513b665b9699e870d`

## Overall result

**PASS**

Note: Harness PASS does not prove every Phase 2 AC.
QA must map each AC to appropriate evidence.
