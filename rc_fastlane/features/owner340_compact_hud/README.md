# P0D #340 Compact HUD PREP — source-only private Studio preview

- Official parent RC65: `96b11c900b4dc689ca41fb0710f5ef650e3f455c`
- Feature: `OWNER340_COMPACT_HUD_V1` (not a portfolio-catalog RC admission)
- Pinned new Luau gitblob: `fcc678d5f0cbfdd1df1cd2f6fc948e1e9431b118`
- New source: `rc_fastlane/features/owner340_compact_hud/CompactHUD.client.luau`
- Integration adapter: `rc_fastlane/apply_owner340_compact_hud.py`
- Pure offline regression: `rc_fastlane/test_owner340_compact_hud.py`
- Rollback: OMIT the optional CompactHUD LocalScript (or invoke adapter OFF) and rebuild the exact previous 65-source official candidate.
- **PREP DRAFT only**. Does not edit the official RC branch, main, published game, automations or any original existing Game/Remote/Store/HUD code.

## Scope

This small LocalScript only runs in Roblox Studio; it locates the existing `TrapRaidersS1HUD` ScreenGui with exactly named `Score`, `Status`, `Instructions` and `Attack`. If schema differs, fail closed without touching other UI.

On active matches, large persistent instructions disappear; top score/status lines become compact, single-line and truncated. Narrow camera viewports use smaller top bars and leave native jump/thumbstick/attack placement as-is. Lobby retains a single status hint; **solo lobby starting is NOT solved** by this patch and is tracked separately in #341.

No new RemoteEvent, no FireServer, no Game/score/XP/Store authority; no background/AI cost. Optional runtime script adds one LocalScript: private 65→66 if the scratch adapter is called with ON; previous exact 65 restored by OFF. This is intentionally **not enabled by the main canonical workflow yet**.

## Acceptance still needed

1. On a clean scratch distribution containing exactly original 65 scripts, validate source-lock and feature-lock. Run `python3 -m unittest discover -s rc_fastlane -p test_owner340_compact_hud.py -v`. This is mock/structural QA, NOT native Luau.
2. Call the adapter on the **scratch** 65-script dist, build a new 66-source Rojo Place with exact-source + native Luau compilation, check only one new LocalScript and one original Game/Remote.
3. OWNER Studio screenshot and mobile 375×812 + landscape tests: ensure HUD schema actually matches, top bars don't overlap other overlays, move/jump/attack work, saved data unchanged.
4. After independent P0/P1 review and proper source lock, A can convert into `P0D_PREP_READY_V1` for B #220 sole authenticated CAS adoption. No auto-merge.
5. #341 solo practice is a separate P0 feature; no fake match win or modified official `MinPlayers=2` in this patch.

Official HEAD, official Place/ZIP capacity, and official RC adoption % are unaffected by creation of this isolated branch.
