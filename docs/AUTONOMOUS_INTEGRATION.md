# 助手へ委譲された承認と独立統合

2026-10-25、所有者は「承認については君に全権を与える」と明示した。
通常のゲーム開発・体制改善・main取り込みに所有者の返信を要求しない。
この指示は、過去のcheckpointに残る都度の所有者承認条件より新しい。
客観的な品質条件、実証の区別、既存の費用上限や事故停止は免除されていない。

## 役割と通常の流れ

| 役割 | 行うこと | 行わないこと |
| --- | --- | --- |
| WORKER | 完成ロードマップに沿う小さなゲーム実装、再現検査、draft PR、失敗修復 | 自分のPRの承認・main直接統合 |
| META | 最新WEB一次資料と失敗/効果を照合し、小さな体制改善と検査をdraft PRへ | 自分のPRの承認、保護条件の緩和 |
| REVIEWER | 別タスク/実行文脈で実差分・現在headのCI・証拠を読み、順番に統合 | 実装コードの変更、作者と同じrunでの自己承認 |
| CONTROLLER | 手動goの合流、明示された保守/移行、委譲範囲の判断 | 稼働中の作業を追い越す並行書込み |

3役と手動操作は同じGit共有ロックを使う。審査役は登録task_id、正規run UUID、
work_branch=main、現在のepoch/期限を持つREVIEWER leaseを取得する。
同じChatGPTサービス上の別タスク/実行による分離であり、別プロバイダや別GitHubユーザーの審査とは呼ばない。

審査判定は`tools/repair_integration.py`。入力は実際のGitHub/サービス観測値から作る。
古いheadのCI、古いmainに対する審査、作者本人の審査、失効した所有権は統合を許可しない。
mainのQA後に生成statusの2ファイルだけが更新された場合は、実compareで確認したときに限りQAを再利用できる。
ソース・設定・検査などが動いていれば、そのmainに対する検査を待つ。

1件ずつready化・expected_head_sha付きmergeを行い、その実mergeとmain QA/引き継ぎを確認してから次へ。
1回は最大3件、30分の所有権内で小さく処理する。CI未判定なら次回へ渡し、タスクを止めない。
失敗mainは最優先で修復要求を出し、他機能の統合を保留する。失敗を成功と記録しない。

## 具体的な記録と修復

共有branchに`ops/reviews/`、`ops/INTEGRATION_LATEST.json`、`ops/WORK_REQUESTS.json`を置く。
対象head、作者/審査役のtask/run、見たmain、合否の理由、検査、merge/main QA、次の担当を残す。
審査待ちは「自動審査・統合待ち」と表示し、所有者用の承認返信文は生成しない。
不備は再現・ファイル・期待値付きで作者へ渡し、次の機能より先に直す。

新モジュールが必要ならMETAがinstaller対応と新しい回帰検査を付けて
`additional_source_paths`の追記だけを提案できる。既存の許可を削らず、他の権限/費用/品質条件は変えない。
独立審査・統合後にWORKERがその明示されたモジュールを実装する。未対応のファイルを黙って配布対象から落とさない。

## 導入時の読取り専用審査

v4自体の導入PRは、共有stateの`bootstrap_review_request`で正確なPR/headと審査taskを指定する。
保存された審査プロンプトが許可するのは読み取りと結果の返却だけ。ロック/コード/PR/mainを変更しない。
CONTROLLERが別文脈の実際のサービス結果、対象head、CIを照合して移行を完了する。
これは通常のv4審査・統合ループが実走した証拠とは分ける。

## 完成と公開の判断

完成への課題は`docs/COMPLETION_ROADMAP.md`を基に、実測と最新情報で更新する。
所有者待ちは通常工程から外すが、実機・複数人・スマホ・外観・プレイヤー体験の証拠がなければ完成/公開可としない。
現在のRoblox公開HOLDは実証不足によるもの。日常の取り込み承認待ちとは区別する。
Gemini事故停止、消費済み試行、認証・費用上限をこの委譲から勝手に解除しない。


## 手動CONTROLLER作成PRの独立審査（Issue #59、導入後のみ）

手動Workが作成した `feature/twf-` は、**ブランチ名だけでは統合しない**。
共有コーディネータ `manual_review_requests` にPR番号・完全head SHA・正確な
base-main SHA・ブランチ・元のCONTROLLER owner UUID/epoch・その取得コミットSHA・
登録REVIEWER task IDを**一意に**記録する（作者のPR本文を証拠にしない）。
登録REVIEWERは独立したrunと有効な自分のロックを持つこと。

審査役はGitHubの不変claimコミットを取得し、取得時のholderがCONTROLLERで
owner/epoch/work_branch/base-main/有効期間が一致することを確認する。
現在のPR headとmainが申請と一致すること、main QA、両必須PR CI、
実Git差分の全パスと状態、履歴の全ソースサイズを再取得して確認する。
`changed_entries`は実Git差分の`status,path`を使い、
`check_auto_diff.violations`により許可されたゲームソース+新テスト+履歴以外を拒否する。

その根拠をREVIEWERの当該runの審査レコード`manual_provenance`に記録する。
`ci.scope_and_claim_gate=MANUAL_CONTROLLER_ATTESTED`は、この**審査役の実証**
があって初めて付与するラベルでありPR作者・CIの自己宣言を信用しない。
評価関数は明示的な依頼・実差分・全証拠と既存の独立性、現main/正確head、
レビュー時刻、main QA、リリースHOLDを同時に要求する。
途中でhead/mainが動いたら審査をやり直す。作者が審査・統合を代行しない。

実際のGitHub照合なしに`*_verified: true`と設定してはいけない。
この方式は許可されたゲームPRの一経路だけ。GitHub Actionsの認証/課金/Roblox公開の
権限を広げるものではない。ポリシー変更PR自身が独立レビュー・CIを経て
mainに採用されるまでは、手動PR #58の自動統合は解禁されない。

### 監査指摘 #60 の解消（証拠の正本）

手動ゲームPRの変更範囲は、実ゲームsourceのM・新規Lua回帰のA・C履歴のAの**3種すべて必須**。docs/EXPERIMENT_LOG.md、権限設定、CI、文書だけ、重複パス、削除は拒否。

単一PR番号に紐づくレビュー依頼は**ブランチにかかわらず1件のみ**。独立REVIEWERがGitHubからfetchしたimmutable claimコミットのファイル原文・blob SHA・commit SHA、第一コミットSHA/親/時刻、PR開始時刻、QA workflow IDと2 job ID/合格結果、比較したbase/headと差分を束ねる。判定関数はraw claimのGit blob SHA-1、厳格JSON（重複キー禁止）、取得時刻≦第一コミット時刻＜期限、および各種SHA・IDを相互照合する。**Git SHA-1単体や自己申告のTrue値はプロバイダ証明ではない**。REVIEWERはGitHubの認証済みコネクタから取得し、真正なAPI結果に基づく証拠だけを入力すること。純粋判定関数自体はGitHub API接続を持たず、独立したGitHub fetchを置換しない。これらが用意できない実行は保留する。
