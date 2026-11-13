# P0D FAST-RC｜正式55本の天空城＋重複体験XPを安全に個別切替（2026-11-14 JST）

**新しいRC55の正本から実物を作成してテスト済み。#220による正式RC採用は未実施。旧RC51/RC54スイッチ候補はSUPERSEDED：古いGame・Store・試遊ファイルを正式RCに再適用しない。**

## 固定した元データと本物のQA
- 公式RC55初回SUCCESS head `0dd7f4418d06200e40688c79c8290745cb56834d`、Actions https://github.com/kk051780/toy-wars-factory/actions/runs/43501488524 、artifact ID14074311951。
- 公式RCの実ZIP SHA256 `9fd0c0d388dc8d89e44cd32d97a935ab83b57c6f600623a2699a979a901c466c`、実Place SHA256 `e439aa5d7372e77b0949bb681ed7342485a541c3738f7c7aceede1b6ea23b8c0`。**55本**の実Luauソースを実物XMLから抽出して比較。
- この専用の非公開Place `P0D_OFFICIAL_RC55_TWO_NARROW_SWITCHES_PRIVATE.rbxlx`、SHA256 `cad86bf4429fe688e3b9347b9a5d73988adc8dae3410d60e8439fbebae7600d6`。これと完全な再現コード/負例QA/元ZIPがオーナーのChatGPTに `P0D_RC55_TWO_SAFE_SWITCHES_QA_20261114.zip` でダウンロード可能。再現ZIP SHA256 `f798da4fd5e8d63d48bd09010ab5c263f2383404e3a21c5df9392005fd72d2c3`。Place/ZIPはGitHubに保存していない。
- 4本のみ実ソース置換（H1FunWorld / RealmHunt / V4TrainingBridge / V4TrialOverlay）、**旧55本のうち51本は完全不変**。元Game、PersistentHatchStore、SixSkillAtomicProfile、SavedPveMasteryPolicy、元Remote、Horde、得点、HP、卵の処理、秘境4個の認定ロジックは保持。
- Native Luau（pin `f46d879e28302a430029304f7f6a162aed66f103`）**55/55本を実コンパイルPASS**。実バイナリ・ソース固定・危険な追加権威・再構築まで **Python20/20 PASS**。別ディレクトリにZIP展開→再ビルドで候補PlaceのSHA256完全一致（実行済み）。

## 2つのServerStorage ON/OFF
**H1_SKYV5**：`P0D_RC_ENABLE_H1_SKYV5` は未設定/trueでON、サーバー起動前falseで天空ルート／浮島／雲を生成しない。海ルート・元Game・幻想生物は残す。起動中に空の足場を削除しない。既存REALM_HUNT_V1のSKY秘境が空中Y35.5のまま残らぬよう、OFF時は同一XZ・地上Y2.5へ出す（発見数は4/4のまま）。実物Studioで地上への到達はNOT_TESTED。

**V4_SESSION_PREVIEW_XP**：`P0D_RC_ENABLE_V4_SESSION_PREVIEW_XP` は未設定/trueでON、falseで**重複するセッション内体験XPの加算だけ**停止（OFF中の時間を再ON時に付与しない）。**公式RC55の本物のDEV保存6技能XP・1日30分保存枠・武器熟練度・Game・StoreはOFFにしない。** 保存済みレベルのHUDとSaveStatusのSAVED表示は継続する。旧51本の「V4全体OFF」と意味が異なるためフラグ名を明確に分離。

## Source and exact instructions for ONLY sole RC writer #220
- 本GitHub rootの三つの `src/*.luau` は最終Placeへ埋込済みの全ソースと**GitBlob完全一致**。最後の `V4TrialOverlay` は、最新版RC55オリジナルのGitBlob `fd5f93f982e353b22eed1a5eb29ad965bb73da5b` を元に、`patch/V4TrialOverlay.patch` で変更、生成結果のGitBlob `8db6f1ff1c26f0dd5ec4d9b5916a02311d0deb22` を照合する。GitHub `tools/build_from_official_rc55.py` は**元公式Actions ZIPの完全SHA→55個ソース→4個GitBlob→XMLの最終SHA**までfail-closedで実装。
- #220が**その時点で最新の公式RC HEAD**に限定して4本を積み上げ、元Game/Store/武器熟練度のSHAを守る。既存1本の `p0d-rc-fastlane.yml` CIでnative Luau全本+Rojo SOURCE_EXACT/単一Game/Remoteを一度検証し、そこで初めて正式RCへの採用を名乗る。新しい元RCが進んでいるときは旧55本を無条件上書きしない。
- 切り戻しは元の成功RC55のsource/feature pinへ戻す。別のprivate RC/profileを正本にしない。main・merge・publish・paid・支出・WindowsPC/CAS/P0ABC/既存5自動化を触らない。

**現物Studio1/2人・Android・DEV DataStore再ログイン・人間FUNは未検証で公開前一括ゲートとして維持。S1品質評価75/100/FUN_NO_GOを変更しない。**
