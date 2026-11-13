# PRIVATE61 — 峡谷＋7職PvE＋1卵リレー＋流星橋（一体化）

## 作者と責任
- BASE: #310 QA-enhanced PRIVATE60 `15c4fdd80837a17ced37f85ce43c1a6c2d024722` (parent #308 GAME); has real 60-source WCS+SevenJobsPvE+classic1egg. Not canonical.
- Added: #311 ORIGINAL meteor `25ee44b852985e770976abb47574c8c915e1e1f3`, blob `9ef84d97a2a629581b3bfa214ac1ed3aefe3db55`.
- All 60 existing original scripts are byte-unchanged, especially Game/HUD/Store/Remote and score/HP/XP authority.
- Integration writer for THIS isolated candidate: independent author. Authorized canonical writer: #220 **only**.
- Portfolio key: P0D-032 existing weather idea. **No new idea row created.**
 
## Product
- WCS峡谷自動岸認識→流星で22秒だけ第三の横断ルートを出現。
- 人が橋にいる間は閉じず、両チームが使える。
- Game/score/egg/HP/Store/Remote/XPを変更せず、出現フラグが未設定ならOFF。Studio以外はOFF。
- Existing WCS source (server) is present. In this candidate, WCS boot attribute `true` is added by original #308 pipeline; this new feature creates a *separate* opt-in BoolValue true for unpublished Studio preview only.
- Disabling feature composition (`apply_meteor61.py --enabled false`) gives 60-source content without writing anything. CI independently checks the complete directory byte-digest before and after disabled execution.

## Built artifact ≠ Studio engine
- Workflows on this isolated branch use original #310 build then append ONLY author-pinned `MeteorShortcut.server.luau` as the 61st Script, update only disposable SOURCE_LOCK, RC_FEATURE_LOCK and project ServerStorage BoolValue for preview.
- Native compile all 61; Rojo SourceExact binary all61; assert exactly one correct actual BoolValue in .rbxlx; keep author's 105 native existing feature test scenarios intact.
- **Never merge all of this into official RC/main.** #220 sole authorized writer should review source and cherry-pick controlled delta only after security gate.
- No owner Studio/2client/Android/physical collision or FUN evidence yet. WCS Stage, legacy sky map, engine occupancy and bridge closure require later final tests.
- If CI fails: treat as SOURCE BLOCKED, do not claim 61 build success.
