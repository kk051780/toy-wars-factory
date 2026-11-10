# P0-D D14 Server-only outbound visual publisher reference (PRIVATE SOURCE ENCRYPTED)

- game_id: `TRAP_RAIDERS`; work_id: `p0d-siege-v19`; feature_id: `D14`; packet_id: `P0D-D14-SERVER-VISUAL-PUBLISHER-20261110-06`.
- **New scope**: opt-in server-owned outbound visual-only RemoteEvent `FireClient` mapper. It converts genuine D14 seat+motion pose to per-round monotonic DTO. It does not create a second seating ledger, motion engine, cart/raft geometry, rider attachment, or Remote inbound handler.
- Local reference: `luau/D14VisualPublisherCore.luau` and `luau/D14ServerVisualOutboundAdapter.luau`, Python independent model, tests and PC API mapping docs.
- Inputs must originate from genuine server-only D14 authority and monotonic clock. If the real client visual schema disagrees, **HOLD**, do not invent a passing adapter.

## Fixed sealed artifact

- Restored private ZIP SHA256: `8e4e9a3f20965f5c6fda21dadd7cdb81a898a1f9fb5c5462dcd165c4e157a27c` (bytes 12169, 7 archive entries).
- `BUILD_MANIFEST.json` SHA256: `6812c1e6dd2f37488208839962780edf5af84213e23ac34e1e674a877867a8dd` (6 source/test/doc entries).
- AES-256-GCM ciphertext JSON SHA256: `53749603a43406c8dbc4ebaedc0fd49217d6653bbff8fa069a65db8dcf01f66e`.
- Ciphertext SHA256: `65133742d20ee4266e4e85ce6e94eae5c48951a1822cebb784177b5b8b767052`.
- Local AES-GCM byte-exact roundtrip PASS; wrong key and tamper rejected.
- Independent offline Python synthetic+static tests: **55/55 PASS**. Lua parse / Studio / PC Windows decrypt / mobile = **NOT_TESTED**.
- The **OWNER private decryption key stays out of GitHub**, separate confidential handoff. No plaintext commercial game Luau or private ZIP will be written to PUBLIC repository.

## Dependencies (distinct ownership)

1. D14 server seat authority v2 `0bcf39c22c583604d72ccac47d29fc9d87b7e662`.
2. D14 server CART rail motion 02B `2cd3fb9b31bfe7817ca0ceba7456300c3a41bd12`.
3. D14 server RAFT motion `027fd926a9d315a84f701086448fa5c1febc6697`.
4. D14 client-only CART/RAFT visuals `3c78cd0af618f320fe9d0aafe7569e1e9b95b4b0`.
5. D14 optional RIDER attachment `0af53f121b35f2e822c63514112360d220c92227`.
6. Existing public-safe D14 5-packet preflight `161032464f24b9f147b5b15e3e487598bc45261b` and D14 triad QA `5b93243006c486faf5bbe8867ce7d2702f0c0917`.

## OWNER Windows Codex acceptance instructions

- First re-fetch #213/#218/#217 and current Windows saved Place, source HEAD/ZIP SHA. Latest OWNER-PC priority is **v43-A saved Place cold-restart QA then D07 Gorogan**. Do not automatically switch to D14.
- Later, OWNER directly directs Windows Codex. Download this ciphertext by **fixed immutable commit** and inspect `tools/restore_handoff_safe.py` pinned `d37eec1b653d060ae27568ddcd5f501da9662081`. Provide key via private env var, not GitHub/Issue or CLI argument. Require game/work/packet/ZIP SHA exact matches and a fresh non-overwriting private directory.
- Run offline Python tests; compile the actual Luau scripts; inspect genuine SeatCore/Motion/ClientVisual mapping. Server adapter defaults disabled and only enables on explicit OWNER review after safe seat/round/roster bindings. No `OnServerEvent`.
- Studio unpublished S1/S2 2–3 clients: authoritative seat changes, cart/raft frame sync, spoof/replay, quit/death/round cleanup, client 10Hz/1.5s TTL, mobile viewport/FPS, 4-map/7-job regression, own Studio PID exit. Mark game integration **NOT_TESTED** until actual PC evidence.
- Do not touch main, merge, publish Roblox, real payments/paid APIs, P0-A/B/C CAS/shared locks or existing automations.
