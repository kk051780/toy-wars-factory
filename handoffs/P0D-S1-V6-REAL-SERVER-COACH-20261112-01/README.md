# TRAP RAIDERS P0D S1 — 本物の試合SNAPSHOTをGuardian向け初回ガイドに通す7ソース結合QA

issue: https://github.com/kk051780/toy-wars-factory/issues/235

## ソース境界を一つのネイティブLuauで動かす

公式RC `1263a03701211a652b99b91d2339575dc8104eff` の Game.server/MapBuilder/S1Rules/LobbyTeamRecovery/Config/S1TrapRules **6本のオリジナルLuau** を、以前成功した実マップ・罠QA `84d061d81ffd28418f6e28e9e85bb684dd0daaf7` の固定テスト環境で実行する。

さらに独立した初回ガイドの実オリジナルLuau `FirstMinuteModel.luau` （Guardian説明改善版の正規固定SHA `e29d37737890671d458072bebe729127878700f6` / Git blob `967ea52df79884e6c73e3e0952d5a97de0d1796e`）を同じVMで動かす。

**実サーバーがFireClientする本物のSNAPSHOT**を正規の `Coach.consume` と `Coach.view` に入力し、REDとBLUEの別々のローカル状態でゲーム状況と子ども用表示が一致することを検証。外部Roblox Instance/Players/Servicesだけが試験用ダブル。テキストのコピーをテストしているだけではない。

### 検証する状態遷移
- LOBBY中の実SNAPSHOT受付と役職選択
- COUNTDOWN → ACTIVEのRED速攻／BLUE守護の表示が役割通り
- 正規ゲーム内で敵の卵を盗んだ瞬間の「卵をゲット！」案内
- 自陣へ届けたときの「得点できたね！」案内
- 2個獲得で勝利し、結果画面の「つぎの対戦も挑戦しよう！」案内
- 再戦後にキャリー・得点・時間表示が初期化
- 以前の対戦の古い結果SNAPSHOT、不正な壊れたSNAPSHOTは拒否
- 60秒後の自動非表示と「？」による手動再表示
- 役職の取り違え、卵を持っていても案内なし、得点無視、結果無視、古い通信受理、60秒自動非表示消失の**6種類の危険変異**を、元のCoachコードの試験用一時変更で検出する

## CIと検収の限界
全ての実ゲームソース・Coachを固定Git Blob SHAで照合し、Pythonの契約テスト14項目・実Luau正規ケース・危険変異6つ・全packのSHA256/ファイルサイズ一致をGitHub Actionsに記録する。ゲーム用サーバーソース/独立HUD原本は**変更しない**。

```sh
python3 handoffs/P0D-S1-V6-REAL-SERVER-COACH-20261112-01/tools/test_server_snapshots_with_coach.py --selftest
python3 -m unittest discover -s handoffs/P0D-S1-V6-REAL-SERVER-COACH-20261112-01/tests -v
python3 handoffs/P0D-S1-V6-REAL-SERVER-COACH-20261112-01/tools/test_server_snapshots_with_coach.py --repo . --luau /path/to/native/luau
```

**Studioでの実機2クライアント・ネットワーク遅延・スマホ実タッチや画面可視性は未テスト**。Roblox外部サービスのモックを使うnative Luau QAの成功だけでS1を公開可能と見なさない。最後の OWNER 一括実機QAは必須。全体進捗は#220の唯一の統合担当の監査に従う。

鍵無し公開ソース専用。main・公式RC変更/merge、Roblox本番公開、支出、OWNERのCodex、P0-A/B/C、既存5自動化への変更は禁止。
