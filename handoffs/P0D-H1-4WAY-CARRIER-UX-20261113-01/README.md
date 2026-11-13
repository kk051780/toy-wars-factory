# TRAP RAIDERS H1 — 卵運搬中HUDの実ゲーム28本統合

Stage: PRELAUNCH / PRIVATE STUDIO ONLY. Existing adoption P0D-FUN-H1-001 (#250); source claim #261. No official RC adoption.

## One-source-only change

- Pinned immutable #255 four-way complete real game SHA1498c2d344ede2d9da6c2bfdd025ebc1a15ec48b with 28 original Luau source modules.
- Exactly 1 replacement client/HUD.client.luau from previously authored #251 frozen SHA4606a74dcebdf4d8a51de4e69b930a15ac788180, exact Git blob313484a69eb10ce01bbdb4872afee215133b01d4, old blob6d273404800e1d25fb1405bc52249b3ab47c1b41.
- Exactly 27 other originals unchanged byte-for-byte, including original one Game server/Remote, RAIDER WindRules, GUARDIAN traps, SKY/SEA six repaired routes, moving two fantasy creatures, D18 lava dragon/guide client-only original sources.
- User-facing change: while carrying egg, disabled trap/wind mobile buttons explicitly say 卵運搬中/風走り不可 or 罠は使えない. On cooldown buttons disabled, cooldown appears. Server still rejects illegitimate action even if client sends R/T key.
- No new remote, game authority, damage, HP, reward, economy, loot, persistent ownership, paid access or release flags.

## Build

From repository root: python3 handoffs/P0D-H1-4WAY-CARRIER-UX-20261113-01/tools/assemble_ux.py --assemble
Recreates own private dist/ complete 28-script game, matching 27 original source bytes; own .github/workflows/p0d-h1-4way-carrier-ux-20261113.yml pins Rojo7.7.1 SHA and actual native Luau compile+Rojo XML28/28, uploading unpublished private .rbxlx after successful CI only.

## Evidence and limits

- Local user-session original .rbxlx patched without modifying other 27 source strings; 217192 bytes SHA256 1d2e95a1dc766b83035dcb59cfe0bd617ef077cf308f607a5736fd151a9b6e4d.
- Existing independent original binary/source QA locally passed 8/8 pinned Git blobs, six joined routes and 16/16 deliberately unsafe mutants rejected on updated binary, after binding HUD SHA to new canonical Git blob.
- New GitHub Actions execution result for this *new HUD* must be independently checked before saying Rojo/native PASS. Earlier #255 28/28 native success only applied to old HUD.
- Real Roblox Studio physical 2client/Android/OWNER H0-H1 first90s human FUN NOT_TESTED. Official RC only sole writer #220; official last whole S1 release score75/100 delta0; FUN_GATE=NO_GO.

Restrictions: no write to main/protected RC/source-owner branches, no merge/Roblox publish/paid/spending/Windows PC Codex/P0A/B/C CAS/five automations.
