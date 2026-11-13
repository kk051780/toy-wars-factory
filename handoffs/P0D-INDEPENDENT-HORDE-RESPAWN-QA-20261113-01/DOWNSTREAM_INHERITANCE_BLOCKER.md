# P0D #288 → earned-power H1: stale boss telegraph regression blocker
2026-11-13 JST · SOURCE-only independent QA; no #288 or earned-power writer code changed

## Verified cross-branch provenance
| Slice | Immutable commit | MusouHorde blob | Status |
| --- | --- | --- | --- |
| #288 v2 ORIGINAL | `55ad13b45907a5a3e9deae7196a7c202a0672c0c` | `c1ef565f4e8b11a6e8ff7eac5ed55c8f268a4553` | Fails stale elite tell/target lifecycle |
| #288 v3 CORRECTED | `1117513a27f66f44e0a2dbaa0e387812d2bc0c73` | `57c70e364b721d24e9e36eaeaf8be6dfd9fca592` | Source lifecycle fixed; native 32/32 and Rojo full38 pass reported in [#288](https://github.com/kk051780/toy-wars-factory/issues/288#issuecomment-6845763711) |
| Earned-power H1 39-Luau | `cb2540dc4a3e5b819c0e3598d4af5e2b6dca76d3` | **`c1ef565f4e8b11a6e8ff7eac5ed55c8f268a4553`** | **Re-inherits the old source bug** |

### Root cause of cross-chat leakage
Earned-power assembly `handoffs/P0D-MUSOU-EARNED-POWER-H1-20261113-01/tools/assemble.py` exact Git blob `04f89fa61f773ecd3342c969a9e354ed6703170e`:
- `"parent_game_sha":"55ad13b45907a5a3e9deae7196a7c202a0672c0c"` is fixed to old #288 v2.
- Asserts Game blob `f8c45bcf109dc3229c0459e4fb9fa224ab6c38a4` from old v2.
- Copies all original 38 modules `shutil.copytree(OLD,DIST)`, then overrides **only** Game.server, HUD.client, and adds PowerFantasyRules. No replacement of `MusouHorde.luau`. Thus its frozen assembled game still contains exactly old V2 Horde blob. This is verified by fetching that original source path **at power commit**.
- Its own native power tests and 39/39 compile + Rojo CI can all succeed without catching the Horde lifecycle bug. CI success is legitimate but not proof of all inherited gameplay invariants.

### Explicit status separation
- **#288 v3 bug fixed in isolated source** (new death + respawn `m.tellUntil=0,m.target=nil`, respawn `m.attackAt=now+1.5`; 32/32 native Horde logic tests logged by original author).
- **39-Luau earned-power H1 remains stale** until its own owner rebases BOTH compiled Game/HUD power changes AND original H1 Horde to #288 v3 (or later stable author-approved SHA).
- No actual Roblox Studio 2client, Android, human FUN, retention/revenue or true DataStore reconnect PASS from either branch. Official #220 last75/100 and FUN_GATE NO_GO.

## Recommended safe owner action
1. Earned-power owner pin latest #288 immutable H1 source and reconcile Game/HUD changes at **function/hunk level**, preserving one Game/one existing Remote and exact XP/score/owned/update persistence authority; no blind whole-Game substitution.
2. Ensure the new built `src/server/MusouHorde.luau` GitBlob equals a #288 *fixed* source blob and contains both death+respawn cleanup. Require original #288 v3+ new *real Horde-state native test*, not only pure power policy tests.
3. Update old builder `parent_game_sha` and Game blob guard to the audited fixed base, and re-pin all 39 module checksums. Do not merely update metadata; test output still must carry fixed source.
4. Re-run original bind20/combat26/Horde32, all earned power native32, XP/save/scout/mode full native QA, Rojo exact byte/roles, anti-double hit, and explicit `death-during-1.5sec-elite-tell -> 8sec respawn -> NO immediate attack`. Verify wall/floor, raid pickup/deposit, PvP cap1.4, no mob kill XP and multi-client FPS.
5. #250 product owner chooses one S1_FUN experiment; only #220 sole RC author may integrate hunk-level source after independent QA and OWNER private Studio2client + Android human play. Existing power H1 source stays **SOURCE_CI_PASS_BUT_PRODUCT_QA_BLOCKED** until rebase.

## Reproducible independent static QA (Git checkout with all SHAs)
Use `git show <immutable SHA>:<path>` to materialize the three Horde source versions and power assembly into separate **temporary local** paths, then run:
```sh
node handoffs/P0D-INDEPENDENT-HORDE-RESPAWN-QA-20261113-01/tests/test_downstream_inheritance.mjs /tmp/horde_v2.luau /tmp/horde_v3.luau /tmp/horde_power.luau /tmp/power_assemble.py
```
18 checks are authored, repository Node invocation is not a claimed run until CI/log evidence exists. Independently in this Chat, six V8 cross-branch facts were executed against **actual fetched GitHub source** and all passed. Static proof is not actual Luau/Roblox engine behavior.

This update is the same independent QA feature slice, **not a new Game/RC owner**. No main, original #288 or power branches, #220 RC, merge, Roblox publish, payments, PC/Codex, P0-A/B/C, CAS or 5 automations changed.
