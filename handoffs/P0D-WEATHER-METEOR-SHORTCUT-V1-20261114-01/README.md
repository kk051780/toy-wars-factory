# P0D-WEATHER-METEOR-SHORTCUT-V1 — 流星が架ける22秒の近道

- Parent: #219企画室 / #222 WORLD / #250採用 / #220唯一のRC writer。
- Catalog existing ID: **P0D-032「雷・吹雪・流星群」** のうち **流星×一時的な橋だけ**。別企画数を水増ししない。
- Gameplay: 55秒間の通常戦闘 → 5秒前に道の出現予告 → 両陣営が通れる青い橋が22秒間出現。卵持ちの逃走、追う側の先回りで使える。端にプレイヤーがいる間は安全のため閉じない。
- Authority: One original optional ServerScript; `Game`, `Store`, `Remote`, HP, score, XP, paid, saved profiles are never modified.

## Integration (sole authorized #220 writer only)
1. Put `MeteorShortcut.server.luau` into ServerScriptService once. Feature is **Studio-only** and requires ServerStorage BoolValue `P0D_ENABLE_METEOR_SHORTCUT_V1=true`. Missing/false means OFF, and public runtime also remains OFF.
2. Route placement: prefer an explicit anchored Folder `Workspace.P0D_MeteorShortcutAnchors` with anchored BaseParts `A` and `B`, planar distance 14–90 studs and height difference at most 5. **NEW WCS integration:** when no explicit folder exists, if `ServerStorage.P0D_RC_ENABLE_WCS_F01_C01` attribute is exactly true and the actual WCS world has two anchored collision banks, the feature automatically spans the far canyon rim (original WestBank/EastBank), with endpoints around `(-26.5, 32.6, -57.5)` and `(26.5, 32.6, -57.5)` for the unmodified WCS stage. If WCS is unavailable after bounded wait, refuse to enable; never create an invented bank. Invalid/partial explicit folders fail closed.
3. The WCS shortcut runs separately from Moguron's gate and the WCS permanent alternate route. Verify temporary bridge geometry against both bank ledges, castle, spawn, sky/sea paths and stair return in native Studio; validate real collision/foot occupancy and safe closure in two-client trial. Occupancy may extend the 22-second opening. Do not confuse code tests with actual physics safety proof.
4. Preserve source SHA and feature-specific rollback. To disable, set BoolValue false and rebuild (the running live event waits until no player is on the bridge). Use existing Game/Remote/Store unmodified.
5. For official adoption run same-head Luau/Rojo source-exact, negative flags, physical Studio, 2-client, Android and human FUN release QA. Only #220 changes canonical RC.

## Evidence
- Isolated SOURCE only. `RC=NO; STUDIO=NOT_TESTED; FUN=NOT_TESTED`.
- Isolated CI workflow `.github/workflows/p0d-weather-meteor-qa.yml` runs 21 narrow geometry/security/anchor policy checks and a pinned native Luau compiler. Actual successful CI runs must be individually linked; neither is a native Roblox Studio test.
- Current canonical RC and main untouched by this feature submission.
