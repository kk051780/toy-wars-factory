# TOY WARS Factory — 無人AI開発エージェント承認ゲート

現状：git branch setup/agentic-runtime-probe 上に、20分ごとの実行設定を持つソースと実際のコンパイル済み .lock.yml を配置。main 未配置なので無人AI開発はまだ未稼働。

## 技術
- GitHub Agentic Workflows / Copilot engine for personal private repository.
- ソース: .github/workflows/twf-autonomous-developer.md
- 生成lock: .github/workflows/twf-autonomous-developer.lock.yml
- 改善対象を src/tests/studio/evidence/docs/EXPERIMENT_LOG.md に限定し、AGENTS/品質基準/Workflowを変更させない。
- 自動マージ、Roblox公開、課金開始は禁止。

## 費用と時間
- 技術的ガード: max-ai-credits 25 / 回、max-daily-ai-credits 100 / 24時間、max-turns 20、timeout-minutes 16。
- これは支払上限ではない。AI Credits以外にGitHub Actionsランナー費用・モデル側課金が発生し得る。
- 20分間隔は最大72回/日。予算の承認と稼働実績を得るまでmainへマージしない。
- owner承認があれば低頻度のテスト運転→段階的に定期稼働に移行する。

## 個人GitHubアカウントの認証
組織ではないためGITHUB_TOKENのcopilot-requests権限は利用しない。
GitHub公式のfine-grained personal access token (PAT)を作成し、Account permissions > Copilot Requests: Readを付与。
トークン値はGitHub repository secret COPILOT_GITHUB_TOKENとしてGitHubの秘密情報管理画面へ保存する。**トークンをChatGPTチャット、IssueやPR、ファイルに貼らないこと。**
Copilotが有効な契約/プランと課金設定、GitHub Actionsの上限を確認する。
GitHubコネクタに秘密情報を読む/変更する権限はないので本人だけがスマホブラウザで承認する。

## 稼働判定
(1) PRの静的品質ゲートPASS、(2) owner's budget/credential approval、(3) 同意を得たmain activation、(4) GitHub ActionsでAI inference成功、(5) AIが実際のゲーム差分・テスト付きPRを生成、(6) そのPRで独立QA合格。
1–3段階だけなら「エージェント稼働」と言わない。

## 運用停止
GitHub ActionsからAIジョブを無効化・credential失効・課金制限を実施可能にする。設定変更はオーナー承認制。
