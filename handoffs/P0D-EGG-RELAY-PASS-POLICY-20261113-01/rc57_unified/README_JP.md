# 卵リレー｜実際の正式RC57から58ソースへ統合した隔離候補

**目的**：卵リレーを仕様書や単体判定コードの段階から進め、Roblox Gameのソースとしてクラシック1卵＋H2得点制5卵の両方へ接続する。**正式RCにはまだ未統合であり、Roblox Studioでの実動作確認は行っていない。**

## 入力はRC57の本物

- 唯一の正式RCの初回成功 `639da1af22f8fcee1e609a2637ef3bbcabf33d6f` / GitHub Actions [43508325263](https://github.com/kk051780/toy-wars-factory/actions/runs/43508325263) / 本物の未公開Studio用Place artifact `14077447164`。
- 元Place SHA256 `15521b7dadbd96c0ef1ed12367b5fcf2f3738c4428ebf2fb8c43532b39b8b1a8`、元57ソース。実元Game git blob `9edc39a681eeefb6ec4178b8bbeabf744cac567b`。
- 既存作者の元 `../rc54_candidate/Game.patch` git blob `a20a1f2599af5ec9f62c5b05206b89886341906b` は**最新RC57 Gameにも6か所すべてGNU patch fuzz=0で適用PASS**。H2パッチ `../h2_complement/H2OnlyRelayV2.patch` git blob `68f3df613ad548ab56e755adf91d797a979e8552` も元のH2にfuzz=0で適用PASS。元H2ソースは正式RC55/56/57でバイト同一。
- 新Gameは呼出元を `H2Score.relayWithVersion(h2ScoreState,eggId,actualVersion,fromId,toId,team)` に変更し、単なる保持者移動ではなく**現卵IDとtransferSeqが一致する場合だけH2正本を更新**する。1卵側は元の `match.eggOwners` と `carry` を一致更新。
- **OFF安全**：ServerStorageの `P0D_RC_ENABLE_EGG_RELAY` 属性が**明示true、かつStudio実行**のときだけパスを許可。false/未設定ならPromptも受渡も無効。主運用の正式RCを無断でONにしない。
- 物理UIは元のGameのキャリアHeadへ追加したProximityPrompt「🥚 パスを受け取る」。既存唯一のGame、唯一のRemote、H2Score、Store、XP/HP/score権威を維持し、別サーバーGameや新Remoteを作らない。

## 隔離候補の実結果

- 元57本→ **58本**。元57本のうち**55本が元の実Placeと完全にバイト同一**。変更2本＝`Game` / `H2FiveEggRules`。新規1本＝既存作者pure `EggRelayPolicy` ModuleScript。
- 出力隔離Place（正式RCではない）SHA256 `ab502740b40a2e62344304461d26d89a91a8bc7ec657091ecc5cf7a9b2bfc5d3`。Game結果SHA256 `9dd0c163b86b6a9a5c9affa5920bf4489ff7e528a83130621d508cdad26d797d`。H2結果SHA256 `89e2f07e0000bb6338e44ad41ee812b054226718161136443e64382028558b00`。
- 実ソース独立検査 **Python 26/26 PASS**（途中でテスト自体の末尾改行比較を修正）。元H2正本＋V2移動ルールとGitHub固定48ケースを、Luau特有の表記をLua 5.4互換へ変換して**実際に実行48/48 PASS**。これは本物のLuau CLIやRobloxエンジン合格とは主張しない。
- **未実証**：新58本すべてのネイティブLuauコンパイル、真正RojoによるSourceExact、Studio 1/2クライアント、Android、ユーザーFUN、永続DataStore再ログイン（これらは全てNOT_VERIFIED/NOT_TESTED）。ソースをXMLへ埋め込むだけではRobloxで安全に遊べることの保証にならない。

## 再現方法・統合方法

1. #220唯一の正式RCから**成功ビルドの本物のPlace**を取得（上記artifact ID）。源のSHAが異なればビルダーは停止。旧Placeを現在のRCへ直接上書きしてはいけない。
2. `tools/rebuild_real_rc57_unified.py --original-place RC57.rbxlx --output ISOLATED_RELAY58.rbxlx` を実行。各ファイルの元/パッチ/作者pure GitBlobを固定照合し、最終Placeの完全一致SHAに対して検査する。オーナー向けZIPには元実体＋隔離出力＋独立QA＋実行用の簡易ビルダーを同封。
3. 並列の[PR #296](https://github.com/kk051780/toy-wars-factory/pull/296)は**クラシック1卵のGame/HUD別案**。そのGame変更と本Game変更を**絶対に二重適用しない**。#220がどちらか一つのGameハンドラを選ぶ。この候補は**クラシック+5卵を一つのGameへ接続する代替案**。PR #296採用なら `../h2_complement/H2OnlyRelayV2.patch` のH2純粋部分だけを補完採用。
4. #220が現在の**最新**RC HEADへリベースし、既存Game/Store/Remote/保存レベル/BEAST/SCOUT/秘境を保持。SOURCE-LOCK→OFF復元→**1回の全ソースネイティブLuau+実Rojo SourceExact CI**を通して初めて `RC_ADOPTED`。今のローカルXML生成だけでは採用とは数えない。

**ユーザーの高速統合方針 V5**：機能ごとの実機FUN試遊は正式RCソース採用前の必須条件ではないが、公開前のStudio 2client/Android/人間FUN評価は未達のまま。公式S1前回公開品質評価 **75/100、FUN_NO_GO**。main変更、merge、公開、課金追加、所有PC/自動化の変更なし。
