# Actual official S1 RC — verified gates and remaining work (2026-11-12 JST)

**In-source ≠ running in Roblox.** This `rc/p0d-s1-kids-rc01` now includes a 30-file full game composition from pinned source candidate `b103389e2089f9ff5a08984fe2f8f6f02aa8b1bc` (import `17ffd5c28bf15aeefa5f524291534f064f74029f`). The immutable `src/` subtree contains 20 actual Luau source files. 30/30 original candidate source SHA256 audit was independently recorded; the source tree was imported at identical Git blobs. Previous 28-file build Python 238/238 and 19/19 assembler do NOT validate the extended 30-file final RC.

### Source/logic status
- Server game match authority and one remote/match/event/damage are defined in `Game.server.luau`. D07/D08 modules are source-present but **explicitly OFF** (`CANONICAL_S1_ENABLED=false`, `D07_D08_RELEASE_REVIEW_APPROVED=false`). Their physical hit behavior cannot be assumed from tests.
- LobbyTeamRecovery and first-minute coach source were added with Rojo mappings. No new server authoritative listener from the client modules.
- Candidate source QA readback: 30/30 SHA256 independently re-computed by separate QA chat; underlying official RC imported exact tree. Full candidate 20 Luau compiler and 21-unit assembler GitHub Actions run status checked as QUEUED, so **NOT PASS** here.
- Independent original S1Rules and D07 attack-window/tightly scoped native Luau tests have PASS evidence, but test executables run outside real Roblox engine and outside this official entire RC.
- Other recommended UI/cosmetic patches and D18 10 optional source-only models are **not selected into this release** pending independent review.

### Next acceptance in order
1. Recheck actual **official RC** `BUILD_MANIFEST.json`, every exact GitHub byte/SHA256 and single authority Rojo; inspect source lock and docs, update #220.
2. Compile all 20 actual RC Luau source files with real Luau (positive and deliberately invalid negative compiler controls); run original Python source tests against actual RC root; run a negative actual-source integration trace under separate QA ownership.
3. Resolve D07/D08 gated activation: reconcile true canonical event and one true damage receipt/2-client warning, including historical red 0.93sec vs blue 1.96sec. Keep OFF if engine proof absent.
4. Only after Chat independent QA and near-final RC, OWNER explicitly initiates Windows Codex single batch: checkpoint latest private PC Place/source/HEAD, compare imports, real Studio 2client/phone, death/quit/reset, mobile HUD & performance, fake Remote/replay, actual boss warning/hit/avoid if enabled, normal Studio shutdown.
5. Human child-friendly first-play and rematch review, discovery/analytics and safe non-P2W value plan, explicit separate OWNER release permission. No payments, game publication, or hidden data collection.

### Data truth
No confirmed public users, D1/D7, payer conversion or net income. No native Studio pass for *this RC*. Preliminary historical PC partial testing (#213) is NOT an approval for newly copied source. Original PC Place is never overwritten by a GitHub Chat commit.

## HUD-only V5 overlay additional evidence
The sole RC writer has selected exact HUD blob 458a23e83d261c51b3bec174e36e183960532f8c from native-tested full-game candidate `0ca2b7ea9f29aa79727b2e7e53a01af093df5b90`. The whole official `src/` Luau tree after this single-file patch is `01aede07b64973a32ba02647c10a9e8b8f8c3285`, exactly identical to source CI `https://github.com/kk051780/toy-wars-factory/actions/runs/43105877169` (20/20 official Luau compiler, original 88/88 Python plus 15/15 result semantic native, 2 rejected negative controls). No server/Remote/gameplay authority modified. Actual official release tree still needs independent specific-SHA QA and Roblox Studio/2client/mobile/real boss attack; both canonical boss flags stay OFF.
