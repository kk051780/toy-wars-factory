# TWF-0002 — Actions標準トークンではワークフローを保存できなかった

発見日: 2026-10-24

- 失敗の実測: https://github.com/kk051780/toy-wars-factory/actions/runs/40048456526
- コンパイル: `gh aw compile` は成功。生成された `.github/workflows/twf-autonomous-developer.lock.yml` は存在した。
- Git push: `GITHUB_TOKEN` にGitHub Appの `workflows` 権限がないため、ワークフローファイルのpushが拒否された。
- 原因の分類: **権限分離**。コンパイル失敗ではない。秘密情報不足やCopilot認証未完了とも別。
- 修正: コンパイル専用workflowにはcontents:writeをこれ以上付与せず、生成物をprivate Actions artifactとして保持。ChatGPTのGitHubコネクタの既存限定権限で内容を監査後に別途コミットする。
- 再発防止: CIでworkflow配置権限を勝手にエスカレートしない。コンパイル→別経路で保存→レビュー→認証→本稼働の品質ゲートを固定。
- 完了条件: 対応ブランチに再生成されたlockを保存し、md/lockのハッシュが一致することを検証。認証・AI実行は別ゲート。
- 誤報禁止: ロックが生成されたという事実を『AIがコードを書いている』と報告しない。
