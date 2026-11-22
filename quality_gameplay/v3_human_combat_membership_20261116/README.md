# GQ V3 — Human Combat Current-Match Membership (unique repair)

**State:** isolated DRAFT source repair only; #218 SOFT_CLAIM request 6912571265, not granted. **Formal RC 0; Studio/Android/FUN/OWNER 0.** No publish, main, protected RC write, original owner branch mutation, paid features or user PC commands.

## Actual defect and proof

The original #482 `EGGRUMBLE_SevenRoleCombat.luau` author HEAD `fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9`, Git blob `66e666418b7c23d41f87faa5d61eb6e2770a463e`, identifies enemy human / teammate solely from a persisted castle ID and team. A departing human can be taken over as AI or rejoin a different lobby/mode, while the old match still holds the same castle owner ID. Physical access to the old arena then permits unintended damage, status effects, or teammate healing by original human combat scripts. These are source-derived unsafe paths, not an observed Android/Studio exploit.

## Exact source fix

`compose.py` pins original author Git blob and generates **one** reversible diff to the existing 7-role Combat file, adding four fail-closed checks: current caster at `execute`; live opposing human in `hitHumanHeroes`; human opponent in `secondaryEffect`; live human teammate in `healAllies`. The only human-presence truth is `session.isCurrentHuman` supplied by existing #531 Bot-vs-Human fix. No second host callback, damage authority, Game, Remote, Store, Swarm, castle or role. Missing #531 callback fails closed rather than letting unrelated users take damage. The feature is **not** independently deployable without the #531 callback. Existing #529 stealth / #510 healing / #516 DOT / #524 movement sources must be source-selectively combined with this one original Combat authority, not replaced wholesale.

**OFF/rollback:** omit this Combat overlay; the original #482 byte content is recovered by `undo()`. Revert this change without disabling or duplicating #531's separate BotActors membership fix. Original source is never altered on the author branch.

## Build evidence

The read-only workflow fetches a pinned #482 author and #531 branch. It reuses #531's exact Host and BotActors overlay, adds only this human Combat overlay, compiles **one actual 21-script private Place** (18 untouched author scripts + 3 modified, single Host), executes source-derived native Luau human hit/status/heal negative tests and checks every Rojo embedded Script source/class exactly. The CI is source/private build proof only: no Roblox engine, live 2client, actual mobile or human FUN result. On a failing source lock, native test or Place comparison, admission is RED and rollback is required.

## Eight-domain collision ledger

| Domain | Existing authority | This candidate delta |
|---|---|---|
| 7 roles | #482 / #529 | existing Combat only, no extra class |
| Field | #482 / #520 / #523 | unchanged |
| Battle | #482 / #529 / #530 | block stale human targets and casters |
| Castle / eggs | #482 / #500 / #527 | existing castle team/HP unchanged |
| Neutral / boss | #494 / #501 / #533 | unchanged |
| Items | #489 / #517 / #525 | unchanged |
| Lobby / membership | #482 / #531 | reuse #531 single host callback |
| Balance / score | #487 / #527 | unchanged actual damage, rate, cost, KO |

## RC gate to completion

1. Original #482/#529/#531 owners acknowledge one composed Host/Combat source and #218 exclusivity decision; do not treat this request as granted.
2. Pin exact Git author HEADs, re-run Native Luau, source lock, 21-source private Rojo and rollback after the final four-/five-author composition. Any preserved #484 real AI duel must be retained.
3. #220 **sole authenticated CAS writer** integrates source-selective changes into latest official `rc/p0d-s1-kids-rc01` only; official same-HEAD CI and UNIQUE canonical ZIP/Place byte attestation and ACK required. No PR merge into main.
4. Studio TEAM/BR two real clients, 1-player bot session, disconnected/rejoin stale castle, 15 min, low-end Android and #420/#470 art+FUN OWNER verification required. The 67-item feature registry and S1 completion may only increase with official, demonstrable evidence.
