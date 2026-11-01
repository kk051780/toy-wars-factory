# TOY WARS / A14 — Open Cloud 固定スモークの戻り値検証ゲート（候補 v4）

## 課題と今回の差分
既存の「88テスト」Open Cloud 静的スクリプト候補の `inspect_untrusted_task()` は、返却文字列内のマーカーや構造名が「含まれるか」のみを報告する。これを実機成功判定に使うと、単なるエラーメッセージや偽の文字列も成功に見えてしまう。

このパッケージは**独立した読み取り専用の追加ゲート** `tools/twf_static_smoke_return_gate.py` と**41個の独自回帰テスト**を提供する。ゲームソースには変更を加えず、固定スクリプト `twf_open_cloud_smoke.luau` は原本SHAを維持する。計画器 `open_cloud_engine_preflight.py` のHTTP本文だけは30秒制限を含めるよう改修した。既存の動的nonceスクリプトのSHAガードは緩めない。

## 成功扱いを拒否する例
- 結果にマーカーの文字列だけが含まれる／文字列リストだけが返る
- タスク状態が `FAILED` / `PROCESSING` / 出力なし / エラーあり
- 元の非公開 Saved-version ID とタスクパスが一致しない
- 戻り値の追加・欠落・重複・型の違い、wave 5/20 の不一致
- `mobile_verified=true` や `publish_authorized=true` の過大申告
- 偽のスクリプトSHA、偽のHTTP本文SHA、別のソース主ブランチSHA
- JSON の重複キー・`NaN`

## 追加の実行時間ガード（v2、2026-11-01）
Roblox Open Cloud Luau Execution API は `timeout` を 1〜300 秒で指定できる。初回の構造検査では `30s` を固定し、**予定していない最大300秒のスクリプト実行を防ぐ**。ただしこれはサーバー起動・HTTP通信を含むエンドツーエンド時間の上限ではなく、クォータや課金の保証でもない。

- `open_cloud_engine_preflight.py`: `TASK_TIMEOUT='30s'` を固定し、POST JSON を `{"script":"...","timeout":"30s"}` としたハッシュへ更新する。依然としてHTTPリクエスト自体は**送信しない**。
- `twf_static_smoke_return_gate.py`: `timeout` の欠落・別の値・型の違い・旧スクリプト単独本文SHAを拒否。実際のプロバイダ認証・タスク起動の許可は**与えない**。
- `tests/test_twf_static_smoke_return_gate.py`: 既存34件に7件を追加。修正前 GitHub Actions #41264707661 は **874件中6件の想定失敗**、修正後 #41264805775 は **874/874成功**。この検証はすべてオフライン。
- 固定LuauスクリプトのSHA256 `fc343ede29c2466b0962689b183b5320d81122a807d65ad7f82e942a9268759d` は不変。将来の接続器も実際のPOST JSON本文のSHAを照合すること。

## Open Cloud公式タスクGETとログを結ぶ追加アダプター（候補 v3、2026-11-01）
`tools/twf_open_cloud_get_log_adapter.py` は、バージョン指定された `GET /cloud/v2/.../tasks/{task_id}` と `GET /cloud/v2/.../tasks/{task_id}/logs` のレスポンスを**ローカル入力**として読み、固定Luauコードのエコー・30秒制限・タスクID・ログページ・結果テーブルの整合性を照合する。

