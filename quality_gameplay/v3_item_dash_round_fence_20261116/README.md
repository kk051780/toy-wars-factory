# GQ V3 / Item DASH old-round expiry fence — isolated candidate

- **OWNER goal**: keep the playable seven-role, terrain, castle, neutral, item, lobby and balance work of original #482 without duplicating any implementation.
- **One unique defect**: original `EGGRUMBLE_FieldItemPickups.luau` item DASH creates a 5s expiry callback that tests only Humanoid's current speed. In a quick match transition, an old DASH expiry can reset a different match's new DASH to its prior WalkSpeed. This is a source-derived possible interleaving, **not** a measured Studio failure.
- **Repair**: inside that original callback, early return unless its **own** `matchActive()` remains true (same session phase ACTIVE and existing world). No new game object, module, remote, storage or reward source. One generated Item source replaces the original in a future **private** 21-source composer; never load both.
- **Source lock**: #482 author commit `fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9`; original Item git blob `24a35a2e6004c635456cc6f2288cf13f8365ba27`. Any drift fails closed, and the original file cannot be overwritten by the patch CLI.
- **Rollback / flag-OFF**: omit this optional overlay; select untouched #482 Item blob. Rollback is a single source-select, not a new runtime toggle.
- **Ownership**: only `quality_gameplay/v3_item_dash_round_fence_20261116/**` and one isolated workflow; #482 original author files unchanged; formal RC #220 only via authenticated non-force CAS. [Claim requested on #218](https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-6914223094). No need for author approval to prepare this isolated candidate; **CLAIM_GRANTED unverified**.

## Eight domains — preserve, don't rewrite

| Domain | Source owner preserved | Gate/impact |
|---|---|---|
| Character (7 roles) | #482 SevenRoleCombat | unchanged role semantics; DASH expiry doesn't overwrite newer character speed |
| Field | #482 FieldItemPickups and Valley map | original item positions and collision are untouched |
| Battle | #482 Combat / #531 AI work | no HP/Remote/damage authority added |
| Castle & eggs | #482 CastleMatchRules | stolen eggs and castle HP unchanged |
| Neutral soldiers/boss | #482 Swarm/StoneGiant; #533 ongoing | no new spawn/KO authority |
| Items | #482 FieldItemPickups | **one DASH expiry hunk repaired** |
| Lobby & replay | #482 RoundReplay | old game callback can't disrupt future match post-lobby |
| Balance | #482 BalanceMetrics; #527 | DASH =27 for 5s in original active match, old expiry suppressed |

## Test / integration

```bash
python3 -m unittest discover -s quality_gameplay/v3_item_dash_round_fence_20261116 -p test_patch_dash.py -v
python3 quality_gameplay/v3_item_dash_round_fence_20261116/patch_dash.py --source /tmp/author/EGGRUMBLE_FieldItemPickups.luau --out /tmp/private/EGGRUMBLE_FieldItemPickups.luau
```

CI checks original immutable blob, one-hunk exact restoration, negative mutants, and Luau syntax of output. Future #220 integration must compose **one** Item into the actual same-head private Rojo Place, run whole-source + CI and record exact official HEAD/artifact bytes; Studio 2-client/Android and OWNER FUN remain separate gates. Do not count this candidate as official RC adoption or S1 completion.
