# P0D S1｜7点統合版の独立「実ソース×初回ガイド×途中退出」Luau QA

[専用Issue #238](https://github.com/kk051780/toy-wars-factory/issues/238)／`TRAP_RAIDERS`／`p0d-siege-v19`／`P0D-S1-KIDS-RC01`

## 重複回避

7点統合プレビューの製作者は別チャット（#218 comment 6823326336）。**こちらはその独立レビュー用ブランチに一切書き込まない**。フリーズ済み 7-safe SHA `d319b56d1552713da482189048473f266c7b3fdc` のソースに対する**検証専用**の別ブランチとした。公式唯一のRC `rc/p0d-s1-kids-rc01` とmainも無変更。

## 検証の内容

検証対象は **本物の7点改修後Game.serverとGuardian FirstMinuteModel**。以前成功した6点実ソース `65785c2e3b9bc37a6962f9ace128fbfcbb670901` との差分が、既に元の公式RCに対してネイティブLuau検収済みの #237「SNAPSHOT updateId + stale拒否」**2箇所+4箇所だけ**であることを検証する。元の6点改善（日本語案内、守護初回説明、右罠ボタン、陸上境界復帰、D07ボス失敗時の安全拒否、4人/途中退出のチーム人数計測）は全て残っている。37個の全ゲームソースファイルのSHA256とバイト長を再読込し、元の6点版から更新されたのはGameとFirstMinuteModelの2本だけだと確認する。

次に実際の7点版Game+Coachを、**オリジナルのMapBuilder・Rules・Lobby・Config・TrapRules**と同じ真正Luau実行環境で動かす。前回の #237 ガイドテスト157項目を再実施し、さらに **途中退出で発行された本物のRESULTS通知の後に古いACTIVE通知が届いても、ガイドが巻き戻らないこと**を確認する。不正な6つのGame/Coach変異についても元ソースの一時試験用コピー上で検出する。元のゲームスクリプトや元のGitHub7点レビュー成果には変更を加えない。

CIはPython単体、3ファイルのSHA256マニフェスト、公式Git blob基準の厳密な全37ファイル再照合、ネイティブLuau実ゲーム実行+不正変異6件を必須とする。

```sh
python3 handoffs/P0D-S1-SEVEN-SAFE-REAL-ORDER-CROSS-QA-20261112-08/tools/seven_safe_real_native.py --selftest
python3 -m unittest discover -s handoffs/P0D-S1-SEVEN-SAFE-REAL-ORDER-CROSS-QA-20261112-08/tests -v
python3 handoffs/P0D-S1-SEVEN-SAFE-REAL-ORDER-CROSS-QA-20261112-08/tools/seven_safe_real_native.py --repo . --luau /path/to/native/luau
```

## 安全と受入

native Luauが実Game/Mapを動かすことは **Roblox Studioの実機2クライアント・スマホや子ども試遊・ネットワーク遅延の実測ではない**。今回のパックはソース機能QAのみで、7点統合プレビューへの書込みも公開/販売/自動Codexも行わない。元の7点版の正式な検収と公式RCの採用判断は統合担当 #220 のみ。公式全体進捗もその独占監査値75/100から勝手に変えない。

本番公開・追加課金・main・公式RC・他チャットのreviewブランチ・P0ABC/CAS・5件の自動化を無断変更しない。
