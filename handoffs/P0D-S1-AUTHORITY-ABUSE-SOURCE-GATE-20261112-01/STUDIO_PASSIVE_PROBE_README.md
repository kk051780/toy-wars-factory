# P0-D S1 Windows Studio passive smoke probes — only OWNER final QA support

Packet: P0D-S1-STUDIO-READONLY-CLIENT-SNAPSHOT-PROBE-20261112-09
Source RC fixed SHA: 5dc6c958ea5549b1e859d6d250e6179e731181fb
Exact genuine Rojo Place: TRAP_RAIDERS_S1.rbxlx, 146522 bytes,
SHA256 f5c0b56cc7d3bbc2d92190dd95cb94f4dfa490f7949f2440655799c5893684a7.

STATUS: ONLY SOURCE-PREPARED. Neither the probes nor their CI are real Roblox Studio,
phone, live Roblox or game release evidence. #220 sole integrator separately owns
the final Windows PC evidence receipt validator and release/score authority.

## OWNER-directed final Windows/Studio QA ONLY

1. Preserve the EXISTING latest Windows PC Place, record byte SHA256 and keep a backup.
   Never overwrite or publish it. Download and SHA-check the official .rbxlx only
   into a SEPARATE LOCAL UNPUBLISHED STUDIO QA CLONE. Do not assume an existing PC
   Place is equivalent to the GitHub RC.
2. In the clone only, paste StudioPassiveServerProbe.server.luau as an ordinary
   Script inside ServerScriptService. Paste StudioPassiveClientProbe.client.luau
   as an ordinary LocalScript inside StarterPlayer/StarterPlayerScripts.
   They are never merged into game source, copied into live Place or published.
3. Run Roblox Studio's local server with TWO actual Studio Player clients.
   Save separately: SERVER Output, RED client Output, BLUE client Output. The
   passive scripts only print P0D_STUDIO_PROBE_V1 lines: they do not create
   remotes, send attacks, teleport, change gameplay or assert any overall PASS.
4. Verify one RED and one BLUE, seven-second countdown, physical move to enemy
   EGG, REAL ProximityPrompt, carry, home score pad, scoring while own egg is
   away blocked, 2 goals -> win, Japanese win/lose, 9s RESULTS, automatic
   new serial/rematch. Observe server-authorized melee after 2.5s spawn
   invulnerability and cooldown, real Humanoid delta, walls and fault/rejoin.
5. Capture first-minute UI at 0,12,32,60s in EACH client, actual role/egg/
   attack instruction/coach, close-and-reopen help, mobile GUI boundaries.
   Studio touch simulation is NOT physical Android or iOS QA. Real phone
   screenshots/performance and input must be separately collected.
6. Retain two real client images/video, Output logs, pre/post Place bytes+SHA,
   Play/Stop, Studio normal exit, mobile/fault outcomes, any FAIL/NOT_TESTED.
   Submit only to the #220 sole integrator's separate final receipt process.
   NEVER count STATUS_NOT_PASS or sample OBSERVED lines as a certified release.
7. CANONICAL_S1_ENABLED=false and D07_D08_RELEASE_REVIEW_APPROVED=false
   are hard locked in current official RC. No boss feature may be claimed or
   enabled without independent explicit OWNER decision and actual engine QA.

## What the diagnostic log lines mean

SERVER MAP_CHECK valid_sides=2: source-generated castles and prompts exist.
SERVER SERVER_ROSTER red=1 blue=1: two players of different sides on actual
server. Each client's own trace/screenshot is still required.
SERVER REAL_EGG_PROMPT / REAL_SCORE_PROMPT: a real Prompt Triggered event.
CLIENT EGG_CARRY / SCORE_INCREASE: a genuine server-authored SNAPSHOT
actually delivered to one local client and reflected objective progress.
SERVER REAL_HUMANOID_DAMAGE: server observed real Humanoid health decrease.
CLIENT PHASE / FIRST_MINUTE / UI_VIEW: server phase plus sampled GUI state,
not guaranteed to prove actual readable phone-size layout or child clarity.
CLIENT RESULTS / REMATCH_OBSERVED: genuine new-round server serial and result.
CLIENT UI_WARNING / BOSS_VISUAL_UNEXPECTED: investigate, do not mark PASS.

These are diagnostic sources only. No credentials or encrypted material needed.