- `tests/test_twf_open_cloud_get_log_adapter.py`：23件のオフライン回帰を追加。未実装時 [GitHub Actions #41265279491](https://github.com/kk051780/toy-wars-factory/actions/runs/41265279491) は、モジュール未存在で **875件中エラー1件**。実装後 [#41265346280](https://github.com/kk051780/toy-wars-factory/actions/runs/41265346280) **897件全合格**。新規23件全合格。
- 偽のスクリプトエコー、別バージョンのタスク、別タスクのログ、ページング未完、巨大ログ・JSON重複キーを拒否。ログ本文は戻り値にも履歴にも含めない。
- これは**公式APIレスポンスと同じ形式の入力を比較するだけ**であり、信頼できる取得元、正当な秘密情報、元のPOSTからのACK、Saved実バージョンと出力のプロバイダ真正性を認証できない。エンジンPASSの根拠には決して使用しない。
- 今後の接続器は、Roblox公式APIキーを受け取る保護されたホスト上でPOST 1回→GET→ログ取得を行い、実際のHTTP応答元、レスポンスとPOST原本、Global CASと秘密鍵の範囲を独立検証する必要がある。ホストの実装・鍵・実アクセスはこの候補には含めない。

公式の返却形式参考：[Roblox Luau Execution API](https://create.roblox.com/docs/cloud/reference/features/luau-execution)、[Robloxによる構造化ログの紹介](https://devforum.roblox.com/t/beta-open-cloud-engine-api-for-executing-luau/3172185/74)。

## 作成時POST応答と完了GET/ログの同一タスク照合（候補 v4、2026-11-01）
Roblox公式の [DemoSDK.luau](https://github.com/Roblox/open-cloud-execution-binary-payloads-example/blob/main/DemoSDK.luau) は、タスク作成応答から得た `path` を使って、後続のGETとログ取得を行う。従来のJSON整合チェックはこの**作成応答とGETの同一性**を比較していなかった。

- 新規 `inspect_untrusted_create_get_and_logs(plan, create_json, get_json, logs_json)` は、タスク作成応答と完了タスクGETの**フルパス完全一致**を必須とする。バージョン/タスクIDの食い違い、作成応答の失敗状態、スクリプト変更、30秒制限の不一致を拒否する。
- 新規17件の回帰検査を、既存 `tests/test_twf_open_cloud_get_log_adapter.py` に追加。GitHub実RED `11c71ed67e70006c9cda7990b1bd8ce70b7fa23f` / [Actions #41266078138](https://github.com/kk051780/toy-wars-factory/actions/runs/41266078138) は **914件中想定エラー17件**、修正後 `04a83070300a0d5318389f8422ecaef6fa81168e` / [Actions #41266148985](https://github.com/kk051780/toy-wars-factory/actions/runs/41266148985) は **914/914全成功**。41件の静的戻り値テストと40件のGET/ログ・作成ACKチェックは通過。
- 重要：**作成応答そのものは未認証の呼び出し元JSON**で、これを実機証拠と見なさない。返却値は `create_response_path_matches_get=True` だが、`create_ack_authenticated=False`、`provider_authenticated=False`、`engine_verified=False`。実際のホストは、認証済みHTTPS応答・当初のPOST本文・非公開保存版・CAS履歴を別個に証明する必要がある。

## 実行
Python 3.10+。追加パッケージ不要。

```sh
python -m unittest discover -s tests -p 'test_*.py' -v
```

## 判定の限界
これは**Robloxの公式GETを直接パースする実装ではなく、将来信頼済みホストが整形するタスク値の型安全検証**。公式の戻り値表現に合わせた変換器は別途ホスト側で検証すること。成功しても `STATIC_SMOKE_RETURN_CONSISTENT_UNTRUSTED` とし、APIプロバイダ署名・原本リクエスト・GETログ・保存済みプレイスの真正性を証明したものとはみなさない。エンジン、Playモード、スマホ、多人数、公開のいずれも合格扱いにしない。

既存A14 #3 / #151 に関連する追加候補であり、重複実装を防ぐため既存の静的スモーク候補と独立審査後に取り込むこと。コードのオーサーによる自己レビュー禁止。GitHubには保護ドラフトPRのレビュー用ソースと検証を記録したが、main・公開設定・秘密情報・Robloxサービスには書込みも呼出しもしていない。

## 原典
- Roblox official Luau Execution API: https://create.roblox.com/docs/cloud/reference/features/luau-execution
- Roblox sample (archived, not production hardened): https://github.com/Roblox/place-ci-cd-demo
- GitHub issue: https://github.com/kk051780/toy-wars-factory/issues/151
