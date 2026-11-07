# P0: GPTチャット上限・停止時の引き継ぎ（保護された候補）

対象：TOY WARS FACTORY Issue #123、並列化PR #173→#174→#200→#201→本PR。

## 目的
GPTチャットが満杯で応答できなくなっても、他のGPTチャットが現在の作業・PR・CI・次の行動をGitHubから復元できるようにする。ただし、チャット終了を本物のサービス終了証拠と取り違えず、重複書込みや他者ロックの横取りを防ぐ。

## 1. チャット停止前に保存する
重要な小作業を終えるごとに、次の情報をGitHubの既存Issue/PRのコメントまたはレビュー済み作業台帳へ永続保存する：
- canonical work_id、project_id、repository、担当owner/run/task、lease epoch、GitHub coordinator ref SHA
- main HEAD、作業ブランチ、現行source HEAD、PR番号、現在のCI run、変更したファイル
- 作業ステージ、次の一手、checkpoint_sequence、作成時刻、SHA256 digest
- 正規の同一holder解放結果・そのGitHub ref再読を、取れたときだけ別途記録

draft_checkpoint は保存用のチェックポイント候補を作る純粋関数に過ぎない。GitHubへ自動書込みはしない。digest は改ざん/破損を検出する参考であり、提供者本人認証や真正GitHub証明ではない。APIキー・トークン・秘密情報をコメントへ書かない。

## 2. チャットが満杯になり別チャットで再開
新しいチャットで「TOY WARS再開」と指示。別チャットは記憶を正本扱いせず、毎回以下の順で確認：
1. GitHub Issues #123/#182・AGENTS.md・現main・共有coordinator ref/state・Work Requestsを原本から独立GETする
2. 元PR・branch・Actions・保存済みcheckpointのhead/branch/ref/owner/epoch/sequenceを突合し、同じ作業IDならJOINし重複PRを作らない
3. 本人のロックがまだ有効なら、後続チャットはread-onlyで合流。元owner_id/run_idを勝手に引き継がない
4. 元の正規解放が独立GitHub原本で検証されたら、必ず新しい独立owner/epochをCAS取得し、最新の差分/CIを確認してから続行する

## 3. チャットが停止してロックが残った場合
- チャットの無応答、context上限、「つぎ」、期限切れ、別チャットの自己申告は、元チャットが終了した証拠ではない
- 登録されたWORKER/META/REVIEWERの場合は元のtask IDとrun IDに一致する本物のサービス完了イベント・時刻を接続元から取得し、既存recover_finished_workerのような正式手続で回収を検討する。古いlatest_result・チャットに貼られたUUID・見かけのcompletedを使わない
- 手動CONTROLLERのチャットは接続元の確かなterminalイベントがない場合がある。元holderとepochを明示したOWNERによる一回限りの非常時解放承認、現行ref+状態の再検証、非強制expected_sha CAS、再読が必要。別holderや新epochには絶対に触らない。一般的な「進めて」は非常時解放の個別承認ではない
- まだ証拠がなければWAITとして報告し、新機能は他の読み取り専用検査・別件計画に限る。単に期限が切れただけで自動解除しない

## 4. 永続性の限界と今後の実装
- PRの元コードとGitHubに永続保存されたIssueコメントは、チャット履歴が閉じても再取得できる
- 現PRのソースは他ownerとの衝突を避けるため、チェックポイント時点と実HEADの一致を毎回再検証
- システムがチャット残量を正確に測定しているわけではない。作業単位の短縮・頻繁なcheckpoint・正常なCAS解放でリスクを減らす
- 本PRでは純粋なcheckpoint作成・後続チャットのread-only preflightのみを実装。自動永続アップロード、サービス終了の真正確認、live parallel leases、無人書込みの本番稼働は未実証
- Issue #57のGitHub無人writer権限障害、独立REVIEWER、protected/main CI、無料枠、Gemini停止、Roblox非公開を維持
