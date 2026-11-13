# P0D｜浮遊クリスタル峡谷＋7職業PvE・積み上げPRIVATE59検証

**STAGE: ISOLATED_CANDIDATE_ONLY / NOT OFFICIAL RC / NOT ROBLOX PUBLISHED**

OWNERの「企画がどんどんRCに積み上がる」方針に対する、既存のプライベートRC58 WCSと7職業PvEを**同一の一つのPlace**へ保全合成する試験。Draft PR候補。#220唯一のwriter認証/CAS・正式採用を代行しない。

## 不変の入力と境界
- 正規RC57 HEAD: `34d6d384d04ba1d4a394331a3e5c74f798e57a22`、公式CI [43508562967](https://github.com/kk051780/toy-wars-factory/actions/runs/43508562967)成功。正式RCそのものはこのブランチで変更しない。
- WCS58候補の作者ベース：PR #300 の `db568966f9ef91159cd2489598e485e066064ec9`、修正安全峡谷Script Git blob `7d2afad5e9b8df410ea0eb83ad962cf42ab98e71`、別CI [43516046707](https://github.com/kk051780/toy-wars-factory/actions/runs/43516046707)成功。
- 7jobs PvE作者ソース：PR #297 / SHA `98edf843fb8a8f6123c13a67745b216712bfe63d`。作者の `tools/apply_seven_jobs.py` Git blob `2f5acfb10dfba0fad7b0245a68d16e500c744a61` を固定参照。作者自身のPrivate58 [43512092000](https://github.com/kk051780/toy-wars-factory/actions/runs/43512092000) は native33 policy+58 native+Rojo成功。
- 合成出力の期待は **59 Luauスクリプト（既存57＋WCS1＋7jobs純Module1）**。既存58のうちGame/HUDのみ7jobsパッチ、**残56/58のコードがバイト完全同一**。新たなGame、Remote、Store、XP・得点・HP権威なし。

## 作業の仕組み
`apply_combined.py` は、正規57から作った**一時的な**WCS58ビルドを入力にする。既存ソース/ロック全体とGit blobを確認した後、WCS Scriptを一旦ソースディレクトリの外に退避して**元作者の改変しない7jobs 57→58パッチャー**を実行する。すぐWCSの原バイトを戻して59ソースのSource Lock/Feature Lockを作り直す。異常時は元58を全ソース＋ロックまで復旧してエラーにする。

- WCS側：#295修正済みゲート、欠落起動属性はOFF、Rojo候補Placeは明示的にServerStorage属性trueを持つ。別にWCSフラグでソース自体をビルドから外せる。
- 7jobs側：`FEATURE_SWITCHES.features.SEVEN_JOBS_PVE_V1.enabled=false` にするとWCS58を無変更で維持。Studioで `P0D_RC_ENABLE_SEVEN_JOBS_PVE=false` とすればPvE技をOFFにできる。元作者のルールでは全7職の**中立PvE技のみ**。PvPフル7職ではない。
- workflow `.github/workflows/p0d-rc-fastlane.yml` は既存WCS手順の直後に作者の完全固定SHA checkout＋合成を追加。機能フラグに応じて59/59ネイティブコンパイルとRojo SourceExactを要求。誤認防止の受渡しreceiptを生成する。

## 検証と制約
このREADME記載時は59-source新HEAD GitHub Actions **未確認**。必ず対象Draft PRの同一HEAD Actionsのログで source-lock/59 native/Rojoバイナリが全部PASSしたか確認すること。旧57/58の成功を59の成功に流用しない。

仮に59コードのCIが成功しても、それは**PRIVATE候補**であり、#220唯一writerが正式RCの現HEADを基準にWCS→7jobsを順番に取り込んで各同一HEADのcanonical CIを通すまで、RC採用数と企画工程を更新しない。WCSは独立新規 P0D-059 SOURCEとして分母に追加する場合だけ企画数59。7jobs PvEは「フル7職完了」と偽らず、P0D-008の未完成サブ機能として追跡する。

実Roblox Studio 2client、Android、物理挙動、実DataStore再ログイン、人間FUN=NOT_TESTED。公開品質評価75/100・FUN_NO_GO据え置き。main変更・PRマージ・ゲーム公開・課金有効化・追加支出・PC/Codex起動・Automations変更なし。
