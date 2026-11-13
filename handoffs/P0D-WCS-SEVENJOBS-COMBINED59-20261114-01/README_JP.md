# P0D：峡谷＋7職業PvE 統合59本／正式RC受渡し

**2026-11-14 JST｜隔離試遊候補・実ビルド成功・正式RC未採用**

## 実成果（作成したファイル）

- `tools/combine_wcs_jobs.py`: 正式RC57ソースを保持したまま、既存の[峡谷PR #300](https://github.com/kk051780/toy-wars-factory/pull/300)の1サーバースクリプトと、[7職業PvE PR #297](https://github.com/kk051780/toy-wars-factory/pull/297)の作者純ルール＋Game/HUDパッチを**同一の59本に積み上げる**独立アダプター。
- `.github/workflows/p0d-wcs-sevenjobs-combined59-native.yml`: フリーズした本物のRC57からの再生成、WCS安全テスト、ソース差分、ネイティブLuauコンパイル、33職業ルール検査、固定Rojo実Placeのソース完全一致を自動検収。
- `QA_REAL_COMBINED59_SUCCESS.json`: 確認済みCIの固定SHA・ジョブ・成果物番号と範囲。

## 実際に成功した検査

固定実ソースHEAD `c5c711ad68af97391cb3a08b5ad20c3915ff672c`、[Actions #43516735974](https://github.com/kk051780/toy-wars-factory/actions/runs/43516735974) **completed SUCCESS**。元RC57→WCS＋7職59本。元57の55本完全不変。変更は唯一Game/HUDの2本だけ、新規はWCSと純職業ルール各1本。保存武器・魔獣・スカウト3種、H1/天空/秘境の原ソースを保持。

実ログで **WCS負例9/9、ネイティブLuau59/59、7職業純ルール33/33、Rojo実Place59/59本ソース完全一致**を確認。[未公開59本試遊Place](https://github.com/kk051780/toy-wars-factory/actions/runs/43516735974/artifacts/14081226099) あり。

**何を証明していないか：** Studioでゲームが実際に楽しいか、ゲートとモグロンの物理動作、2人通信、7職PvP本実装、Android、保存再join、公開の許可。すべて未検証。7職業は中立PvE技の候補で、完全な職業システムではない。

## #220唯一の正式RC writerへ

1. 正式RCの新HEADを取得し、WCS PR #300のビルダー配線と独立OFF機能をまず正式RCへ採用。元57本のソースとSourceExactを守り、同一HEAD CIに成功して初めてRC台帳へ反映。
2. 7職業のゲーム担当ソースはPR #297に固定。**元57へ厳密適用してから差分3本をWCS側へ移す**今回の手法を使えば、古いゲーム全体のコピーによるWCS消失を防げる。追加機能OFF、負例、実59本Luau＋Rojoを正式HEADで再実行。
3. このPR #304は#300の子DRAFTで**直接RCへマージしない**。卵リレーPR #296はGame/HUD修正が競合するので、7職統合の次に最新Game/HUDで別途リベース。H2は別権威パッチを二重挿入しない。

企画室公式台帳の直近実値は **RC21/58=36.2%・SOURCE27・IDEA10**。PR #300が新案P0D-059をSOURCE仮登録しているが正式RCでは59番案を追加済みと数えない。S1品質75/100 FUN_NO_GOは従来の値。main変更・未承認マージ・公開・課金・追加費用・新しい自動化なし。
