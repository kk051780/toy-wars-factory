# P0D｜正式RC56＋浮遊クリスタル峡谷／モグロン＝実物57スクリプト（2026-11-14 JST）

**本ファイルは#220の公式RC書き込みではない。オーナー向け非公開Studioバイナリと、最新の成功RCにそのまま積み上げるためのsource/QA成果。旧RC55版を採用しない。**

## 実際に作ったもの
- 最新正式RCの実物は `947cddb5351ba95b9b27597b9ec1828a8297cd66`、[Actions43504336646](https://github.com/kk051780/toy-wars-factory/actions/runs/43504336646) SUCCESS、artifact `14075771698`、本物のRC56 Place SHA256 `3b8df96e32433a645a957604e7f50062a9ffd2e34831d8e6ba21f7ab2bfabc5c`。ここに**1サーバースクリプトのみ追加**、全部で57本。元の56本は**全て一字一句変更なし**、Game/Remote/Store/6技能/保存武器/新保存魔獣進化/天空/無双/秘境4/4を保持。
- 新Script `src/WCS_Integrated.server.luau`のGitBlob `5eb76749414c33c11eb70310b2d1c59c1f945c21` は既存作者 #293 / [PR#294](https://github.com/kk051780/toy-wars-factory/pull/294) の `CrystalCanyon.server.luau` GitBlob `c3cf119e26ab0241a7bd2b0b25acca75a4250e10` 本文6,520bytesを**完全にそのまま埋め込んだもの**。同じ原文が本体に1回だけ存在する。
- 公式GameはX±130、Z±76の場外へ出ると自陣へ強制帰還する。このため**アンカー (0,32,-23)** に浮遊峡谷を構築、元の「SKY_WALKWAY」の赤・青両端から共通の物理坂を1本ずつ加えた。坂最大勾配約0.362、安全レール計4本、強制ワープなし。新しい舞台は元の場外境界内、SkyV5が見つからなければ機能を安全側で省略。
- **体験：** 両岸に原作者のモグロン2体。どちらのチームもProximityPromptからショートカットゲートを14秒開通、4秒再操作制限。橋上に人がいればゲートが閉まらず、迂回橋は常時開通、転落時の階段を維持。課金・有料能力・新Game・HP/score/egg/XP/Storeの第2権威はない。
- OFF切替：起動前の `ServerStorage.P0D_RC_ENABLE_WCS_F01_C01=false`。本Scriptは未公開Studio内でのみ実行。追加Scriptを正式RC profileから除外することで原本56へバイト単位で戻せる。

## 現物検証
オーナー向けに **`P0D_RICH57_FLOATING_CRYSTAL_CANYON_PRIVATE.rbxlx`** SHA256 **`365d6122e73b3199250dc1fb0e01656f88231bd3eb7021f3bfd7af753fca431e`** を作成済み（元の公式RC56 ZIPと共にオーナーChatGPT会話でダウンロード可能、GitHubにはバイナリをアップロードしていない）。元RC ZIP SHA256 `de43ff8676691c1faab498a09f27c64311a5522d7919919834956c26277d26c4`。

**現物RC56から全57本の固定Luauコンパイル57/57 PASS、Python31/31回帰・負例 PASS、ZIP別フォルダ再展開→再構築でSHA完全一致。** 保存済みBEASTポリシーも元ソース完全同一、原作者GitBlob完全一致。完全QA ZIP SHA256 `2c364aa58835209af12b85290149c11befa10343092855951adbdfbab5f40b7e`。GitHubの `tools/build_from_rc56.py` は真正のRC56 ZIP SHA、既存56本、元作者本文GitBlob、追加元ソース・生成Place SHAまでfail-closedで照合。

**未検証：** Roblox Studio実機での橋/プロンプト/坂の物理、2client、Android、実クラウドDataStore再ログイン、OWNER FUN。Luaコンパイルはエンジン動作成功を意味しない。

## #220唯一のRC writerへの依頼
その時点の最新の正本を再確認。もしRC56以降の変更があれば旧Placeごと上書きしない。**統合すべき差分はこの単一のWCS_CrystalCanyon Scriptだけ**。新機能 `WCS_F01_C01_FLOATING_CANYON` を `rc_fastlane/FEATURE_SWITCHES.json` の独立OFF可能な項目として登録、SkyV5への依存を明示。元のGame/Store/Remote/進化・熟練度・他機能をソースロックし、既存の一回のRC native+Rojo SOURCE_EXACT CIを通し、その成功時にのみ正式RC採用とする。OWNER V5方針で事前の人間FUN試遊は要求しないが、公開前には実機/Android/FUNは必須。main/merge/publish/paid/PC/追加費用/5自動化には触れない。

**過去の公式公開品質評価75/100 FUN_NO_GO据え置き。**
