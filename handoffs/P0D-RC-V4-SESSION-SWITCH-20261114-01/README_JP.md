# P0D FAST-RC first independent feature switch: V4_SIX_SKILL_SESSION

**2026-11-14 JST — SOURCE DELIVERED / PRIVATE BINARY CREATED / NOT YET ADOPTED BY SOLE #220 RC WRITER.** Explicit 2026-11-14 OWNER fast-lane policy applies: *no per-feature human FUN trial before RC integration; retain Roblox Studio 2client/Android/FUN as release gate*. Main, existing RC branch and other authors' sources were not modified by this independent candidate.

## Actual source and feature scope
- Canonical RC selected rich51: source commit `79123d35cd7afdd5f4f9941675bc2d2cf382ac4e` (one original Game, one Remote, original Store) and RC first successful run 43483022604; source originally 51, V4 training **SESSION ONLY**.
- Actual canonical RC zipped binary artifact ID `14066271707` was downloaded and independently extracted, original `.rbxlx` SHA256 `6c9d36d6944301c4fb7317e087f877f5cdeb513b38213608976da4cce1c6bb65`. Source branch original Luau Git blobs: server `326ec2cadbc71ef9d1d3a08e797479d1c6e08203`, client `0859702fdd050e0b66a2c0672c419e5c7adb812a`.
- This lane changes *exactly two existing scripts* **inside V4 preview**, with new Git blobs **server `06491af532efb6a0e9c29e6ebed7f12b200df69e` and client `90ce2e89b59385d25d2405c91deb00074567abd4`**, independently fetched back at fixed HEAD. The original 49/51 source bodies are byte-for-byte unchanged, notably Game, Remote/Score/HP/XP authority, PersistentHatchStore, V7 Horde, eggs/sky, H1 BEAST/WEAPON dojo, and result/waypoint.
- New actual private Roblox XML candidate `P0D_RICH51_V4_FEATURE_SWITCH_PRIVATE.rbxlx` SHA256 `58f19613545ea358c630ba6a6fedbaef8b6c5b855dd9143ae48054a34ebe6e20`. This binary is **only available in the originating ChatGPT download ZIP**, not checked into GitHub and not official RC.

## Operational switch
- FEATURE ID `V4_SIX_SKILL_SESSION`. Studio server `ServerStorage` boolean attribute `P0D_RC_ENABLE_V4_SESSION`; missing/true = ON (compatible current rich51), explicit false = OFF. This is server-owned, not a client entitlement, reward or paid power. Dynamically toggled server-side: 8 additional preview pads invisible when OFF, V4 XP seconds NOT credited, `lastTick` updated each tick to prevent backlog XP on re-enable; original H1 2-pad progression still untouched.
- `ReplicatedStorage` attribute `P0D_RC_V4_SESSION_ACTIVE` is **status-only** for the client; nil/false => V4 overlay OFF, only true => render. The original studio-only guards remain. This first switch covers V4 preview only; H1 Sky/Horde/egg independent feature switches remain NOT IMPLEMENTED.
- Side maintenance: optional V4 bridge friend check now uses `Player:IsFriendsWithAsync`, same old `task.spawn` + `pcall`; verified same-server players only. No new DataStore, `FireServer`, `OnServerEvent`, Remote or Marketplace calls.

## Actual independent source QA
- Original archived real RC `.rbxlx` checksum and old adapter Git blobs checked fail-closed. New XML 51 scripts, exact old 49 unchanged, one Game, two modified sources only.
- Native Luau compiler compiled **51/51 actual embedded source** from resulting Place using pinned upstream Luau compiler; 13/13 locally executed Python unit/negative tests PASS (including source mutation, original Place tampering, single-authority, server switch, client UI gate, original Game exact, no remote/Store new authority).
- **NOT TESTED**: actual Roblox Studio toggle behavior, real physical UI, 2-client, Android, OWNER FUN. New test binary not represented as engine runtime PASS.
- Reproduction/test bundle owner download: `P0D_RC_V4_FEATURE_SWITCH_SOURCE_QA_20261114.zip` (source `.rbxlx`, two full patched scripts, unified patches, exact-source-lock Python builder, 13 tests, README). No paid features and no actual V4 6-skill persistence; **six-skill V4 session XP and 30m focus still reset on reconnect**.

## EXACT #220 fast-lane integration instructions
1. Only #220 sole writer may modify canonical branch `rc/p0d-s1-kids-rc01`. Fork the **existing** canonical source's V4 server/client two scripts at immutable `79123d35...` into new authored unique source commit, applying the exact two source files above. Original 49 scripts untouched.
2. Re-pin the original source assembler's two Git blobs from author old to new expected values above and assert 51/51 total and Game exactly once. Canonical `rc_fastlane/ACTIVE.json` should point rich51 to this new source SHA. Registry `V4_SIX_SKILL_SESSION.independent_switch` becomes truthful for this *one* V4 feature. Keep prior rich51 SHA as rollback and rich47/legacy21 available.
3. Run the **existing one canonical RC Actions build** with SOURCE_EXACT and native/static safety checks. No additional redundant prerelease Studio or private selected UX committee is needed. If Source LOCK mismatch or one/Game/Remote/Store authority violation, fail closed and rollback.
4. Report new RC commit, successful run and Place artifact. Human Studio FUN, mobile, 2 clients remain NOT_TESTED until OWNER batch release gate. Publish/paid/main/merge still requires separate OWNER approval.

**Do not mark SIX_SKILL_DURABLE, full classes, source-only EggRelay or all H1 features as switchable.** This new switch is narrower and genuinely implemented. Last official product quality score 75/100 FUN_NO_GO unchanged.
