# Exact source recovery — D16 Scale FX

- game_id: `TRAP_RAIDERS`; work_id: `p0d-siege-v19`
- prior packet: `P0D-D16-SCALE-FX-20261110-01`
- previous sealed source commit: `7242b32760327a527b868f5405d7782265388fe2`
- restored original ZIP sha256: `d5df52cd3b2fdf26bca05bc38123ac81d27024c944c4a465d66e3a4e0ad0c7cd` (authenticated AES-256-GCM and whole-archive SHA256)
- delivery: new PUBLIC_SOURCE_V1 source transport; game code bytes unchanged.
- old root `BUILD_MANIFEST.json` retained byte-for-byte at `docs/LEGACY_BUILD_MANIFEST.json` to avoid manifest schema conflict. Nine source/test/document files preserved byte-for-byte.
- Historic Python model and Luau Core use `ScaleFx.new(matchId)`, `begin(matchId,eventId,kind,actor,roster,now)` and `scaleMilli` (1600/700), duration 8 **seconds**. They do NOT implement the different cleanroom D16 Core API `new()` and `nowMs` or `visualScale`.
- Thus old fallback scale-core commit `883ca3b790c938587c5d9c305a887a1ffff1249f`, optional D08->D16 V1 `ac50372942712503f836fb84d6331ef3bcc4b8f2` and V2 `1877222d4817153435bc5cfacdf1bb4e90d75aff` are **not drop-in adapters for this recovered original**. Keep all on HOLD and do not install both original and fallback. Codex must inspect the genuine latest PC source and design a separately reviewed authentic integration if needed.
- This package contains no encryption key. Neither Windows Codex, Luau parser nor Studio acceptance is implied. No main push/merge/Roblox live publishing.
