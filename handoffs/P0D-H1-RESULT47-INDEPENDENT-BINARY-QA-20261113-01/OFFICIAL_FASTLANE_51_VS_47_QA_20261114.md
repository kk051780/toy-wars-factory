# P0D canonical RC FASTLANE: independent actual 47→51 binary comparison

**2026-11-14 JST. This report is SOURCE / BINARY QA ONLY. NO official RC source change.**

## Authoritative OWNER decision

Owner explicitly changed P0D to a FAST RC model in #220: same canonical branch `rc/p0d-s1-kids-rc01`, SOURCE_PIN and one original Game/Remote/Store, one RC CI build; human Studio and FUN deferred to batch review before public launch; release/publish/paid/main writes still require separate approval. Do not apply superseded B42-only private-trial restrictions to RC integration. Canonical ACTIVE.json and FEATURE_REGISTRY from RC SHA `50bf5b4851fc0eb7c16052f578d6360ec54cd63a` verified via GitHub fetch.

## Actually downloaded authentic SOURCE-backed Place artifacts

| | Original rich47 rollback reference | CURRENT OFFICIAL RC rich51 |
|---|---|---|
| Source | #220 sole integrator `f74686cbfc601436962df8aeb8da7a1b3ff92152` | pinned `79123d35cd7afdd5f4f9941675bc2d2cf382ac4e` |
| GitHub Actions | https://github.com/kk051780/toy-wars-factory/actions/runs/43430925222 | https://github.com/kk051780/toy-wars-factory/actions/runs/43483997763 |
| Artifact ID | 14039442605 | 14066132178 |
| Real ZIP SHA256 | `a56742f9f130588603b9608763b61c1a401742947a5ceeecfa55022bae653bcd` | `1b20eda5fb17c3e58d015036c03bbd790ef908d985a29792880fa9c03b614ffb` |
| Real .rbxlx SHA256 | `321636a34ed217d0d5191ab25d6db1895d6fda8da11bb7a34ab6014b3d3455d9` | `6c9d36d6944301c4fb7317e087f877f5cdeb513b38213608976da4cce1c6bb65` |
| Real Luau source counts | 2 Script / 7 LocalScript / 38 ModuleScript =47 | 3 Script / 8 LocalScript / 40 ModuleScript =51 |

Both ZIP archives **actually downloaded** via connected GitHub, archive contents extracted and XML inspected. Real RC51 source digest exactly equals GitHub Actions author's receipt (same 469021-byte .rbxlx). 51 current RC job conclusion COMPLETED SUCCESS, all steps SUCCESS. Source fingerprint is pinned to the cited RC SHA, not future mutable HEAD.

## Executed REAL artifact-byte audit

- Source comparison keyed by actual Roblox XML Class+Name: **all 47/47 existing Luau Source bytes are exactly equal**; 0 removed or modified.
- Exactly four new V4 components, no additional change:
  1. ModuleScript `FocusTrainingScheduler`
  2. ModuleScript `SessionSixSkillXPPreview`
  3. Script `V4TrainingBridge`
  4. LocalScript `V4TrialOverlay`
- One original `Game` Script, existing original authoritative Remote event handler, single shared Store module unchanged.
- New four V4 scripts contain no DataStore update, FireServer, extra OnServerEvent handler, Marketplace or purchase API. Server bridge and client HUD both enforce Studio-only.
- Independent local Python auditor checks exact SHA256 for **both** real ZIP files and actual `.rbxlx`, source/class counts, 47 original untouched, exact four additions and Studio-only/authority guards. Positive real pass + two negative tamper trials both **PASS** (tampered previous47/official51 ZIP rejected).
- Local reusable independent auditor `P0D_RC_FASTLANE_PROFILE_AUDIT.py` SHA256 `7788f232e116f1f31b6656098db12a7e2d823c59d677781b5d5b5c6b9e00ba76`; actual JSON receipt SHA256 `652273d14b988df25d007795d16a7f2aa88a6810ab59f2f26f2efbae79fed474`. Both delivered to OWNER in this conversation, not committed to or run by official RC. This is **not** a new RC CI or duplicated game builder.

## Fastlane status / next integration

- **ACTIVE** official RC profile is **rich51**, not an isolated prototype. Official CI 43483997763 SOURCE_EXACT 51/51.
- **Rollback source integrity to original author's rich47 is proven 47/47** from authentic original binary; however a separate `workflow_dispatch` run of current RC workflow for `rich47` and `legacy21` has **not** been observed, so do NOT declare those RC fallback builds SUCCESS.
- **Real human Studio 1/2-client, Android and FUN are still NOT_TESTED**, only deferred to release-stage review.
- Six-skill V4 addition is **SESSION XP preview ONLY**, not saved levels, not actual skills/stronger player, not persistent JST 30min free focus. Original Store normalization currently drops unknown V4 fields; protect existing inventory/eggs/dojo and coordinate exact canonical same-key migration before real persisted XP.
- Original last assessed S1 release quality **75/100 FUN_NO_GO**, not auto-increased merely due to new RC source/profile.
- **NEXT_OWNER** is sole #220 RC integrator under updated owner FASTLANE mandate: integrate next actual feature only after pinned SHA + one Game/Remote/Store + source-exact RC build; prioritize schema-reviewed durable V4 leveling / daily quota or child-relevant combat feature, with feature rollback. No need for per-feature human Studio gate before RC; require it before publish. No other agent or branch writes official RC/main or issues paid/publish actions.

This QA branch/report does not update ACTIVE.json, official rc/p0d-s1-kids-rc01, P0-A/B/C, CAS, automations, costs or live game.
