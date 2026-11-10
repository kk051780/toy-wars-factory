# P0-D D14 CART/RAFT visual-only handoff

Game `TRAP_RAIDERS`, work `p0d-siege-v19`, packet `P0D-D14-CART-RAFT-VISUAL-20261110-02`.

**Scope:** Independent Roblox client-only decorative anchored low-poly CART and RAFT models, 2-seat occupied count (server-supplied *boolean* flags only), conservative event snapshot policy (one round / monotonic seq / four visual instances max / TTL <=20 seconds / cleanup), mobile low-detail option. **NO actual drivable seat, steering, water buoyancy, physics, damage, carrying egg, server-verified occupancy or production integration.** Source ZIP remains private.

Existing server seat contract is already in immutable handoff `0bcf39c22c583604d72ccac47d29fc9d87b7e662`; **do not install a second server occupancy implementation**. PC integrator must derive every packet field from the actual server and verify RemoteEvent source/round. Client visuals cannot authenticate packet provenance. There is no automatic GitHub -> Windows execution.

## Encrypted delivery

- Expected restored ZIP SHA256: `6a7c63113ae1938247d72d42320fcdd2e1145d36632bdb0c7615eb9962e3458a`
- SHA manifest SHA256: `41826fd9e8ceb805278da073d7391598156068fbcbcd193da0b4500bc95f34bd`
- Ciphertext JSON SHA256: `28223100604a4568dc290002df47d7cd622589550c08edd8351ba8b139eeecf5`
- Ciphertext bytes SHA256: `61562b0b4d098e1d21692386e6b9f61e44847d67603a26c28529a9fa64ea4719`
- ZIP file count: `13` (source/tests/docs + BUILD_MANIFEST)
- Tests: `75/75` local Python unittest PASS (including deterministic 1500-step property and source-shape checks); Luau syntax/Studio NOT_TESTED.
- Restoring requires OWNER's **private** key (not stored in this PUBLIC repository).

Use a trusted precreated private Windows directory and the reviewed non-overwriting `tools/restore_handoff_safe.py` at immutable commit `d37eec1b653d060ae27568ddcd5f501da9662081`. Supply `CHAT_CODEX_HANDOFF_KEY` privately in process environment and run with `--expect-game-id TRAP_RAIDERS --expect-work-id p0d-siege-v19 --expect-packet-id P0D-D14-CART-RAFT-VISUAL-20261110-02 --expect-zip-sha256 6a7c63113ae1938247d72d42320fcdd2e1145d36632bdb0c7615eb9962e3458a`. Review code only after authenticated restoration and ZIP manifest verification. Do not extract into or overwrite the true game source directory.

## Pending PC/Studio acceptance

1. Verify newest actual PC source + Studio saved Place SHA; preserve existing v39-H1 scoped results. Close final saved-Place v39 QA blockers and review v43-A priority.
2. Review older D14 seat authority and conflict with cart/raft client visual Remote mapping; display only on approved unpublished isolated Place.
3. Studio Luau parse, two-client CART/RAFT visibility, driver/passenger counts `0/2`, `1/2`, `2/2`, fake packet/stale match, 4-vehicle limit, disconnect/round end, mobile FPS, R6/R15 camera, motion quality, transparent vs solid obstacles.
4. No client vehicle part CanCollide/CanTouch/CanQuery or server state mutation. Stop/Edit/Save/normal Studio exit + verify only owned PID disappears.

**Statuses:** `OFFLINE_PY_75_PASS`, `LOCAL_AES_GCM_ZIP_BYTES_IDENTICAL`, `GITHUB_READBACK_PENDING`, `PC_RESTORED=NOT_TESTED`, `LUAU_PARSE=NOT_TESTED`, `STUDIO_QA=NOT_TESTED`. No main/merge/Roblox publish/real purchase/added spend.
