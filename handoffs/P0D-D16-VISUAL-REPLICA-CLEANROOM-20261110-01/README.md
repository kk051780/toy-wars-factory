# TRAP RAIDERS D16 keyless client replica – clean-room alternate

Game: `TRAP_RAIDERS` / `p0d-siege-v19`.
Packet: `P0D-D16-VISUAL-REPLICA-CLEANROOM-20261110-01`.
Delivery mode: `PUBLIC_SOURCE_V1` — literal Luau/Python source without decryption keys.

**Not historical source recovery.** This is a new original implementation, not the
sealed `P0D-D16-VISUAL-REPLICA-20261110-02` ZIP
(`31a53ead53095152ac57d2b0ee49b49c37477c5341ef0bdd25c8c463fd911d7d`).
If the original author reissues the exact source, OWNER Windows Codex must
choose ONE replica renderer, never enable both. No original ZIP/AES bytes were
recovered or decrypted here. Do not count this candidate among exact migrations.

**Contents:**
- `ReplicaSnapshotBridge.luau`: pure *server-owned* display projection, accepts
  only approved `GIANT_ONE` / `MINI_ALL` event snapshots. Its critical TTL is
  `remaining_seconds = expires_at_round_seconds - server_round_elapsed_seconds`
  using the **same server round-elapsed clock**, not Unix/local clock.
- `ReplicaDisplayPolicy.luau`: pure *client* view filtering and local countdown.
  Hard caps are 8 target players x 18 decorative parts, range 90 studs,
  reduced-motion 4 players x 6 parts. Rejects replay, invalid round or expiry.
- `ReplicaClientRenderer.luau`: opt-in camera-local translucent ghost Parts.
  144 maximal decorative parts, anchored, collision/touch/query disabled,
  no real Character mutation and no automatic network or frame subscription.
- Python oracle and offline tests. They do **not** execute Luau.

Only a separately reviewed real owner PC server adapter may produce the approved
bridge snapshot; a client cannot assert `server_authorized` or event approval.
Only the existing **single** canonical D08 event chooser creates effects. This
packet does NOT pick events, enforce scale on real players, or change core HP,
physics, progression, data stores, monetization or player controls. PC integration
is OFF until OWNER specifically authorizes an isolated Studio evaluation.

Required before acceptance: latest PC source/Place/CHECKPOINT SHA; real Luau parse,
2-client visible/hidden tests, GIANT_ONE one actor, MINI_ALL up to 8, R6/R15,
respawn/leave/round/expiry cleanup, reduced-motion phone FPS, Play/Stop/save and
normal Studio exit/PID. The numerical 8 sec/8 x 18/90 are policy limits, **not
observed Studio performance**. Main/merge/Roblox publish/paid/CAS changes forbidden.
