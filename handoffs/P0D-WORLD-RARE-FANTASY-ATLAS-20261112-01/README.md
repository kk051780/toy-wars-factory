# P0-D WORLD-FIELD-ENGINE — Rare Fantasy Fields V2

Public, keyless, original design-only spec for 4 rare worlds: SPACE, CELESTIAL, EMBER, ECLIPSE. Adds 12 new mechanic cards WF-13..WF-24 and 8 proposed neutral NPC concepts. Parent cards WF-01..WF-12 are unchanged in [Issue #222](https://github.com/kk051780/toy-wars-factory/issues/222).

**DO NOT mark game/Studio implementation complete.** This packet is pure UTF-8 JSON + local Python built-in unittest. No Luau / Roblox assets / Place / secrets, no main or official release RC edits. All new 3D/physics is S2+ design candidate unless sole #220 integrator selects a specific feature.

## Design contracts
- Every mechanic records one easy action, child-readable three-second cue, role/item tactic, opposite-team counter, H0/H1, rollback and 7s/15s promotional scripts.
- Four worlds are available via free, fair map rotation or explore portals; numeric rarity odds are **NOT_SET**, not fabricated.
- Eight original neutral NPC *ideas* have no D18 canonical identifiers, no live spawn rates, no buffs, and no current implementation.
- Localized low-g cannot be done by toggling Workspace.Gravity for one zone; global gravity remains unchanged. A separate server-authoritative VectorForce + enter/exit + fall recovery prototype requires real Studio QA. Never trust client location or client damage.
- No pay-to-win, paid loot, secret advantage, published Roblox feature, or claims of actual player outcomes.

## Verify
```bash
python3 -m unittest discover -s handoffs/P0D-WORLD-RARE-FANTASY-ATLAS-20261112-01 -p 'test_rare_world_fields.py' -v
```
This checks editorial data contracts only, **not real map physics**.

## Trace
Issue #222 original 12 cards and full V2 comment: https://github.com/kk051780/toy-wars-factory/issues/222#issuecomment-6808319162
S1 release score authority: #220. Current reading 70% at #220#6808174562, NOT changed by this design packet.
