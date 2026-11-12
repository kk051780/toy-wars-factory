# P0-D S1 — Codexなしリリース経路 V1 (source-linked / advisory only)

> Scope: TRAP_RAIDERS, work_id=p0d-siege-v19, release=P0D-S1-KIDS-RC01. This document does **not** authorize game publishing, modify the official release candidate, run Roblox or GitHub Actions, unlock protected gates, or certify real-client QA. Official owner/single-writer authority remains [#220](https://github.com/kk051780/toy-wars-factory/issues/220); cross-chat rules remain [#218](https://github.com/kk051780/toy-wars-factory/issues/218). DO NOT paste API tokens, private place data, or Roblox credentials into this public repository.

## Decision

**Codex is optional; real Roblox execution evidence and OWNER release approval are not optional.**

- **Path A, Studio available but Codex unavailable:** ChatGPT implements the locked and reproducible S1 Rojo source project. OWNER/manual operator uses a backed-up unpublished Studio place for 2-client playtests, mobile/console/physics/performance checks. Studio usage does not require Codex. After gates pass, OWNER decides whether to publish. No routine per-packet PC tests.
- **Path B, no Windows Studio session currently available:** ChatGPT and isolated GitHub branches build, source-lock, test, and independently audit the full S1 place. A pinned Rojo-built .rbxlx is only an artifact, **not** proof of Roblox runtime. With an already-existing permitted private Roblox universe/place and OWNER-configured secrets, Roblox Open Cloud **Luau Execution** can provide headless actual engine evidence; this cannot by itself prove real 2-client GUI/touch/mobile operation. A real phone/2-client player session is still required before public release. Without any provisioned place/credentials, stay in build+offline QA and mark CLOUD_ENGINE_NOT_TESTED.
- **Path C, approved release without Codex:** The **Place Publishing API** can upload an .rbxlx or .rbxl to an **existing** place with version control, and can be invoked from an OWNER-approved workflow instead of Studio's Publish. This is a deploy-to-place operation, **not** the same as making the experience publicly playable: audience/public visibility and content/rating eligibility must be separately checked and explicitly approved by OWNER. Use a private staging experience before any production place. Never have issue comments, pull requests, or automated checks silently trigger live deploys.

## Official documentation (checked 2026-11-12 JST)

1. Roblox official file-based tools and workflows: https://create.roblox.com/docs/projects/file-based-workflows — Rojo builds .rbxlx or .rbxl, place-publishing and Luau-execution APIs support CI.
2. Place publishing API: https://create.roblox.com/docs/cloud/guides/usage-place-publishing — updates **existing** places with correct universe/place IDs, scoped API permission; explicit format application/xml for .rbxlx; Roblox warns that modified EditableImage, EditableMesh, PartOperation, SurfaceAppearance or BaseWrap instances need Studio publishing.
3. Open Cloud Luau Execution API: https://create.roblox.com/docs/cloud/reference/features/luau-execution — executes headlessly in actual Roblox place; task duration maximum 5 minutes; not equivalent to mobile multi-client interaction.
4. Roblox create/release requirements: https://create.roblox.com/docs/production/publishing/publish-games-and-places — publication, audience and content questionnaire are separate from uploading the place. Roblox Kids/Select requires additional account and experience eligibility checks; subscription or refundable fee may apply. Do not enable payments or pay fees without OWNER authorization.

## Non-negotiable release gates / evidence

| Gate | Acceptance evidence | Current official status at document creation |
|---|---|---|
| G0 / authority | OWNER explicitly grants S1 public release for exact RC SHA, intended universe/place, audience, costs, and rollback | **NO** |
| G1 / real S1 full source | #220 sole integrator publishes exact 40-hex SHA, full source-lock/manifest, one authority per subsystem, real .rbxlx reproducible build | S1 source-built candidate exists; latest official RC SHA reported as `1263a03701211a652b99b91d2339575dc8104eff` (recheck before reuse) |
| G2 / static+native offline QA | Independent QA of the **same exact current RC SHA**, including negative controls and security/duplicate reward cases | Much evidence exists but DO NOT reuse pre-trap SHA `5dc6...` as proof of V6 |
| G3 / actual engine | Real Studio or Open Cloud Luau Execution in a known, isolated private place, log+place version/source evidence | **NOT VERIFIED for current S1 RC** |
| G4 / actual clients | Two real Roblox clients complete steal, damage, traps, win, rematch, logout/rejoin on same candidate; mobile GUI/touch/FPS checked | **NOT VERIFIED**; headless script tests don't replace it |
| G5 / players+audience | Child-friendly short initial explanation, test-player replay desire, moderation, content/rating and public audience eligibility | **NOT VERIFIED** |
| G6 / OWNER release | Explicit approval **after** G1–G5 and rollback plan, manual/public API release only to approved target | **NO** |

**Do not collapse progress:** latest sole #220 S1 audited **75/100**; this document contributes **0 points** toward actual game completion or Studio QA. It is a no-Codex path only. No claim that a release is ready. Optional post-S1 field/sky/sea, S2–S4 and all 648 characters must not block initial S1.

## Safest practical execution order

1. Keep all code in distinct public-keyless *TRAP_RAIDERS-only* source branches; no secrets in PUBLIC repo. Continue Chat implementation, locked official S1 integration only by #220; off-branch independent tests by QA.
2. Fix exact current S1 SHA and produce fully reproducible Rojo project, place file, source lock, checksum receipts, negative-control native Luau tests.
3. If an existing private staging universe and an approved secure credential path exist, create **read-only/test-only** Cloud Luau execution tests without writing SavePlaceAsync, production DataStore, or Place Publishing; log version, test script hash, start/end time, stderr/stdout, success and unsupported checks. No automation invokes this on an issue comment.
4. Get **two live clients** and **touch mobile** playtest evidence using the approved unpublished place; inspect castle collisions/guardian slow trap/egg scoring/round reset and resource load. If not possible, stop at **RELEASE_BLOCKED_REAL_CLIENT_QA** even if cloud tests pass.
5. Check account age verification, 2FA, content maturity questionnaire, target age groups and any new Roblox requirements directly in Creator Dashboard. Do not assume all-ages public release is automatically free or available.
6. After #220's independent audit and explicit OWNER approval, deploy the exact approved place (manual Studio Publish or OWNER-approved explicit Open Cloud API call) only to the named target with backup/rollback; verify resulting place version and public audience setting separately. First public availability must not be inferred solely from HTTP 200/201.
7. Once actual players can play, launch measurement only with privacy-compliant instrumentation and no unapproved monetization: 60-second drop-off, finished matches, repeat play, D1/D7, and net proceeds. Any later changes start a new reviewed RC.

## Forbidden shortcuts

- No direct edits to `main`, #220 official `rc/` branch by this lane, auto-merge, public Roblox publication, spend, Roblox key handling in GitHub Issues, P0-A/B/C authorization bypass, or changes to existing five Automations.
- Cloud headless tests are genuine engine tests only when executed against the actual named version and producing evidence; Python mocks/native Luau CLI are **offline**, never labeled Studio/CLOUD_PASS.
- API use can modify a Roblox place and needs separate explicit OWNER authorization. Treat any publication token/credentials as secrets and keep them out of GitHub/public messages.

## Next owner of this lane

This runbook is **advisory** and non-overlapping with #220. #220 sole integrator decides when/if to adopt a Cloud QA adapter. A separate narrow feature claim is required before implementing any cloud test runner. Current authoritative status: [#220](https://github.com/kk051780/toy-wars-factory/issues/220), [#218](https://github.com/kk051780/toy-wars-factory/issues/218), [#213](https://github.com/kk051780/toy-wars-factory/issues/213).
