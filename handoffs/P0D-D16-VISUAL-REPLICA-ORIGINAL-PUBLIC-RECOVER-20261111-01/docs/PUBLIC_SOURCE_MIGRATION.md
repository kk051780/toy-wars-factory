# D16 VISUAL REPLICA — exact legacy source keyless migration

- game_id: `TRAP_RAIDERS` / work_id: `p0d-siege-v19`
- old packet: `P0D-D16-VISUAL-REPLICA-20261110-02`
- old immutable AES envelope SHA: `ec521761a4ceb61f187f0aa83c3a0a5600d16bcb`
- old source file: `handoffs/TRAP_RAIDERS_D16_VISUAL_encrypted.json`
- original ZIP SHA256: `31a53ead53095152ac57d2b0ee49b49c37477c5341ef0bdd25c8c463fd911d7d`
- original BUILD_MANIFEST.json SHA256: `d24a42b3bce31dbef576c2e2977adce83f27185465499909cc846e48d6b9b343`
- original encrypted ciphertext SHA256: `2aa07608f723432f84b0bc14cbd3bd1e3264db164eb577811d96d35e880f14b1`
- exact authenticated AES-GCM restore, entire original ZIP SHA and all 15 original unmodified source/test/docs files verified; original legacy manifest preserved at `docs/LEGACY_BUILD_MANIFEST.json`.
- Original source is PUBLIC for this specific game per OWNER permission in Issue #218. No encryption key is included or required to use the public source.

## Integration safety

The package is the original client-only noncolliding scaled visual ghost reference including `ScaleFxClientPolicy.luau`, `ScaleFxSnapshotBridge.luau`, `ScaleVisualReplica.luau`, and an optional guarded client bootstrap. It is not installed into an actual Roblox Place. Original D16 SCALE_FX server Core `584b11ef24cf3d44695d86b505207491bbd3844e` is preferred over later cleanroom alternative. Do not install both original visual source and cleanroom visual candidate `356dcd0d26aecf7bb5ab3e7d7a697e78a59db74e`. Do not install the optional D08-D16 V1/V2 cleanroom API gates `ac503729...` and `1877222d...` against the exact original server API.

D08 single canonical event chooser only. Source uses server-round elapsed seconds -> bounded `remainingSeconds` for client-local TTL and cannot use `os.clock()` as the original server round time. Real server-side authorized publisher and read-only client display only. No effect on actual original player size, collisions, physics, damage, permissions or monetization. Before use, Windows Codex must protect the newest real Place/HEAD/source checkpoint, verify real current runtime APIs, native Luau, 2-client mobile and Studio clean exit. No assumptions of PASS from Python tests.

No main modification, no merge, no Roblox publish, no spending or change to P0 A/B/C CAS authorization or 5 Automations.
