# GQ8 — 8領域「実際の正式RC Place」照合ゲート

2026-11-16 / Owner「原作者ACK待ち不要、Chat引継ぎ先がRCまで責任継続」運用。

この検証はゲーム機能をもう一度実装せず、既存の正式RCワークフローが生成した `EGGRUMBLE_V3_RC31_CANONICAL_STUDIO.rbxlx` の **Roblox XML 内の31個の本物の Script Source** と、同一HEADのActions receipt、`rc_fastlane/EGGRUMBLE_V3_ACTIVE.json`、旧S1 `ACTIVE.json` を独立突合する。原作者ソースと他班の Host/Combat/Swarm/Bot/Item/ART/Score/Lobby 変更はゼロ。

対象8領域：キャラ7職、フィールドのAI遮蔽、戦闘の死者ガード、城/卵表示、雑兵の本物の攻撃と共有予算、アイテム取得、TEAM/BR入口、スコア/結果。現在判明した17個の公式ONフラグに実コードのアンカーを対応付ける。#551旧アバターの卵誤落下、正式RC採用済み#538結果表示の再送、#523フィールド卵の城土台回避、#517満HP時の回復薬空消費防止も実成果物から確認する。別の新規フラグは `unassessed_new_flags` に列挙し、既検証と偽装しない。

RED：SHAが違うPlace、現在と異なるRC HEAD、欠けたSource、31本より少ない/重複したScript、異なるScript class、記載だけONで実コードにない修正、既存S1が無承認で切り替わる、Publish済みを示すreceipt。

既存正式ワークフローの **Rojoビルド後・Actions成果物アップロード前** に実行するので、`GITHUB_SHA` はその成果物と同一。プレビューPRはそのPRの検証であり正式RCではない。正式RCへのマージ後はRCブランチ push Actionsを再確認する。

**限界:** Luau構文/Sourceアンカーとビルドの真実性検査であり、Roblox Studio実行・2クライアント・低性能Android15分・絵の品質・FUN・OWNER受入・Roblox公開ではない。合格をゲーム完成100%と呼ばない。

ソース: `verify_artifact.py`。変異/誤証拠を拒否するテスト: `test_artifact.py`。切戻しは本ワークフローのGQ8 stepだけ外す（既存31ソースのどれも変更不要）。

並行Chat用：正式RC HEAD→最新他Chat PRとCLAIM差分→GQ8 same-head CI→実Place byte/SHA→8領域証拠の順で追跡。新規ゲームコードの作者重複はしない。
