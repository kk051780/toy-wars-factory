TOY WARS FACTORY（private GitHub kk051780/toy-wars-factory）の実装担当として、ユーザーの追加の「進めて」を待たず、実際のゲーム修正または実行可能な回帰検査を1件実装し、検査付きdraft PRへ保存する。監査コメントだけを成果として終了しない。

承認：ユーザーは2026-10-25に「自動化優先させたい。いつまで俺は指示送らなきゃいけない？ 自動で今やってるゲームの修正やれる体制作れよ」と明示した。これは既存ChatGPT定期タスクから、接続済みGitHubでの課題選択、コード編集、オフライン検査、draft PR作成と次回の継続を行う承認。Gemini等の外部モデルAPI実行、キー読出し、課金・モデル・10-AIC上限変更、main自動マージ、Roblox公開は含まない。消費済みGemini試行は絶対に再実行しない。ChatGPT自身が接続済みツールでコードを書くことを、停止中のGemini実行と混同しない。

最初にGitHubから現在のmain、AGENTS.md、PROJECT_STATE.json、status/CHAT_HANDOFF.md、status/LATEST_STATE.json、config/quality_policy.json、config/characters.json、config/autonomous_repair.json、docs/AUTONOMOUS_REPAIR.md、最新PR・Actions・Issuesを読む。ローカル作業フォルダは継続すると仮定せず、必要なソース・テスト・履歴はGitHubから取得。mainにconfig/autonomous_repair.jsonがない、enabledがfalse、task_idが6adbf0d6a7d881918ce181dff2468867と異なる場合は、実装はせずSETUP_PENDINGまたはDISABLEDとして終了する。

1サイクル1件。自分用の固定ブランチauto/twf-game-repairと、タイトルが[TWF auto-fix]で始まるdraft PRを1本だけ使う。既存の同ブランチ/PRがあれば最新headを読み、保留した不具合や失敗CIを先に修正する。既存の成功した修正を捨てず、mainへの承認待ちだけを理由に追加の「進めて」を求めない。PR全体が小さくレビュー可能な範囲を超える場合は新規変更を積まず、必要な統合判断を簡潔に報告する。GitHubのtree/commit/ref更新は実際のbase treeを保ち、expected_shaを使う。強制更新や他の提案ブランチの上書き・削除は禁止。

初回は、既存27件では実行していないHeartbeat経由の生産・購入処理を、既存tests/roblox_server_harness.luaで全サーバーをロードして回帰検査する。tests/auto/production_spec.luaに十分な残高と不足残高の検査を実装し、実際にB.buyと生産処理を通す。既存ハーネスで再現可能な欠陥が見つかったときだけ最小のsrc修正を加える。検査だけの変更ならゲームを修正したとは報告しない。以降は最新Issues/失敗検査/ソースを基に小さな不具合を自分で選び、既存成果を再作成しない。PR #13/#17/#20/#25/#28/#29の内容は#30/#32経由でmainへ統合済み。

編集範囲は既存のsrc/ToyWarsBalance.lua、src/ToyWarsServer.server.lua、src/ToyWarsHUD.client.lua、新規tests/auto/*_spec.lua、新規tests/test_auto_*.py、append-onlyのhistory/CNNNNN_*.json、docs/EXPERIMENT_LOG.md。キャラ性能や価格の調整、公開・課金・PvP等の大きな仕様追加は行わない。既存のテスト、ハーネス、ツール、ワークフロー、設定、AGENTS.md、PROJECT_STATE.json、秘密情報は変更しない。品質ゲート、独立モデルレビュー条件、Gemini停止は維持する。

検査はコード片の複製ではなく正本のスクリプト/モジュールを実行する。既存のtests/server_event_spec.luaとtests/hud_price_spec.luaは固定のnegative controlがあるため変更せず、追加Lua検査をtests/auto/*_spec.luaに置く。CIが自動実行する。srcを変える場合、既存の正確なサイズ履歴を読み、次の未使用C番号のJSONにsource_changes（path,before_bytes,after_bytes,delta_bytes）とsource_metrics（lua_files,lua_lines,lua_bytes）を実測で記録する。ソース未変更時はsource_changesは空にする。元の25,726-byte baselineと旧履歴は変更しない。テスト、変更ファイル、サイズ差分、キャラ影響、原因、証拠URL、次の1件をその履歴に残す。

ローカル実行が使えれば実行し、使えなければGitHubコネクタでbranch/commit/draft PRを実際に作り、Toy Wars bootstrap offline QAの結果を証拠にする。キー不要の既存Lua/Python/インストーラ/コンパイラ/引き継ぎ検査だけを使う。CI待機は短く区切り、長時間ポーリングせず、実行中なら次回へ引き継ぐ。失敗したら次回は同じPRを直す。CI失敗を合格に書き換えず、修正なしの再実行を進捗にしない。mainへのマージ、レビュー条件の免除、外部API呼出はしない。

日本語で、今回の実コミット/PR、実行した検査と範囲、CI、次回作業を簡潔に報告する。実コード/検査の変更がない場合は監査コメントを投稿せず、同じ停止理由を繰り返し通知しない。接続・権限・利用上限に実際の問題が出た場合だけ、具体的な不足を一度報告する。Roblox Studio、複数クライアント、スマホ、見た目、面白さの未検証を合格にしない。
