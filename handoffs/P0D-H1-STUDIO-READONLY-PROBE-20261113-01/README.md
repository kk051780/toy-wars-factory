# P0D H1 – 実ゲーム28本＋既存Studio受動観測器2本：QA専用Place

**NO PUBLISH / PRIVATE OWNER STUDIO TEST ONLY.**

This deliverable is NOT a new game authority, not a new gameplay feature, and NOT an owner play-test pass. It makes the **real #255 4-way H1 game** more observable during the existing owner-driven two-client Studio check. Main, official S1 RC, all original game sources, #257/#258 QA, and live Roblox are untouched.

## Exact components

- 28 genuine authored H1 game Luau source scripts from issue #255 immutable commit `1498c2d344ede2d9da6c2bfdd025ebc1a15ec48b`: egg heist, original original server combat, GUARDIAN trap, RAIDER wind, repaired sky/sea routes, original moving whale/pegasus, D18 lava dragon client-only first-minute guidance, HUD.
- **Exactly two byte-exact source-vetted existing passive Studio-only observer scripts**, authored by the independent prior #245 / source `e2662b540f2312c95af67a1761ea05842482919d`, blobreferenced below:
  - Client: `StudioPassiveClientProbe.client.luau` Git blob `c0fb0a8ff39ba02277bd4484604b80f3207d7756` — logs authentic client snapshot phase, egg carry, score, win/replay, HUD/Coach visibility and viewport, does NOT command the game.
  - Server: `StudioPassiveServerProbe.server.luau` Git blob `6272cbd587c714046685aba82be775c6dad21057` — logs authoritative existing actual map+egg/score prompt, players/teams and real humanoid damage events, read-only.
- The full Rojo QA-only Place contains **30 Luau**: server Script3, LocalScript5, ModuleScript22. Built from `tools/build_qa_only.py`, which rebuilds #255 author original source, preserves all 28 exact source bytes, strictly source-pins two original observers, rejects seven deliberately malicious/invalid observer mutations, maps one client and one server observer in a separate copy.

The automated CI validates source count, original game and observer identities, actual original 30/30 embedded Rojo XML equality and native compile. **An actual engine run on 2 clients, a physical phone, frame rate, egg transport and child delight remain untested until OWNER actually plays.**

## Owner private Roblox Studio procedure

1. Open the genuine completed run artifact from [this dedicated workflow](https://github.com/kk051780/toy-wars-factory/actions/workflows/p0d-h1-fourway-studio-probe-20261113.yml) and download `P0D-H1-QA-ONLY-30-LUAU-READONLY-STUDIO-OBSERVERS.zip`. It contains `TRAP_RAIDERS_H1_QA_ONLY_DO_NOT_PUBLISH.rbxlx` and receipt JSON. Open as **NEW UNSAVED LOCAL PLACE**. Never overwrite the pre-existing PC current Studio game, never publish this QA_ONLY Place.
2. Studio **Test → Start Server + 2 Players**. Confirm exactly SERVER, RED client, BLUE client; collect Output in **three separate UTF-8 files**. Preserve original logs only on OWNER PC, avoid attaching personal data. Logging is observational, not automated test approval.
3. Check both teams for **LOBBY → COUNTDOWN → ACTIVE → egg stolen → safe carrying on repaired SKY and SEA paths → own SCORE_PAD → RESULTS → REMATCH**. Observe original HP, GUARDIAN trap slowdown, RAIDER Wind 18-second cooldown and 2.5-second effect with carrying prohibited.
4. Confirm in-world animated STAR_WHALE + PEGASUS, client-only D18 original lava dragon by each team spawn. Tap/E on the dragon should show directions to the *enemy* egg when empty and *own* scoring pad when carrying; the hint is read-only and no remote/Robux/reward allowed.
5. Perform phone horizontal landscape / Device Emulator then **real phone**, check HUD button touch collisions (Wind vs Trap), first 15s WOW, player understands theft by 30s, first meaningful action by 90s, visible routes, collision/fall recoveries, FPS and readable characters. Record human preference H0(original 8safe) vs H1, repeat-play desire. No fake retention, no fake revenue.
6. Press **Stop**, close Studio normally. Only #220 sole official integrator reviews source and real QA evidence before any official RC adoption; OWNER's separate public release approval is required.

## Strict optional three-log observation parser

The original #245 observation-only log parser is reused byte-for-byte in `tools/review_studio_probe_logs.py`. From repository root, after capturing real OWNER Studio server/red/blue Output:

```sh
python3 handoffs/P0D-H1-STUDIO-READONLY-PROBE-20261113-01/tools/review_studio_probe_logs.py \
  --server-log server.txt --red-client-log red.txt --blue-client-log blue.txt \
  --output h1_readonly_observations.json
```

The parser explicitly preserves all 34 inherited manual QA cases as `NOT_TESTED` and does NOT auto-certify real 2 clients, mobile, owner fun or publishing. Additional H1 gameplay features (wind, rare creature visual, D18 guide) require separate human screenshot/Output/manual acceptance; original read-only probes are generic S1 observers, not fabricated specialized H1 engine proof.

## Source/rebuild

Run from repo root:

```sh
python3 handoffs/P0D-H1-STUDIO-READONLY-PROBE-20261113-01/tools/build_qa_only.py --assemble
```

The output isolated Rojo project is `handoffs/P0D-H1-STUDIO-READONLY-PROBE-20261113-01/dist/H1_QA_ONLY_UNPUBLISHED/default.project.json`. GitHub CI downloads pinned Rojo 7.7.1 and pinned Luau, produces .rbxlx and verifies 30/30 Lua bytes. All output and generated files are ignored/unpublished until OWNER chooses to download.

## Release policy

Initial P0D official S1 whole-game last explicit #220 auditor score = **75/100, no change**. Product enjoyment remains **NO_GO** until human H0/H1 trial. Original #255 source QA passed, but it does not certify true Studio 2 clients or mobile. No public publish, payment, spending, GitHub main, protected RC, P0-A/B/C CAS, 5 automations, or Windows Codex execution initiated by this task.
