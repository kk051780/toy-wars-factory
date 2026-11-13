# P0D-EGG-RELAY-001｜実RC54からの最小差分：卵リレー（隔離ソース候補）

## 最新実体と採用境界

2026-11-14時点の唯一の公式RCの**最初の54本ネイティブ/Rojo PASSの実物**を読み込み、2つの現在存在する卵モードのGame権威に合わせて構築した**実Gameソース差分**です。従来の仕様書だけではありません。ただし**この枝は唯一の公式RCではなく、Roblox実機で成功を確認していません。**

- 原本：#220 canonical RC branch `rc/p0d-s1-kids-rc01`、真の54-source Actions [43491029567](https://github.com/kk051780/toy-wars-factory/actions/runs/43491029567)、artifact [14068663217](https://github.com/kk051780/toy-wars-factory/actions/runs/43491029567/artifacts/14068663217)、対応済みRC HEAD `2e86ac4fd0d4cb67fd7c673dc4e891b2af6bdc2c`。
- ダウンロードした**本物の `.rbxlx`** SHA256 `1afdb2661b47eafa97985b27eaab5b0236d15f6f6e21863d089cebaf7e745758`。RCがその後進行していれば**必ず最新HEADに改めてリベース**する（旧Placeへ全面差替えは禁止）。
- この作者の隔離候補 `P0D_RICH54_EGG_RELAY_ISOLATED_SOURCE_CANDIDATE.rbxlx` SHA256 `c744765df52b572179dd8dc17a28c6592f1c489177ce5a570e40ac529bf78a8a`、55 Luau source、**元54のうち52本バイト同一**。既存GameとH2FiveEggRulesの**2本だけ**の変更、既存作者の純粋判定EggRelayPolicy ModuleScriptを**1本だけ**追加。追加Remote・Game・DataStore key・Store権威なし。
- GitHubには厳密 `Game.patch` GitBlob `a20a1f2599af5ec9f62c5b05206b89886341906b` と `H2FiveEggRules.patch` GitBlob `92b04190d01483354a361e059559f7ac95fbef95`、固定元政策GitBlob `ef9b65bd6520231f299f21c5cfe2aa250798c8d0` がある。各patchが旧54ソースにfuzz=0で適用できることをローカル検証済み。
- `build_from_rc54_patches.py`：公式の旧RC54実Placeと3つのGitHub原文をソースロックし、**同一55 PlaceのSHA256へ再組立**するPython道具。元のRC/他の作者/Studio/公開環境は一切変更しない。

## ユーザーが遊んで理解できる挙動

チームの卵を盗んだプレイヤーの頭に「🥚 パスを受け取る」ProximityPromptを出します。**近づいた味方が受け取り操作**を押し、サーバーだけが実Team/現持ち主/次の受取人の空き手/双方生存・未拘束/距離（水平8、垂直4）/実raycastで障害物なし/ラウンド一致/12秒再パス待機/卵の保持バージョンを検証。OKのときだけ既存の唯一のGameの持ち主情報を**待機を挟まず**更新します。

- **通常1卵モード**：元の `match.eggOwners[eggId]` と `carry[Player]` を同時変更。旧得点/卵消失処理や再戦はそのまま。
- **5卵得点モード**：元の `H2FiveEggRules.relay` を追加して、既存の `h2ScoreState.carryByPlayer`、`eggs[id].holder`、`transferSeq` を1回だけ変更。保持中の得点時間は維持、得点を追加しない、卵数は5個を保存。元の `H2Score.assertConserved` を呼ぶ。Game自身の `carry` 表示も同時に合わせる。
- Remote追加無し。信用しないclient actor ID/位置/時刻を一切受け取らず、発動したProximityPromptの実Playerだけを確認。敵/自分/壁越し/死者/拘束/既に卵所持者には渡さない。
- **OFF切戻し**：Studio検証時 `ServerStorage` 属性 `P0D_RC_ENABLE_EGG_RELAY=false`。元の正式RC54ソースは変えない。仕様は**Studio専用 private candidate**、公開ゲーム利用は不可。#220が正式RCの独立機能スイッチと源LOCKを管理する。
- UI注意：相手チームにもPromptが表示される場合がある（サーバー側では必ず拒否する）。スマホHUD/画面重複と3D障害物raycastの**実Roblox Studio検証が必要**。

## 実行証拠・過大主張禁止

1. **ローカル実ソース差分/実XML検査15/15 PASS**：真の旧54 source保存、2本以外52本完全一致、Game/Remote/Store一意、元の得点・XP処理の数を維持、候補SHA一致。
2. **H2FiveEggRules実ルールLua5.4互換実行20/20 PASS**：元のH2本体と新relay関数を最小Lua5.4文法変換だけでC `liblua5.4.so.0` 実行。敵チーム拒否・二重パス・二重得点・保有先の納品・保持秒継続・タイムアウト・卵5個の保存確認。**本物のLuau CLIではない**。
3. 以前のEggRelayPolicy純粋判定はPython43/43 PASS・Lua5.4互換41/41 PASS。今回の候補に対する**実Luau全55 native compile、真正Rojo source-exact、Roblox Studio1/2、Android、OWNER FUNはNOT_TESTED**。
4. 55-source XMLは本物RC54のソースから構築した**isolated candidate**、物理・UI・ネットワークが正しく動く保証ではない。正式RCへの組込みも、公式S1完成度加点もしていない。

## 唯一の統合者 #220 への直結依頼

**他のChatがRC branchを書かない。** 最新RCを読んだ#220が、本差分を最新実Game/現H2へ移植し、`EGG_RELAY_V1`を**機能OFF時に旧動作が完全復帰**するソース／assemblerスイッチにする。既存`Game`/H2 score/唯一Remote/Storeの権限を保ち、元作者の他スクリプトを触らない。最新RC HEADで全スクリプトのネイティブLuau compileと実Rojo `.rbxlx` SourceExact、二重スコア負例を同一RC CIで検証。#220が固定RC SHAとrollback証拠を出して初めて `RC` 進捗へ。新OWNER V5では各機能のStudio事前試遊はRC採用の前提にしないが、実機2client/Android/人間FUNは**公開前一括ゲート**で必要。

USER/OWNERは現在の旧S1完成度75/100 FUN_NO_GO、公開未許可、企画55件中18件のRC実装（この卵リレーは未計上）を引き続き区別する。追加課金、main変更、merge、公開、PC/Codex自動実行、既存Automations更新は行っていない。
