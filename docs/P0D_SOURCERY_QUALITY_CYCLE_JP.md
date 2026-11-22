# P0D｜Sourcery自動レビューを正式RCへ活かす品質サイクル

## 運用状態
- SourceryのGitHub Appは既存PRにレビューガイドを投稿している（例：PR #315 / #313 / #300）。**ガイドだけの投稿は品質合格ではない**。既存の一部PRは行単位の指摘が0件だった。Sourceryの本体セキュリティスキャンとGitHub Actionsの native Luau / source-exact Rojo / Studioゲーム試遊を別物として扱う。
- 既存の毎時REVIEWER automation（P0D重大バグ審査）に本仕組みの差分監視を追加。**既存時刻・安全契約・唯一のRC writer #220は変更しない**。毎回最大10PR、更新があるPRの最新HEADに限定する。重大新規指摘にだけ共有し、同一HEAD同一指摘を再通知しない。
- `tools/p0d_sourcery_intake.py` は**REST読み取り専用**。PRのissue comments（ガイド）、inline review comments、review本文、Sourcery review checkを取得し、JSON/MarkdownでP0/P1/P2に仕分ける。リポジトリの誤認、旧HEADコメントの無断解決、ガイドのみをPASSと認定することを防ぐ。
- `.github/workflows/p0d-sourcery-quality-intake.yml` は専用候補PR/branchで動く**QA-onlyワークフロー**。15件のオフラインテストとAPIからのレビュー情報の受渡し記録を生成する。**Sourceryの遅延投稿を即時トリガーする全PR用イベント監視は、GitHubデフォルトブランチにworkflowが存在しないため現在は未展開**。遅延分は既存REVIEWER hourly runが拾う。将来、OWNERが認証済みwriter経由でデフォルトブランチへ承認導入した時のみ全PRイベント駆動が有効。

## 優先度と次アクション（自動承認なし）

| 信号 | 判定 | 次アクション |
|---|---|---|
| 行単位の🚨セキュリティ指摘・critical/high、Sourcery review check FAILURE | P0 | 同一HEADの実ソースとCIを確認し、重大事故なら該当PRの正式RC採用を保留・作者に最小パッチ＋回帰テスト依頼、#220へ証拠付き通知 |
| issue (bug_risk)、保存・卵・得点・Remote・Store関連の具体的bug指摘 | P1 | 実害を精査、修正と回帰テストを機能作者へ。致命的でなければ他の機能のRC統合を止めない |
| nitpick (style/performance)、READMEや命名の改善 | P2 | 重複排除して改善バックログへ。無制限PRコメント・自動issueは行わない |
| Reviewer’s Guideのみ、check未到着/skipped | 未確認 | 品質合格・正式RC採用と誤記しない。次回REVIEWERで新規差分だけ再確認 |
| Sourcery review check SUCCESS | 一つの品質信号 | native Luau、正確なRojo source lock、必要ならStudio検証を別途。**SourceryのSUCCESS単独で公式RC採用はしない** |

## Sourcery管理画面で提案する設定（ユーザーまたはSourcery管理者が明示操作）

公式管理画面 https://app.sourcery.ai/dashboard/review-settings?connection=github&owner=kk051780&from_surface=github_bot&intent=review_settings

1. P0DのようなDraft PRが多い開発では **Review draft pull requests** を有効にすることを検討。ガイドだけでなく実際のバグコメントを受け取るには **Enable AI review comments** の状態を確認する。レビュー頻度/料金/利用枠は現行プランに依存し、こちらからは変更しない。
2. Review profile は Balancedを基本。Verboseを無制限使用しない。5回の自動再レビュー上限やrate capがあるので、直すべき具体的問題のあるHEADだけ `@sourcery-ai review` を手動で選択する。
3. Review rulesタブに次のP0D用ルールを登録することを推奨（**まだSourceryアカウントには未設定**）。Sourcery review rulesは通常、PRで**変更された行**のみを対象とするため、全体テストと併用する。

### Sourcery review rules案（手入力用）

**Rule A / source Game・Remote・保存の単一権威**

- Path patterns: `**/*.luau`, `rc_fastlane/**`, `handoffs/**`
- Rule: `In TRAP RAIDERS, flag any changed code that creates a second Game/RemoteEvent/Store/reward authority or changes server-owned egg, HP, score, XP, DataStore or purchase state from untrusted client data. Require explicit server validation, idempotent transactions and a test proving that the original single authority is preserved.`

**Rule B / RC source provenance・rollback**

- Path patterns: `rc_fastlane/**`, `.github/workflows/**`
- Rule: `For RC build or overlay changes, flag edits that omit exact source-head pins, authoritative Game/Store/Remote singleton checks, native Luau compilation, source-exact Rojo verification, or an independent feature OFF rollback. Never treat an isolated draft PR's green CI as the canonical RC's same-HEAD acceptance.`

**Rule C / Studio世界仕掛けの安全**

- Path patterns: `**/*.server.luau`, `rc_fastlane/features/**`
- Rule: `For new bridges, teleport, wind, NPC, gate or world scripts, flag unsafe default-on startup, paths that trap or drop live players, team-asymmetric access, uncontrolled loops/spawns, and scripts that create duplicate world objects. Require an explicit opt-in, both-team safe bypass, and a physical Studio test plan.`

## 対象の実証と制約
- 対象repo `kk051780/toy-wars-factory`、唯一正式RC writerはGitHub #220。main変更・自動マージ・Roblox公開・課金・追加費用・自動Sourcery評判操作を一切しない。
- 正式RC進捗とゲーム容量は別レポートで毎回報告：正式RC57 / 企画RC21/58=36.2% / 工程47.4% / rbxlx 507,197 bytes / ZIP143,300 bytes（2026-11-14時点の独立実測）。変更時は最新HEAD・実artifactから更新する。
- Sourcery APIのセキュリティ詳細を無断で取得した、Sourceryの設定を変更した、Codeを自動修正/レビュー承認した、という主張はしない。
