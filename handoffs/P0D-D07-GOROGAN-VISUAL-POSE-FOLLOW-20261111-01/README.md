# TRAP RAIDERS — D07 Gorogan visual-follow, independent keyless source candidate

`game_id=TRAP_RAIDERS` / `work_id=p0d-siege-v19` / `packet_id=P0D-D07-GOROGAN-VISUAL-POSE-FOLLOW-20261111-01`

**New optional source, NOT a recovery of old encrypted content, NOT an automatic game patch.** The exact original D07 visual, AI, combined server and rig packages are already recoverable from GitHub. This package does **not** change those originals; it addresses the specific integration observation that original `GoroganVisualPrefab.render()` keeps moving the model back to `handle.rootPosition` established only on START, whereas the real R6 Humanoid RigDriver moves.

## Deliverables

- `luau/GoroganPoseOutboxPolicy.luau`: **server-owned, purely functional** `Outbox.new(config)`, `Outbox.sample(state, snapshot)`, `Outbox.close(state)`; maximum 64 validated POSE output value-snapshots, at least 0.20s spacing, 14s lifetime. Does **not** broadcast, listen to any RemoteEvent, subscribe to Heartbeat, sample from clients, move NPCs or create game instances.
- `luau/GoroganVisualPoseFollower.luau`: **client presentation-only pure reducer** `Follower.new(matchId,eventId,stageId,epoch,initialPosition,localNow)`, `Follower.accept(state,packet,localNow,existingVisualPolicyActive)`. Strict round/boss/epoch/poseSeq, replay, anti-teleport speed, local timeout, state-copy and cleanup. Does **not** create a second OnClientEvent listener or change any Player, physics, damage, RNG, inventory or server state.
- `tests/oracle.py`, `tests/test_visual_pose.py`: executable independent behavior oracle, static Luau checks, 45 offline Python tests.
- `docs/PC_INTEGRATION.md`: disabled-by-default optional single-listener handoff for owner Windows Codex.
- `BUILD_MANIFEST.json`: file sizes and SHA256. All actual text is public and requires no decryption key.

### Original sources consulted, never modified

- D07 visual: `e9b0a7496a69bda3e0e6527ff4d112d50cf70e80`
- D07 server rig: `14935dca217391a7d82d809a3856ee602c446704`
- D07 combined wiring: `80a1f0ce15adfb475df0c95677f9966bb760a8ae`
- Original source-backed read-only crosspack audit: `00c78355fad46ed9a53608b7de882a97bc251db6`

**Only if the actual latest PC Place still has visible drift:** one owner-reviewed server sample of the existing real boss render-anchor pose may be sent over the **same existing approved** `TRAP_BossVisualEvent`, as a `kind="POSE"` message. In the **existing** client listener, intercept POSE before `GoroganVisualPolicy.apply`, feed the follower, and on accepted position write `handle.rootPosition=Vector3.new(p.x,p.y,p.z)`; the existing prefab's next `render()` applies it. The existing VisualPolicy remains the sole START/STOMP/END authority. This never creates another event chooser, NPC, damage gate, subscriber, or visual prefab.

**Vertical anchor warning:** `GoroganRigDriver:start` spawns the R6 Humanoid RootPart at `groundPosition + Vector3.new(0,5.5,0)` while the original client prefab is pivoted around the supplied **ground anchor**. Blindly sending raw `RigDriver:getPosition()` can therefore make the client model appear **5.5 studs too high**. The OWNER PC integrator must verify real rig ground/humanoid height/terrain and provide the already-correct `visualAnchorPosition` to the producer. This pure policy does not guess or subtract an offset.

**Default OFF.** No Windows PC integration, native Luau parse, Play/Stop, mobile testing or Studio exit was conducted in this source production lane. Windows owner Codex alone may decide to use it after preserving and comparing the real latest PC Place. If the PC already has a working pose follower, **do nothing**.
