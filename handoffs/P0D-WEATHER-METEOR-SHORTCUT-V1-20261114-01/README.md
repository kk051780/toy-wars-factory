# P0D-WEATHER-METEOR-SHORTCUT-V1 — 流星が架ける22秒の近道

- Parent: #219企画室 / #222 WORLD / #250採用 / #220唯一のRC writer。
- Catalog existing ID: **P0D-032「雷・吹雪・流星群」** のうち **流星×一時的な橋だけ**。別企画数を水増ししない。
- Gameplay: 55秒間の通常戦闘 → 5秒前に道の出現予告 → 両陣営が通れる青い橋が22秒間出現。卵持ちの逃走、追う側の先回りで使える。端にプレイヤーがいる間は安全のため閉じない。
- Authority: One original optional ServerScript; `Game`, `Store`, `Remote`, HP, score, XP, paid, saved profiles are never modified.

## Integration (sole authorized #220 writer only)
1. Put `MeteorShortcut.server.luau` into ServerScriptService once. Add ServerStorage BoolValue `P0D_ENABLE_METEOR_SHORTCUT_V1=true` only when deliberately enabling feature. Missing/false means OFF.
2. Put an anchored Folder `Workspace.P0D_MeteorShortcutAnchors`, with anchored invisible BaseParts `A` and `B` on safe crossing endpoints, same deck height within 5 studs, planar distance 14-90 studs.
3. Verify temporary bridge geometry against castle, spawn, sky/sea paths in Studio, and verify foot occupancy before closure. An arriving player may extend the 22-second nominal opening. Do not confuse the offline test with actual physics safety proof.
4. Preserve source SHA and feature-specific rollback. To disable, set BoolValue false and rebuild (the running live event waits until no player is on the bridge). Use existing Game/Remote/Store unmodified.
5. For official adoption run same-head Luau/Rojo source-exact, negative flags, physical Studio, 2-client, Android and human FUN release QA. Only #220 changes canonical RC.

## Evidence
- Isolated SOURCE only. `RC=NO; STUDIO=NOT_TESTED; FUN=NOT_TESTED`.
- Offline narrow geometry/security policy tests: `python3 test_meteor_shortcut.py`, 13/13 on local authoring. They are *not* native Luau compilation or Roblox Studio evidence.
- Current canonical RC and main untouched by this feature submission.
