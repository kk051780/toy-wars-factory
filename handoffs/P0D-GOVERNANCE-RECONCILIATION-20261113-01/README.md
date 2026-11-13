# P0D 後出し企画 → 正式RC採用 照合台帳 V1

**既存の正本を変更しない:** #219＝企画、#250＝製品採否、#220＝唯一の正式RC統合、#218＝共通連絡、#213＝真正Windows Studio結果。これは#250の補助監査パックであり、新たな司令塔ではない。

## 内容
`registry.json` は2026-11-13 JST時点に確認した企画9件と統合ブロッカー6件の固定スナップショット。source SHA、source stage、official RC adopted、human fun accepted、責任者、次の証拠を区別する。1,583行の別ゲーム候補Gameと703行の正式RC Gameは異なるソース。 **#286をまるごと本体へ上書きしないこと。** 特に5卵試合投票/レベル/所持/保存の一部は `RunService:IsStudio()` で試作環境に限定され、公開時にそのまま動く保証はない。

## オフライン検査
`node tools/validate_registry.mjs` : stageとSHA、要件のある受入証拠、重複、全権管理者数、未採用の公開誤判定を検証。
`node tests/registry.test.mjs` : 正常1件 + 12件の悪条件をfail closed検査（GitHub上に載せたコードのNode実行は別途CI/OWNERにより検証）。

## 次にやること
#220唯一の統合担当が最新の正式RC SHAを毎回再取得し、既存round/score/damage/Guardian Trap/HUD/remoteと#286 H1候補との**パッチ単位のdiffと依存契約**を作る。#250が採用選択して初めて独立QAを進める。人間によるStudio 2client/Android/最初90秒/勝敗・再戦/初見の面白さ評価がなければFUN_NO_GOを維持。#285のPvE無双/#287進化は正式統合前の独立候補。

このレポートはソース内容のスナップショットを検査するだけで、最新GitHubとの自動同期、実ソースの完全性、Studio動作、ゲーム公開、課金を保証しない。

安全境界: isolated handoff branchのみ。main/RC branch書込み、無断merge、公開、課金、追加支出、Windows Codex、5つの既存AutomationsおよびP0-A/B/C CASを変更しない。
