# Independent S1 source handoff schema finding (2026-11-11 JST)

**Game:** TRAP_RAIDERS / p0d-siege-v19 / P0D-S1-KIDS-RC01

**Affected actual, immutable author source:**
https://github.com/kk051780/toy-wars-factory/blob/35d7d0525388e885aac8281eff2315a59831e0cf/releases/P0D_S1_KIDS_RC01/BUILD_MANIFEST.json

**Normative original verifier:**
https://github.com/kk051780/toy-wars-factory/blob/b519a17a3152613666822b7d9660742f93a739b7/handoffs/P0D_PUBLIC_SOURCE_HANDOFF/tools/p0d_public_pack.py

## Finding: PUBLIC_SOURCE_MANIFEST_SCHEMA_MISMATCH — confirmed source-contract defect

The initial S1 `BUILD_MANIFEST.json` at that pinned game commit contains the
seven root fields `files`, `format`, `game_id`, `packet_id`,
`public_source_allowed`, **`status`**, and `work_id`.

The established V1 `verify()` contract requires the root key set to be exactly
`format`, `game_id`, `work_id`, `packet_id`, `public_source_allowed`, and `files`.
Therefore the extra `status` root field causes `manifest schema mismatch` even
though the original S1 manifest's 15/15 per-file SHA256 and sizes previously
matched the exact remote source. This is a **pre-existing, concrete handoff
blocker**. Source-byte integrity and strict packaging acceptance are different.

The independent QA checker previously checked the SHA values and Rojo wiring
without requiring this official canonical manifest schema; V1.3 closes that gap
and its fixture recreates the extra `status` field to prevent regression.

## Exact smallest safe owner action (SOLE #220 CHAT-INTEGRATOR)

1. Work ONLY on its own isolated `rc/p0d-s1-kids-rc01` branch. Keep all Luau
   gameplay byte-for-byte unchanged for this schema-only correction.
2. Keep `status`, `game_ready=false`, `studio_status=NOT_TESTED` and
   `release_approved=false` state in `docs/RELEASE_STATUS.json`, which is the
   appropriate status document; **remove only the extra root `status` from
   BUILD_MANIFEST** by regenerating with official `p0d_public_pack.py build`
   using the same verified source tree and packet ID.
3. Verify the rebuilt source with the exact original `p0d_public_pack.py verify`
   (not just a helper that checks SHA), then run independent
   `verify_source_snapshot.py`. Pin the new author commit and all file digests;
   do not retroactively alter the old Git commit/SHA claims.
4. After actual D07/D08 integration and complete plan/receipt creation,
   run independent `verify_rc_wiring.py` on the real assembled RC; the
   gameplay-trace QA and final OWNER Windows/Studio verification remain separate.

**Do not change:** main, unrelated feature branches, real Windows Place,
Roblox public publishing, paid functionality, protected cross-P0 controls, or
existing automations. The S1 first release remains NOT_AUTHORIZED.

## QA truth

- Actual fixed initial S1: 15/15 remote file SHA256 and size verified
  previously; 3/3 Rojo source mount mappings verified previously.
- Actual fixed initial S1: strict PUBLIC_SOURCE_V1 schema **FAIL** due to one
  extra key (`status`), per directly read immutable manifest and official guard.
- Offline independent negative fixture covers this failure. Actual rebuilt S1
  with new manifest is **NOT YET AVAILABLE / NOT RECHECKED**.
- Native Luau/real 2-client/mobile Studio and commercial validity are NOT_TESTED.
