# EGGRUMBLE V3 — 既存8領域の単一試合への安全受入・重複防止（2026-11-16）

OWNER指示：「他と同じことはするな。キャラ、フィールド、バトル、城、中立兵、アイテム、ロビーをバランスよく進めろ」。すでに各担当が作った独立Studio試作を**コピーし直さず**、有効なものだけ現行EGGRUMBLE V3（TEAM / BATTLE_ROYALE）に取り込む。ここでいう受入は **隔離Studio SOURCEの構成に追加すること**であって、公式RC / Android / OWNER試遊の合格ではない。

## 現物コード照合に基づく8領域の状態

| 領域 | 既存実装の現物と再利用 | V3統合状態 | 次の不足と真正担当 |
|---|---|---|---|
| キャラクター | `SevenRoleCombat` / `ProceduralSkills` / `WeaponSilhouettes` | 7職21技・7武器・21ポーズ SOURCE統合済 | 3D Rig/動作が本当のR6/R15/AJUで成立することを#470/#420実測 |
| フィールド | V3の3攻略路・尾根・森＋独立 `ValleyLandmarkKit` | V3基本3路あり／LandmarkKit本体は別試作 | 重なる固体地形が経路遮断を作る可能性があるため**安易に二重配置しない**。#222/ARTがPathfindingと実地形整合後に導入 |
| バトル | `AttackGeometry`,`SevenRoleCombat`,`SkillFX`,`ImpactFeedback` | V3同一試合に接続済 | 音・豪華専用モーション/低Android実機/対人実測 |
| 個人城・卵 | `CastleMatchRules`、V3個人城モデル、独立 `EnterableCastleInterior` | V3本体の城/複数卵/盗取/全城脱落は接続済、独立Interiorは未採用 | **新Interiorを重ねると城門・壁・卵倉庫が二重化**する。作者#城/#220が既存構造を置換するまでは合流禁止 |
| 中立兵 | `SwarmCombat`＋独立 `NeutralStoneGiant` | 大群/本物KOは統合済、石の巨人は独立試作 | **StoneGiantの元ソースにsessionActive/canEngageオプションを追加して誤被弾防止、V3に各モード1体をSOURCE統合済**。独立した新ボスを複製せず、7職技→弱点実HPの攻撃配線を追加。実Studio/Androidで同時2モードの本当に安全な動作は未検証 |
| **アイテム** | **既存 `FieldItemPickups` の本体を無変更再使用** | **今回 `RaidItemIntake` でTEAM・BR双方へ初めてSOURCE接続** | 9個を3攻略路×左右中央に分散。各生成回1回取得・35秒後再出現/クールダウン/所有城生存を既存作者がサーバ検証。Studio取得/スマホ入力未試験 |
| ロビー | V3内の7職台座/TEAM・BRポータル＋独立 `LobbyUXPreview` | V3本体の実キュー・AI枠補充は接続済、独立LobbyUXは未採用 | 独立プレビューは選択属性だけで実キュー開始しない。台座と入口を**二重生成しない**。#ロビー作者の改善点を現行V3へ source-selective |
| バランス | `CastleMatchRules`,`CombatBalance`と独立 `BalanceMetrics` | 城HP/防衛予算・技CD・7職数値はV3ルールとして使用 | `BalanceMetrics`の理論的な動的NPC予算やスコアは**試合未接続**。source合格や数字をStudio実測と混同しない |

## 今回実装した「アイテムの公平な3×3配置」

**追加ファイル** `EGGRUMBLE_RaidItemIntake.luau`。源泉 `EGGRUMBLE_FieldItemPickups.luau` はこの統合作業では**無変更**。別担当が35秒再出現を追加しており、その実装を尊重して契約QAのみ追随している。本体は常に同じ順序で HEAL→DASH→SHIELD を9回循環するため、配列順に配置座標を並べ、3攻略路（z=300/470/640）と左/中央/右（x=-140/0/140）**各行・各列に3種類をちょうど1つずつ配置する**。TEAMはx中心-620、BRは+620で別マップ。公式Gameや複数プレビューへ二重起動しない。対人/対城/課金強化は追加せず、既存の取得回ごと原子的ロック・35秒再出現と生存判定をそのまま維持。

- `EGGRUMBLE_LobbyCastleModesPreview.server.luau` の **Rules.startの後** `RaidItemIntake.start(session,root,FieldItems)` を **1回だけ**呼ぶ。試合終了時は session.world破棄で全アイテムが消える。
- Sourceが壊れてもコア試合を止めない。任意アイテム連結の例外は `YELLOW_ITEM_OPTIONAL` と警告、部分的なフィールドアイテム模型を破棄し、複数卵・城・大群は継続。**ゲーム内の試合ルールそのものの障害はREDとして扱う**。
- native Luau CLIで配置の各列各行3タイプ均等・2モード分離・二重起動防止・エラー巻戻しを実処理検査。Pythonはソース結線・独立試作の二重起動禁止を検査。

## 追加：中立石巨人の同一試合受入（SOURCEのみ）

- 元作者の`EGGRUMBLE_NeutralStoneGiant.luau`だけを拡張し、既存`Boss.spawn(workspace,at)`を残したまま、V3のみ任意の `options.isMatchActive` と `options.canEngage(player)` を適用。タイミングの前後と2秒予告→28ダメージ衝撃波をチェックし、別モード/城陥落者/キュー外/終了試合への被弾と攻撃を防止。
- 新`EGGRUMBLE_BossSessionFence.luau`は**ボスを作らない小型の純Luau入場セッション判定**。同じV3 hostがTEAMに1体、BRに1体だけ生成し、World.destroyで退場。既存の`SevenRoleCombat`の本物の扇/線/円の形・障害物レイチェックを使って石巨人のコアへ7職技がダメージ。通常の雑兵Humanoid死亡KOには加算せず、別`EGGRUMBLE_BossDefeats`で確定撃破のみ記録する。
- それぞれ同じ試合の大群・卵・城・3路・9個の回復/疾風/盾・7職ロビーを維持。失敗時は部分ボスを破棄し`YELLOW_BOSS_OPTIONAL`として試合継続する。
- Native Luauが**同時TEAM/BR 2つのセッションで互いの攻撃遮断、ロビー移動、陥落、試合終了、古いsessionの再利用拒否**を真正実行。実際のボスモデル・衝撃波・視界がStudioで適切かは未試験。

## 次に取り組む実機品質・所有権

#470: 1P+15AIのTEAM/BRで全アイテムが拾えるか、アイテムが地形/城の壁に埋まらないか、卵携行中DASHとバリアのゲーム公平性、3種類各CDおよび死亡/退室中の二重取得を**Studio実機**で再確認し不具合は隔離SOURCE修正。#420: アイテム視認性、モバイルUI占有と低FPS。#222: LandmarkKitと城・3路の地形重複とAIナビメッシュ解決。#中立ボス担当: 巨人の衝撃波にセッションIDを持たせTEAM/BR跨ぎ誤被弾を修正。#220: 真正writerだけがSOURCE-CASと同HEAD Studio QAを通して本番RCへ source-selective採用。

**現状は SOURCE_WIP / Native純ロジックのみ / Studio・Android・本番RC・OWNER受入は未検証**。main直push、無断PR merge、Roblox Publish、課金ON、新規外部素材は禁止。
