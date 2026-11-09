# P0-D D18 Collection Atlas — First Six Editorial Pass v2
As of 2026-11-10 JST | `TRAP_RAIDERS` | `work_id=p0d-siege-v19`

## Status, scope, rights
**DESIGN_ONLY, NOT a 3D/model/gameplay delivery.** This is an additive editorial quality refinement of six **COMMON** items from an existing 648-row conceptual atlas. The full commercial creative descriptions, workbook, and ZIP remain in OWNER's private ChatGPT Library and are NOT included in this PUBLIC GitHub branch. These references do NOT auto-start Windows Codex.

- Parent: #218 (D18 claim and coordination), #219 (market/creative research), #213 (actual PC/Studio truth), #217 (cross-P0 safety), original catalogue pinned commit `275695238e1278e8fb9e60e82af4b574f2f2dcb6`.
- Packet: `P0D-D18-COLLECTION-ATLAS-20261110-01` / revision `D18-EDITORIAL-R01-CH01-V2-20261110`.
- **6 changed records:** `TRCA-BE-001` (P10 legacy), `TRCA-SP-001` (M06 legacy), `TRCA-VE-001`, `TRCA-WE-001`, `TRCA-ZO-001`, `TRCA-TR-001`.
- Region: R01 星屑の廃都 / Chapter 1 「最初の一灯」. All six are COMMON, and their existing IDs, names, category, legacy mappings, and rarity remain unchanged.
- 642 other records: **UNEDITED**. Original 648-row JSON/ZIP untouched.

## Why an editorial pass was necessary
An actual audit of the previous private 648-row JSON found:
- 648/648 were `manual_design_check=NOT_REVIEWED`;
- 72/72 flagship story blurbs shared the identical ending 「持ち主が負けた日も同じ表情で迎える。」;
- 108/108 beasts shared the generic silhouette intro 「低ポリ生物・顔に大きな目」.
These exact repeated fragments mean that a unique name/ID is not equivalent to a lovingly crafted distinct character. The new six editorial cards each add unique silhouette, emotion, flaw, three-scene story, idle/tap/victory/defeat gestures, original audio prompt, free permanent unlock proposal, existing role/interface boundaries and first 3D/LOD instruction.

**Honest stage:** 24/24 structural design checks PASS locally; NO user-preference/child usability test and NO Studio test. Data tests do not prove art quality. The original 72 flagship cards still need distinct rewriting in a later pass.

## Private deliverables (not present in public GitHub)
`/TRAP_RAIDERS/企画室/TRAP_RAIDERS_COLLECTION_ATLAS_648_v2.xlsx`
- SHA256 `b3b29880c0212b99b2e6d2efb1838f616e6247dd14b9ff08810904a067da5f10`
- 135672 bytes. Preserves original 6 workbook sheets, adds four: 6-item editorial highlights, 126 fine-grained spec rows, audit notes, Codex acceptance gates.

`/TRAP_RAIDERS/企画室/TRAP_RAIDERS_D18_FIRST_SIX_EDITORIAL_V2_PRIVATE.zip`
- SHA256 `a3bb7d80b95405540807334ba692689b3912b9a6d058d029ba5617a48dbcdb16`
- 19843 bytes. Contains six-item overlay JSON, Japanese creative bible, evidence audit/QA, file-SHA manifest, 24 structural check results.

**Neither file was transferred to the owner's PC through this GitHub branch.** The owner's Windows Codex must request a private/OWNER-mediated archive transfer and verify the SHA. If unavailable, record `SOURCE_BLOCKED_NOT_RECEIVED`; never infer source bytes from this README.

## Implementation handoff (OWNER-authorized, bounded)
1. Check latest #218/#213/#217. Back up and hash the *real saved PC* Place/source/CHECKPOINT. Keep v37 final 2/3-client QA and older v39 bounded restore ahead of any D18 Studio integration. Never overwrite other chats' D01–D17 files.
2. Securely receive OWNER's V2 ZIP; validate SHA256, all manifest file SHA256, no zip traversal or symlinks, and six IDs against verified original 648 atlas. Apply only overlay; do not regenerate all records from a template.
3. Build **6 static lobby/library miniatures + 2-second original idle gestures** only as a small first experimental batch; no new battle stats, damage, NPC directors, vehicle physics, loot/grant authority, or monetization.
4. Test white-outline differentiation, 3-second category recognition, age-appropriate silhouettes, optional low-motion variant, small-screen readable UI, mobile FPS/memory, same 7 free classes, one-time story + tiny plaque upon collection; no rewards with PvP power.
5. Studio Play/Stop/Edit/save/PID exit only in verified isolated target, owner-approved. Label untested items `NOT_TESTED`. Only 6 of 648 concept entries are editorially rewritten; none currently have actual new 3D QA.
6. Source is private commercial IP; no plaintext source on PUBLIC repo, no unauthorized branch/PR merges, direct main writes, Roblox publish, payments, random paid eggs, P2W, or added spend.

## Public-safe numeric manifest
See `handoffs/P0D_D18_EDITORIAL6_META_V2.json` in the same fixed commit.

Official references for the design decision:
- https://create.roblox.com/docs/production/game-design/onboarding
- https://create.roblox.com/docs/production/game-design/core-loops
- https://create.roblox.com/docs/performance-optimization/improve
- https://create.roblox.com/docs/production/analytics/retention
