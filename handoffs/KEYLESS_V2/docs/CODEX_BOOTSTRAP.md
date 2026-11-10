# Windows Codex 最初の1回だけ（PRIVATE repoを作らない場合）

1. OWNERの直接指示に基づき、GitHub固定コミットから `tools/keyless_handoff_v2.py` を取得する。
2. PCのPython（cryptographyインストールが必要）から以下を実行。実行前に既存の identity の有無を確認。

   `py keyless_handoff_v2.py enroll --public-out recipient-public.json`

3. **公開情報** `recipient-public.json`（format, recipient_public_key_b64, recipient_key_id）だけを #217 に報告する。PRIVATE JSONがある Windows user profile pathは内容を表示しない。
4. 以後は各ChatGPTチャットが recipient へ暗号封入するので、OWNERは個々のAES鍵を貼らなくてよい。Codex は同じ tool の `restore` を使うだけ。
5. Windows再インストール時はidentityを失うと旧v2パックは復元不能。秘密identityはWindows専用の安全な場所へバックアップするが、GitHub・ChatGPT・Issueへ貼らない。

**PRIVATE repoを用意できる場合**: このセットアップは不要。private repoへの通常ZIP・SHA納品に切り替える。

現行リポジトリはPUBLIC。秘密のゲームZIPはGitHubに平文掲載不可。
