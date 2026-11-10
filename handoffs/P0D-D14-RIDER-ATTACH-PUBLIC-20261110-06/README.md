# D14 Rider Attach Safety (server reference)

TRAP RAIDERS / p0d-siege-v19 / packet P0D-D14-RIDER-ATTACH-SAFETY-20261110-04.

## What is actually implemented

- `luau/RiderMountPolicy.luau`: pure server snapshot→mount/unmount intent state machine (no Roblox physics). Strict round, vehicle, stage S1/S2, monotonic auth epoch/sequence, fresh signed-by-server-in-process snapshot timestamp, two roles only. All player/user IDs and character generations are derived from trusted server roster and original SeatCore. Fails closed on mismatched team/invalid seats/egg/snare/glide/rewind/death. Immediate logout/match-end/invalid-roster cleanup; 1500ms authority lease on lost updates.
- `luau/RiderMountServerAdapter.luau`: optional **DISABLED** server-only experimental `WeldConstraint` bridge with real server-side `HumanoidRootPart` and trusted anchored noncolliding mount parts; never listens to client remotes. Aborts and disconnects on driver mount failure. Requires live PC Studio 2-client, character respawn R6/R15, ladder/fall and avatar collision/replication quality checks; do not enable as playable riding without these.
- `reference/rider_mount_model.py`: independent Python contract implementation; `tests/`: deterministic and randomized negative tests, ZIP/manifest integrity and Luau static checks.

## Integration and safety boundaries

Requires genuine **current** PC `.rbxlx` and latest SeatCore. This packet deliberately does NOT copy or edit vehicle motion/SeatCore. `provider.getTrustedSnapshot(vehicleId)` must be a server-only callable producing roundId, vehicleId, vehicleType CART/RAFT, stage S1/S2, `authorityEpoch`, fresh `seq`, `issuedAtMs`, team, roundOpen, trusted slots DRIVER/PASSENGER with `userId`, `characterEpoch`, exact `seatEpoch`, flags and distanceStuds from server. RemoteEvent payload NEVER yields a trusted snapshot. `getSeatPart` must return purpose-built anchored, noncolliding, static safe local seat mount BasePart and `getCharacter(userId,charEpoch)` must resolve current genuine player character only. Do not use a passenger-provided CFrame. The server must maintain and increment `characterEpoch` on respawn and `authorityEpoch` on driver/seat handoff. This pack cannot establish those facts by itself.

Physical welding is opt-in and unproven; even a successful offline test **does not** establish weld movement, player controls, seat release or FPS in Roblox. Do not enable without real unpublished Studio authority, security, latency and mobile tests. If a mount fails, reject rather than leave a passenger alone on a moving vehicle. All original server permissions and main remain untouched.

## Owner Windows Codex acceptance

1. Read current #218 / #213 / #217 and real latest Windows source/Place SHA. The last public progress described v39 final 2-client PASS and v43-A 2/3-client scoped PASS, but v43-A Studio save and normal exit remained unverified at that report. Check newest genuine PC checkpoint, preserve it, finish missing final checks first.
2. Restore this packet with reviewed `restore_handoff_safe.py` in a new private directory, with OWNER-supplied key, verify ZIP+manifest SHA and test `python -m unittest discover -s tests -q`. Review Luau source with a genuine Luau parser.
3. Compare original SeatCore's actual field/seat semantics and character lifecycle; do not adapt by trusting player Remote. Do not add a second seat permission ledger. Add disabled bridge to an unpublished Studio copy only.
4. With 2 clients: driver+passenger mount, boat/cart pose, kill, disconnect, change team, respawn, seat switch, replay, stale authority lease, round close. Check no character freeze/orphan weld, collisions, R6/R15 and smartphone. If anything fails, leave it disabled. Save Source/Place/manifest/QA and normally quit only owned Studio PID.

PUBLIC repo: only AES-GCM ciphertext and this public-safe README. Private ZIP, commercial source and secret key remain private. No main change, merge, Roblox publish, payments, spending or P0-A/B/C protected gate bypass.
