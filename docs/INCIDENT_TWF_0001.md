# TWF-0001 — 開発エージェント状態の誤判定

発見日: 2026-10-24
証拠: https://github.com/kk051780/toy-wars-factory/actions/runs/40047505929

現象: AIエージェント未稼働という正しい状態なのに、古い品質ゲートが FAIL と報告。

原因: 自動開発状態名を NOT_ACTIVE から NOT_ACTIVE_AI_INFERENCE_UNVERIFIED に詳細化したが、検査側だけ NOT_ACTIVE と完全一致していた。

修正: tools/verify_status.py に未稼働状態の許容集合、稼働状態 ACTIVE_VERIFIED の追加証拠要件、不正な状態の拒否を実装し、tools/repository_gate.py から呼び出す。

再発防止: tests/test_verify_status.py で未稼働2種・ブロック状態、虚偽の稼働、認証されていないURL、別リポジトリ、未知状態を検査。CIの合格確認まで完了とは宣言しない。

ゲームのRoblox実機合格やAI自律推論稼働を示すものではない。
