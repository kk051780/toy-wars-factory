# GQ583 original-author 16-player roster cap — canonical 31-source intake

- Parent official baseline: `62ee101ded97f8b2f9e983d846053a782e00df9e`, superseded if official moves. Do not CAS a stale HEAD.
- Uses existing original [GQ583 #583](https://github.com/kk051780/toy-wars-factory/pull/583) source HEAD `60b67c8dade80ff7ccd1d97e03480ba333977084`. Not a second implementation of the rule.
- Original source from #482: `EGGRUMBLE_CastleMatchRules.luau`, Git blob `27da5ca1e9e6d9a7afe0674030e387f094ee7492`. Existing `M.MAX_HERO_SLOTS=16` is the single source of truth.
- Two original guard occurrences `<=32` become `<=M.MAX_HERO_SLOTS`; no other gameplay source changes. The final selected 31 Project reuses all original #541/#537/#540/#539/#555/#536/#547/#551/#538/#523/#517/#508 updates.
- New adapter `rc_fastlane/quality_roster583_rc31/select_original_roster583.py` maps all 31 source files using the existing #508 single-Host/single-Swarm project mapper, checks exact original author blob and 30/31 source preservation, creates one CastleRules overlay and generates exact original/fixed 16-vs-17/32 Lua differential harness from frozen author logic. No new Game/Remote/Store/Combat/AI/Item source authority.
- Dedicated Python tests and existing author tests, native Luau compile all31, old/new executable differential, pinned Rojo7.7.1 actual 31 Script Name/Class/Source readback, source-hash proof and rollback exactness are required before a PREP_READY claim.
- Canonical V3 workflow temporarily switches resulting unpublished .rbxlx source to that selected profile; `rich51` stays primary; the manifest documents feature flag and 40-digit original PR SHA. This is not a merge, public release, Studio/Android acceptance, or user approval.
- Source OFF: select immediately prior `GQ523_HEAL517_KO508_SELECTED31.project.json`, byte exact all 31 originals. Branch-level rollback: revert the isolated adapter, workflow one-step and manifest data.
- Gate sequence: `SOURCE_WIP → PREP_READY (exact PR HEAD Native31+Rojo31) → #220 single authenticated nonforce CAS on *latest* official HEAD → exact new official HEAD dual CI/ZIP/Place → Studio/Android/ART/FUN/OWNER`.
- No individual original-author reply wait. Never use stale PR source as formal RC adoption. Do not edit main, publish Roblox, purchase paid services or operate Windows.
