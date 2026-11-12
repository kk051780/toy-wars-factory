# P0D TRAP RAIDERS 8変更版｜OWNER PC実機QA用・鍵なしZIP

## これは実機試験の準備物です

公式RCや公開中のRobloxゲームではありません。SOURCE_SHA `7b4f95a3f424741bbe8ff1c555c5f5a2ed64d4bd` からGitHub CI #43257388055がビルドした**本物の未公開Rojo Placeファイル**を保全し、Windowsの新しい隔離フォルダーへだけ安全に渡します。

- 元CI：<https://github.com/kk051780/toy-wars-factory/actions/runs/43257388055>
- 元GitHub artifact：`P0D-S1-EIGHT-SAFE-HUD-REVIEW-ONLY`（ID13961872174）
- ファイル：`TRAP_RAIDERS_S1_EIGHT_SAFE_HUD_REVIEW.rbxlx`
- サイズ：159080バイト
- SHA256：`b27f401cd6aed7242665098a4cf323184fe13f2ef964b59a3c97b82daf998d04`
- 21本の本来のLuauソース全てが元ゲームの実コードとバイト一致、元CIで12件の危険なXML改変を拒否。8変更版のHUD修正も元#240でネイティブLuau実行43件合格。
- こちらのZIPは鍵・秘密情報を必要とせず、Studioは**自動で一切操作しません**。

## Windowsでの操作（OWNERが最終QAを指示する場合のみ）

1. 最新の8変更版Owner PC QA ZIPを、GitHub Actionsの該当runのArtifactsから取得します。ダウンロード直後にZIPのSHA256をWindows PowerShellで `Get-FileHash -Algorithm SHA256 .\P0D_S1_EIGHT_OWNER_PC_QA.zip` で確認し、最新の引渡しIssueに記載した値と照合してください。
2. ZIPを既存の作業Placeと別の一時フォルダーに展開します。Python3がある場合は `python owner_pc.py --bundle .` で内容を**読み取り専用検証**できます。
3. OWNERの判断で孤立試験コピーを作る場合だけ、例 `python owner_pc.py --bundle . --prepare --destination C:\Users\Public\Documents`（既存の絶対パスのフォルダーに指定）を使います。特定の名前のサブフォルダーを新規作成し、**既にあれば上書きを拒否**します。元のファイルやStudioプロジェクトを一切更新しません。
4. 保存済み通常Placeを保護したまま、手動で新規QAコピーだけをRoblox Studioで開きます。開始/終了・2client・スマホ・卵/罠・場外/退出・HUD遅延・再戦・正常終了を `STUDIO_QA_CARDS.md` と `SCENARIOS_NOT_TESTED.json` を参照してテストしてください。
5. 実機で見た結果は**別の新しい記録**に記載し、#220の公式統合担当へ提出してください。元の30件の `NOT_TESTED` やサーバー承認表示を書き換えないでください。

Pythonがない場合のSHA256手順はPowerShell `Get-FileHash` でも実施できますが、独立した検証・安全ステージングはPython3を推奨。ZIPや書き換え後のPlaceが誤ったSHAなら開かずにBLOCKED扱いです。

## 厳格な限界

このZIPの作成成功、元CIのRojo/Luau成功、Pythonの20件超の陰性検査成功は**本物のStudio二者接続・スマホ操作・実端末FPS・人間の試遊合格を意味しません**。元の試験成績にない「実機PASS」を書き足すことはできません。

P0D全体の最終公開判定と公式RCの変更権は #220専任統合担当およびOWNERにのみあります。最終公開はOWNERの別途の明示承認が必要です。P0A/B/C、main、保護RC、CAS、他の自動化タスクには触れません。追加課金・Roblox公開・Codex/Studio自動操作はありません。

受け渡しパックのコード、検証ワークフロー、試験ログは <https://github.com/kk051780/toy-wars-factory/issues/218> に参照を残します。
