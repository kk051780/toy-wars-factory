# TOY WARS / A14 — Open Cloud 固定スモークの戻り値検証ゲート（候補 v1）

## 課題と今回の差分
既存の「88テスト」Open Cloud 静的スクリプト候補の `inspect_untrusted_task()` は、返却文字列内のマーカーや構造名が「含まれるか」のみを報告する。これを実機成功判定に使うと、単なるエラーメッセージや偽の文字列も成功に見えてしまう。

このパッケージは**独立した読み取り専用の追加ゲート** `tools/twf_static_smoke_return_gate.py` と**34個の独自回帰テスト**を提供する。既存ソースの改変はなく、元の固定スクリプト `twf_open_cloud_smoke.luau` と `open_cloud_engine_preflight.py` を**原本のまま同梱**する。既存の動的nonceスクリプトのSHAガードは緩めない。

## 成功扱いを拒否する例
- 結果にマーカーの文字列だけが含まれる／文字列リストだけが返る
- タスク状態が `FAILED` / `PROCESSING` / 出力なし / エラーあり
- 元の非公開 Saved-version ID とタスクパスが一致しない
- 戻り値の追加・欠落・重複・型の違い、wave 5/20 の不一致
- `mobile_verified=true` や `publish_authorized=true` の過大申告
- 偽のスクリプトSHA、偽のHTTP本文SHA、別のソース主ブランチSHA
- JSON の重複キー・`NaN`

## 実行
Python 3.10+。追加パッケージ不要。

```sh
python -m unittest discover -s tests -p 'test_*.py' -v
```

## 判定の限界
これは**Robloxの公式GETを直接パースする実装ではなく、将来信頼済みホストが整形するタスク値の型安全検証**。公式の戻り値表現に合わせた変換器は別途ホスト側で検証すること。成功しても `STATIC_SMOKE_RETURN_CONSISTENT_UNTRUSTED` とし、APIプロバイダ署名・原本リクエスト・GETログ・保存済みプレイスの真正性を証明したものとはみなさない。エンジン、Playモード、スマホ、多人数、公開のいずれも合格扱いにしない。

既存A14 #3 / #151 に関連する追加候補であり、重複実装を防ぐため既存の静的スモーク候補と独立審査後に取り込むこと。コードのオーサーによる自己レビュー禁止。GitHub本体・ロック・権限・Robloxサービスには今回書込みも呼出しもしていない。

## 原典
- Roblox official Luau Execution API: https://create.roblox.com/docs/cloud/reference/features/luau-execution
- Roblox sample (archived, not production hardened): https://github.com/Roblox/place-ci-cd-demo
- GitHub issue: https://github.com/kk051780/toy-wars-factory/issues/151
