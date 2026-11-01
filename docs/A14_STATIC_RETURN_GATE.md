# TOY WARS / A14 — Open Cloud 固定スモークの戻り値検証ゲート（候補 v2）

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
