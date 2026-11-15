# FB025｜魔獣実AI・野生遭遇・魔獣使い指揮・騎乗（実RC82 PRIVATE SOURCE）

**OWNER「つぎ」→ 2026-11-15 直近試遊報告のP0**。既存FB015（魔獣の見た目）、FB004（7職フル能力）、FB020-G（見つけても反応なし）へ一貫して紐付け、重複Game/AIライターを増やさない。

## 実ファイルのソースプロヴェナンス
- **元:** FB024 PRIVATE 82 Script Place、818203 bytes / SHA256 `0c88d572f7fb08df0595ebed5d8cb71d689852ed8db88ee7ffbf7b472bf72b15`
- **新:** `TRAP_RAIDERS_RC82_FB025_BEAST_AI_PLAYTEST.rbxlx` **837563 bytes** / SHA256 `0fdb6932be2d33eb1711d80d8b4a4c9a56be86b05f95faa818c482541e0c54df`
- **ZIP:** `TRAP_RAIDERS_RC82_FB025_BEAST_AI_PLAYTEST.zip` **237533 bytes** / SHA256 `42afa199f80c74d3079c113e71bfddd620cf90833e48e001ae856a490284d2a9`。
- 原本全82 script XML再読、**Game/SevenJobsRules/TrapRaidersHUDの3 script sourceのみ変更、その他79元Lua本文完全一致**（魔獣以外のFB020-024元実体を保持）。
- Game blob: `9e712afc6e64b9bc382365c4f11aca844d36446d` → `a2ebd9471d2ae4ceef7d4026b3c67b5fad68a460`。
- SevenJobsRules blob: `5e04c1b4b62908ebb0dc21db7ae82653d70e8ef8` → `9bb1e4be79974ffddae5dac139444bff375e456b`。
- HUD blob: `3af56301667b783a23f9c641f9b6b6289df0f44f` → `6e667a0680aff26de3833a473512b228d1702377`。
- ZIP内に `SOURCE_PATCH.py`（元FB024実PlaceのSHA固定・実Luau source差分再現パッチ）、`RECEIPT.json` と実Studio `.rbxlx`、READMEを同梱。**PUBLIC repositoryにはゲーム全源/Place binaryを無断アップロードしない**。ユーザー私的受渡しのみ。

## 追加した実Luau挙動（企画書だけではない）
1. **魔獣使いQ**: 既存職選択Server ACK・ACTIVE・所属・卵非運搬・非拘束・生存・5秒CDで、実3D魔獣1体をserver-side作成。2回目以降Qで FOLLOW→GUARD→ATTACKを変更。追従は所有者付近へ実位置移動、護衛は中立兵の実攻撃1件を2.5秒間隔で阻止、攻撃は既存Horde:hitのHP/KOsを変更し個人撃破数へ本当に算入。寿命65秒/各試合・職変更/死亡/退出で実破棄。
2. **野生4体**: 中央森林脇など4座標で体・頭・牙/角・脚/爪・翼・尾・装甲を持つ実3D魔獣をserver生成。29stud内の生存プレイヤーに反応して追跡、距離と射線が成立したら2.7秒以上ごとに元GameのHumanoid:TakeDamage(5)。本物のF/Qアクションを同一元Gameのseq/cooldown/視線/LOSで受け、HP減少/死亡/撃破1算入/22秒後再出現。魔獣使いだけ近接E/tapで野生の仲間化（元の手持ち魔獣は1体上限）。
3. **乗降**: 実VehicleSeatを魔獣モデルに装着して本人のみPromptでSit/降車、同Server tickでSteerFloat/ThrottleFloatを位置更新。ジャンプ/スマホの実制御はStudio未実行であり**動作合格を主張しない**。
4. **移動安全**: original Gameの唯一0.5sec tick、足場下向きRaycast + 前方障害物Raycast + X/Z world guard。元Score/Egg/HP/Store/Remoteは二重作成せず、Clientからターゲット/ダメージを受け付けない。

## 検証・採用
- **独立Python静的 40/40 PASS**（実Place/パッチ再生完全一致、82 inventory、他79原文一致、SHA/ZIP/未承認強制拒否、単一Remote/KO/装備/7職/HUD/終了/負例等）。
- **Native Luau compile, Rojo Full Build, Roblox Studio1人/2人, Android、騎乗入力、ART基準、OWNER_FUN は NOT_RUN**。品質判定は**PRIVATE_SOURCE_PATCH_STATIC_PASS / PRODUCT_NO_GO / ART_NO_GO / OFFICIAL_RC_ADOPTED=0**。
- 次のAUTH: 既存Game/SevenJobs作者 #297 と魔獣元作者 #373/#420 にrebase方式で差分提案。#220のみが最新RCのsource_lock/同HEAD Luau+Rojo/非force CAS、#470が実PlayでWild AI・タム/Guard/Attack/騎乗の実証→OWNER受入。不合格時は同じFB025を修正。
- **YELLOW**: 見た目/演出/AI些細な滑り/アニメ未完成は負債記録し私的RC SOURCEを進める。**RED**: native文法/runtime hard-stop、Rojo/SourceLock、二重Remote/HP/score/CASは停止。main/merge/Publish/課金/PC操作禁止。

このSliceの成功は「ゲームソースを修正した」までで、正式RC採用/試遊合格を意味しない。
