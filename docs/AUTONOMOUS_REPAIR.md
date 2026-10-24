# 毎時ゲーム開発と承認待ちキュー

2026-10-25、毎回の「進めて」を待たず自動開発を続ける依頼を受けた。
毎時タスクがPR #35のレビュー待ちを理由に自身を一時停止したため、キューv2で修正する。

## 常設タスク

- ID: `6adbf0d6a7d881918ce181dff2468867`。既存の毎時スケジュールを維持する。
- ワーカーによるタスクの変更・停止・削除・追加起動は禁止。自身のrun_idを読むpeekだけ可能。
- 待機時はその回を終了し、次の通常実行で再確認する。通知省略のためにスケジュールを止めない。
- 所有者による停止は尊重し、自分で再開しない。main設定のenabled=falseでも編集しない。
- 正本はGitHub。ローカルフォルダの維持やPC常時起動を前提にしない。

## 最大3本の独立したdraft PR

合格した1課題のPRはレビュー用に保存し、別課題を積み増さない。
旧`auto/twf-game-repair`と、新しい`auto/twf-game-repair-<サービスrun UUID>`を使う。
新規修正は現在のmainから開始し、未統合の修正を別のPRへ重ねない。
タイトルの先頭は`[TWF auto-fix]`。mainの自動マージとRoblox公開は認めない。

選択関数は`tools/repair_queue.py`。入力は実際のPRとそのheadの最新QAから作る。

| 観測した状態 | この回の動作 | スケジュール |
| --- | --- | --- |
| 自分のPRにCI失敗 | 同じブランチを先に修正 | 維持 |
| CI実行中・情報不足 | 待機、次回確認 | 維持 |
| 合格PRがあり空きもある | 現在のmainから次の1課題を開始 | 維持 |
| 合格済みPRが3本 | 新規編集せず統合/終了を次回確認 | 維持 |
| 1本が統合/終了 | 空きを自動で利用 | 維持 |
| 同じrunの再試行 | 既存成果を再利用、重複PRを作らない | 維持 |

正規化したJSONは`run_id`と`pulls`を持つ。各pullはnumber、branch、repository、state、
ciを持つ。ciは現在headのsuccess/failure/pending等。別forkや別ブランチは枠に数えない。
Python実行例: `python3 tools/repair_queue.py --input /tmp/queue.json`。
実行環境でPythonが使えなければ同じ規則を取得済みの事実に適用し、判断を履歴へ残す。

## 修正と品質

編集は既存Balance・Server・HUD、新規`tests/auto/*_spec.lua`、新規
`tests/test_auto_*.py`、新規C履歴、実験ログのみ。受理済みのテスト・履歴、
ハーネス、方針、ワークフロー、認証、モデル・費用設定は変更しない。
自分の未統合検査の不備は同じPRで直せるが、削除・弱体化で失敗を隠さない。
PR本文は実際の最終差分と現在headのCIへ更新する。

既存27サーバー/6 HUD negative controlを保ち、新しいLua検査をCIが自動実行する。
新しいUUIDブランチも、信頼するbaseの設定とスクリプトで編集範囲を検査する。
source変更には実行可能な新規回帰検査と正確なサイズ履歴が必要。
GitHubのbase treeを保ち、expected_shaを使って更新する。

## 次の具体的対象

3つの床FeltBattlefield、FactoryFloor、LobbyGroundがCanCollide=falseのまま。
旧main `0e66049e95bc555bfb2a12aeafe46e73ea420c90` のserver blob
`8d6a40fcb602a728f8876ca62194a0acb4bb45b9`を全サーバーのLuaハーネスで
実行し、3つともfalseを確認した。次の空き枠で、床だけを衝突有効にする最小修正と
全サーバーの属性検査を行う。装飾・ユニットの衝突設定、キャラ性能・価格は保つ。
これは属性の再現であり、実機で落下を観測した証拠ではない。
公式API: https://create.roblox.com/docs/reference/engine/classes/BasePart#CanCollide

## 承認と検証の境界

通常の課題選択・編集・検査・draft PR作成は追加指示不要。
キュー満杯でも自動開発タスク自体は停止せず、承認後に自動で続きを選ぶ。
main統合・独立審査・外部モデルAPI・課金・Roblox公開の既存条件は維持する。
Geminiの消費済み試行は再利用しない。実機・複数人・スマホ・面白さは未検証。
登録や実行中表示を成功とせず、実コード・サービス結果・現在headのCIを照合する。
