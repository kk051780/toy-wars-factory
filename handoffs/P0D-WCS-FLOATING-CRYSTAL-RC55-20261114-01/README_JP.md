# P0D / クリスタル峡谷 × 橋掘りモグロン：最新RC55への本物のゲームソース統合

**2026-11-14 JST。非公開Studioプレイ用の56スクリプトを実生成・ネイティブコンパイルしました。ただし正式RCの#220 writerによる採用・Studioでの実プレイは未実施です。**

## 正本・作者の再利用
- 統合元は #220正式RCの本当の成功ビルド [Actions43501488524](https://github.com/kk051780/toy-wars-factory/actions/runs/43501488524)、HEAD `0dd7f4418d06200e40688c79c8290745cb56834d`、artifact `14074311951`、実物 `P0D_CANONICAL_RC_rich51.rbxlx` SHA256 `e439aa5d7372e77b0949bb681ed7342485a541c3738f7c7aceede1b6ea23b8c0`。RC55は同一Game/Store/Remote、6技能DEV保存・保存済み武器の中立敵PvE強化・天空/海・4秘境・無双戦闘を含む。
- **企画室既存のF01+C01を再利用**。企画・源泉は #293 / [Draft PR #294](https://github.com/kk051780/toy-wars-factory/pull/294) の作者既存ソース `CrystalCanyon.server.luau` Git blob `c3cf119e26ab0241a7bd2b0b25acca75a4250e10`。**その6,520バイトのLuau本文を一字一句変えず**、元Gameの実地図に安全配置する起動コードを前置して1本のScriptにした。元作者ブランチ・正式RC branch・mainは未変更。
- 新しい実際のサーバースクリプト `src/WCS_Integrated.server.luau` Git blob `5eb76749414c33c11eb70310b2d1c59c1f945c21`。56本中**元55本のソースが完全にバイト同一**、追加1本のみ。旧55の唯一のGame・Remote・HP・得点・卵・Store・PvE武器熟練度・RealmHunt4/4に変更なし。

## 新しい遊び方（非公開RC56候補）
- 「浮遊クリスタル峡谷」は現Gameの範囲内 **anchor=(0,32,-23)** に配置。原作者案の地上150×85の舞台をそのまま既存マップの上空へ移設。旧Gameの場外判定は **|X|>130 / |Z|>76** で強制帰還するため、場外に造ると遊べない実バグを避けた。
- 正式H1の `SKY_WALKWAY`（Y16、Z18）の**赤・青両端から独立した緩い上り坂を接続**。両方とも中心Y16からY31、水平長約41.4で上昇勾配約0.36。合計2本の全職共用橋、転落軽減レール4本。**歩ける実体のルート**であり強制ワープ/移動課金なし。
- 両岸には原作者の「橋掘りモグロン」2体。ProximityPromptで、中央のゲートが14秒間開き、4秒クールダウン。ゲートが閉じるときは橋上に人がいれば待つ。迂回用 `AlwaysOpenSafeRoute` と低地から登る階段は常設。赤/青いずれも使用できる。
- **サーバー起動時feature flag**: `ServerStorage.P0D_RC_ENABLE_WCS_F01_C01=false` なら丸ごと非生成。未設定・trueでStudio上ON。既存 `H1_FUN_WORLD.SKY_WALKWAY` がない場合は生成を拒否（天空城をOFFにした構成に到達不能な島を増やさない）。
- **Studioのみ** `RunService:IsStudio()` を検証し、公開サーバーでは実行しない。公開許可を与える処理・課金・DataStore操作・二重Gameを含まない。

## 再現可能な実物とQA
- 新しい未公開Studio用 `P0D_RICH56_FLOATING_CRYSTAL_CANYON_PRIVATE.rbxlx` SHA256 **`adc667a507fc3f4e691140888300dc8926f7617e3ae1db148817492081788d0f`**。元RC55からPython `tools/build_from_rc55.py` でXML内のオリジナル55本を一切改変せず1本足し、元作者ソースGit blob、公式RC ZIP/Place SHA、56本、単一Game、Byte-for-byte GitHubソース一致・XML再parseを**fail-closed**で検査。
- 元の作者55本+新しい1本を **固定Luauコンパイラで56/56本すべて実際にコンパイル PASS**。本当のZIP/Studio XML・地図の境界・接続坂・ゲート14秒・権威重複拒否・改変負例を **Python 30/30件実行PASS**。ZIPを別の場所へ展開し再ビルドしてもPlace SHA同一。
- 完全なテストコード `test_rc56.py`、元のauthor script `CrystalCanyon_original.server.luau`、純粋builder、元公式RC55 ZIP、生成された56本Place、SOURCE_LOCK、READMEをオーナーの会話ZIPで提供。GitHubにはソース+再構築コード+結果証拠。**本物のRoblox Studio物理挙動、2client、Android、OWNER FUN、DEV DataStore再接続はNOT_TESTED。**

## 正式RC担当 #220：既存の1つのRCだけに採用する方法
1. 必ず**その時点の最新正式RC**を確認。初回作成時の正本はRC55 `0dd7f...` だが他チームの採用が先行した場合は全体を上書きしない。オリジナルWCS-F01+C01の作者PR #294には編集を加えない。
2. この`src/WCS_Integrated.server.luau`を**独立オプション1本**として既存`ServerScriptService.TrapRaidersS1`へ追加。元55本の権威は一切置換せず、唯一のGame/Remote/Storeを維持。元作者の6,520バイトソースが失われないことをGit blobで照合。
3. `rc_fastlane/FEATURE_SWITCHES.json`で `WCS_F01_C01_FLOATING_CANYON` を独立OFF可能な対象として選択。必要なら旧SkyをONの前提依存として登録。無効時は新Scriptのみ除外して**元RC55へそのまま戻せる**。実行時ServerStorage属性falseも追加のフェイルクローズ。
4. `#220`のみRCブランチを書き、**既存の1本のRC Actions**でsource-exact 56本、Luau native、Rojo、単一Game/Remote、署名済みrollbackを確認。RC登録前の人間FUN試遊はOWNER V5方針に従い不要。公開前にはまとめて2client/Android/床衝突/実際の面白さの確認が必要。

**現在の評価は「本当の非公開Studioバイナリ＋ローカルソースQA合格、正式RC未採用」。公開品質の過去評価75/100 FUN_NO_GOに加点しません。main/merge/公開/課金/支出/OWNER PC/Codex/CAS/P0ABC/5既存オートメーションは変更していません。**
