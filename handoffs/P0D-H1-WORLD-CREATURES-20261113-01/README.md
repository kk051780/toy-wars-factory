# P0D H1: 企画室の初回実ゲーム統合（試作ソース）

**状態:** 8-safe S1全ゲームソース + H1戦術フィールド + 元ソースの動く幻獣を同一Rojoプロジェクトへ取り込んだ。Roblox Studio / 2client / phone / 本当の面白さは NOT_TESTED。公開は禁止。

## 何が実体として入ったか
- src/ のベース21本は固定 commit 3120b9d3c0a5ec58c9f2613c5d186f3493b54f83 の全Git tree 26370ba54608a040d8a968a0ab2744ba2a32fc74 のコピー。Game.server、MapBuilder、HUD、罠、卵、勝敗、再戦、Coach は変更しない。
- src/server/RareEncounterModels.luau = 元 #232 Git blob 30594595d91f18f4b870c3c8109c8155f55f78bd; RareEncounterPolicy.luau = 52364faac20d4bd92fb6fde54ea0ce7f2ca1a84e（元 commit 6ad87b25004165e7e2ede489bceb2ccaaf3abe70 の原本そのまま）。
- src/server/H1FunWorld.server.luau = 新規起動Script。既存S1 MapBuilderが作る TRAP_RAIDERS_S1 を待って同じマップ内に物理的に通れる天空ランプ／高架回廊／海側の橋を追加。空中城・雲・泡は装飾。元の卵、城のコア、HP/攻撃、Player Spawn、RemoteEventは変更せず、2体のオリジナル動く幻獣（星くじら・虹羽ペガサス）を #232 元の Model.create/update で表示する。
- 幻獣は非戦闘、当たり判定なし。発見操作でplayer個別の一時属性のみ付ける。図鑑や報酬の実装・保存・課金・ゲーム勝敗への干渉は無い。
- default.project.json も元8-safeから正確にコピー。ゲーム全体（Game / HUD / Coach）+ H1 worldをひとつのルートからRojoビルド可能な構成。

## 意図的にまだ入れないもの
- 4世界を丸ごと生成する元 #230 Scene.build は既存 TRAP_RAIDERS_S1 の存在を拒否し別SpawnLocationを作るため、直結しない。異なるゲームを二重起動することを防止する。
- 7職業フル仕様、戦闘魔法、騎乗、宇宙の本物の無重力、D18図鑑648収集/永続報酬、課金、公開は未統合。
- 陸海空の別ルートで卵争奪が実際に面白くなるか、天空回廊で弾が通るか、モバイル操作が成立するかは Studio 実測待ち。

## 私的Studio検収（全て未検証）
1. このディレクトリの default.project.json をRojoで新規未公開Placeとしてビルド。v43-Aや既存のPC保存物を上書きしない。
2. F5: 元のロビー、天空の実通路と海の橋、空中城、動く2体が見え、Outputに赤エラーがない。
3. Test→Server & Clients 2人: 卵奪取、納品、戦闘、守護の罠、決着と再戦がベースと同じ。3経路から両陣地に出入り可能。
4. 地上から幻獣のPromptを押して発見。図鑑やRobuxは増えないこと。
5. Device Emulator/実際のAndroid/iPhone: 操作UI、経路視認性、FPS、落下/復帰、正常Studio終了。
6. H0元8-safe .rbxlx vs H1私的試遊：初見15秒の景色・最初90秒の理解度・もう一回遊びたさを比較。単体機能数だけではリリースOKにしない。

## 安全と権限
- H1 overlayは RunService:IsStudio() 以外では自動実行しない。初回リリースの許可ではない。
- #248固有branchのみ、#247企画、#219企画室、#222フィールド、#232元幻獣、#220 sole RC ownerの参照。
- 未検証のゲーム機能を「Studio PASS」としない。正式RCにも mainにもmergeしない。公開/有料/新規支出禁止。
