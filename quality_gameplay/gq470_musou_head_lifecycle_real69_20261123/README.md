# #824 / #825 — current69 MUSOU observer Head lifecycle

SOURCE PREP for the existing `GQ8_MUSOU_FEVER_CHAIN_20261119` feature.
This packet changes one selected Controller in the H93 private companion. It is not a formal RC adoption, active-profile unification, Studio result, or gameplay-authority change.

## Problem and behavior

The original Controller renders on character observation and server snapshot changes. The original AuraClient returns without constructing visuals when Head is absent. Later Head arrival has no callback, so a valid MUSOU/RUSH/KAKUHEN snapshot can remain invisible until another attribute changes.

The [Player.CharacterAdded documentation](https://create.roblox.com/docs/reference/engine/classes/Player#CharacterAdded) allows character parts to arrive later on clients. The native cases model this sequence; they do not measure engine replication or rendering.

The replacement Controller:

- Keeps one current character binding for each watched Player, with exactly two character subscriptions.
- Observes direct Head addition/removal before the first render.
- Reconciles the selected Head identity before using the original Aura.stop/update APIs.
- Retains the actual created origin so a detached old Head can be cleaned.
- Refreshes that origin after every Aura.update, including a role change under the same Head.
- Invalidates retired bindings before disconnecting and cleaning. Deferred renders check the watched Player generation, exact binding, Player membership, and exact Character.
- Retains subscriptions while the server snapshot is OFF or Head is temporarily missing.
- Preserves the existing three server attributes, phase/role interpretation, five Player subscriptions, and seven-role visual module.

There is no polling, additional render loop, server attribute writer, Remote, KO/Score/HP/Store authority, or new aura implementation. `EGGRUMBLE_MusouAuraClient.luau` remains byte-exact.

## Exact inputs and change

| Input/output | Bytes | SHA256 |
|---|---:|---|
| Original Controller | 1,881 | `13495f0c816f88a78f62e8c40ec5a79c7140c2057b33037695d6073e527768c9` |
| Candidate Controller | 4,407 | `c4bd990ef8e0f0135d52620e50acfe93620f83acc4097c2b78ef366ab980271e` |
| Unchanged AuraClient | 6,205 | `b2c279371a8fd986b929883290aae58ed9acdafb7cd48f878eae3785e4acccab` |
| Original/rebuilt OFF Place | 828,658 | `9cc9068b85893605c5090964fdc27175d9c48372803d65fe52914591fa7e5899` |
| Local candidate ON Place | 831,184 | `844665d032a34e008a9eb452a4db5959270fd64bef714b1d0ceea82dd64e1c0f` |

Runtime and Place delta: **+2,526 bytes**, exactly one of 69 selected source bodies. Other 68 bodies and all 75 instance paths/classes remain unchanged.

Immutable official input: `93a1147561a531610ac1609ebc68cc0ecf546623`, [push run45106580546](https://github.com/kk051780/toy-wars-factory/actions/runs/45106580546), artifact14787568439 `P0D-EGGRUMBLE-V3-REAL69-CANONICAL-PRIVATE-STUDIO`. ZIP5,840,240B/SHA256 `1187e0f2ff176a286855e911495da84006d5c99841f68891aeca9630915f275d`.

The fixed `source_lock.json` pins the original manifest, project, Place, source endpoints and toolchain. The 119 manifest entries plus the manifest itself are verified. Old receipts are read-only provenance; the candidate output copies only the project and source files before creating new evidence.

## Reproduction and acceptance

The fixture embeds the complete original AuraClient and complete selected Controller exactly once with verified byte ranges. Only Roblox services, Instances, signals and deferred execution are doubled. It does not substitute a model of the Controller's render logic.

| Expectation | Original | Candidate local run |
|---|---|---|
| Head present on initial observation | PASS | PASS |
| Existing Character receives Head with unchanged snapshot | FAIL | PASS |
| CharacterAdded render runs before Head arrives | FAIL | PASS |
| Later valid server snapshot still recovers | PASS | PASS |
| OFF before Head arrival stays OFF | PASS | PASS |
| Old avatar's queued render stays retired | PASS | PASS |
| PlayerRemoving before queued render cannot resurrect | FAIL | PASS |
| CharacterRemoving before queued render cannot resurrect | FAIL | PASS |
| Role refresh, then same-role Head replacement retargets and cleans | FAIL | PASS |
| Foreign child/non-BasePart Head does not activate | PASS | PASS |
| Original phase/role visuals and burst behavior | PASS | PASS |
| Unrelated/duplicate Head events and unchanged-Head snapshots do not reburst | PASS | PASS |
| Twelve avatar lifetimes and final Player removal disconnect listeners | PASS | PASS |

Local reference execution on 2026-11-23: **baseline8 PASS/5 expected FAIL, exit1; candidate13 PASS/0 FAIL, exit0**. Five failed expectations are not five distinct live game bugs. Removal timing and same-Model replacement are modeled boundary sequences.

The packet gate also performs 69 actual ON compilations, two Native starts, two Rojo builds, actual XML Source/Class/Instance comparison, and exact inverse/source/Place recovery. Baseline Native exit1 is explicitly expected and retained; it is never represented as a green original game. Candidate stderr, missing/duplicate assertions, unexpected failures, and input drift fail the gate.

The local reference run reused an existing pinned Native binary and recorded its hash. The dedicated hosted workflow builds Luau from commit `f46d879e28302a430029304f7f6a162aed66f103` / tree `2432c996fc9fa73680b5e2cfe172d36114fe3746`, and uses digest-pinned Rojo7.7.1. It binds the actual source checkout, official input run/artifact, raw commands and resulting artifact. Hosted results must be read back at their actual immutable source head; the local run has `source_head=null`.

## Run locally

Use the exact official extracted artifact and supplied tool executables. Output must be a fresh directory outside the artifact and this packet.

```bash
python3 -B quality_gameplay/gq470_musou_head_lifecycle_real69_20261123/verify_packet.py \
  --base-artifact /absolute/path/to/extracted-official-artifact \
  --archive /absolute/path/to/original-official.zip \
  --output /absolute/path/to/new-output-directory \
  --luau /absolute/path/to/luau \
  --luau-compile /absolute/path/to/luau-compile \
  --rojo /absolute/path/to/rojo
```

Omit `--source-head` for unpublished local changes. The offline gate labels a supplied source head as caller-supplied; only actual GitHub readback and the independent review can establish hosted provenance.

Forward and inverse helpers reject an unexpected current Controller. The inverse reads its original bytes from the immutable baseline. Build the OFF project to recover the exact original Place; do not replace official artifacts or carry a stale original receipt into a modified candidate.

## Scope, lineage and next gate

Actual claim: [#2187091401148](https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-7091401148), `P0D-GQ824-AURA-LIFECYCLE-20261123-BEB3C323`, registered in `ea2e2951cce0da37fc13a0287412b353ed1cde3b`.

This is an add-only eight-file continuation on original PR825. Its 13 historical paths at `b49350c8b8aaba561c9e0839d27fc5fc275c3a32` are frozen with blob identities in the lock. Never whole-merge that historical PR stack into the current RC. Preserve D5F's existing Swarm charge/avatar/round continuation and PR950's AuraClient visual/LOD work.

Author contexts are `CODEX_ROOT_BEB3C323FED2:/root` and `:/root/planning_gaps`. The separately registered source reviewer is `CODEX_ROOT_BEB3C323FED2:/root/rc_rules`; authors cannot self-approve.

Source publication requires the real current source scope, a separate owned source lease, an expected-parent non-force update, actual same-head CI/artifact readback, and registered independent source review. Canonical selection and formal RC integration require a separate bounded writer allocation after the existing Bot → BEAST → Guardian/currentP0 order. This source grant does not authorize shared canonical producer/profile/workflow edits.

Preserved profile labels: `ACTIVE_RUNTIME=rich51`, `PRIVATE_COMPANION=REAL69_UNION22`, `RUNTIME_UNIFIED=NO`. Source counts are inventories, not completion rates.

Studio solo/two-client, Android, ART, FUN and owner acceptance remain **NOT_TESTED** for this repair. Source/Native success cannot establish those results. The authorized single Studio owner must later exercise the actual same-RC Place.

