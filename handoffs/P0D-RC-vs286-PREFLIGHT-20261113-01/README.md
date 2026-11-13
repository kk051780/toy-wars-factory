# P0D 正式RC対#286 ソース差分統合ゲート

**実施：** GitHubの正式 Game703行/HUD195行と、別系統候補Game1583行/HUD420行の実ソースを読み、既存行の保持と違いを比較。ソースの同順一致はGame688/703行、HUD188/195行。これはStudioや実動作の合格ではない。

**重要な実害候補：** SCORE_5選択とXP・孵化・DEV保存に `RunService:IsStudio()` の制限があり、単純に新候補をRCへコピーしても完成した公開ゲームにはならない。1つのGame/Remote、既存罠・攻撃・卵権威を維持しながら差分導入し、変更した勝敗・落下・退出・点数・HUDを再検証する必要がある。

**実ファイル：** `source_diff_report.json` に危険差分・次の責任者、`tools/preflight.mjs` は必要git refがローカルにある場合にオフラインでGit blob SHAと既存ルールをフェイルクローズ検査、`tests/preflight.test.mjs` は正常1+異常8件の再現検査。今回V8で同じソース条件を9/9テスト済。Node/CIとStudioは未実行。#220が最新HEADを必ず確認し、#250採用決定後に唯一RC writerがパッチ実装する。

**非変更：** main、正式RC、Codex/Studio、merge、公開、課金、5 Automation、P0-A/B/C CAS。
