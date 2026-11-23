# EGGRUMBLE｜全並列担当 NO-STALL・発見課題の終結責任 V1
制定：2026-11-23 JST
OWNER指示：「並列作業をやっていて、未開放があると作業が止まる。これをやめさせたい。並列作業している全てが見つけた課題を最後まで解決するようにルール化して、ほかチャットが分かるようにして」

## A. 適用対象・優先関係
適用：企画室、ゲーム品質、ART/MOBILE、キャラ、戦闘、城、フィールド、中立兵、アイテム、UI、ロビー、バランス、Codex親/子G1〜G4、WORKER/REVIEWER/INTEGRATOR、全後継Chat/既存自動化担当。

参照すべきOWNER正本：#1011、#839、#218、#219、#250、#470、#420、#220、#364、#910と正式RC AGENTS.mdおよび docs/EGGRUMBLE_AI_DEVELOPMENT_SYSTEM_V1.md。

**この規則は未解放の本番権限を解放しない。** 真正CLAIM/lease、独立レビュー、#220唯一RC writerの認証とfresh expected_SHA/force=false、Studio排他、main昇格・Roblox Publish・課金/支出の承認条件は維持する。

## B. NO-STALL 五原則
1. **発見者が追跡責任者**：課題を発見した担当は、同一FEATURE_ID/FB_IDの ISSUE_SHEPHERD として記録し、再現→原因→実修正または元PR再利用→ソース検査→独立レビュー→唯一RC採用→同RC SHA実機再検証→OWNER受入/根拠ある廃案まで見届ける。作者が保護操作を勝手に実行してよいという意味ではない。
2. **BLOCKEDはその操作だけ**：未開放、CLAIM待ち、writer待ち、Studio排他、CI失敗、相手の反応待ち、利用枠不足があっても、可能な読取・原因調査・隔離実装/テスト・不具合修理・既存PRの差分確認・rollback・受入パケット準備を続ける。「待って終了」だけを既定動作にしない。
3. **実物優先**：P0「職選択→敵卵→納入得点→城勝敗→本人再戦」、7職/AI/攻撃HP/無双/旗艦ART/Android/FUNを優先。監査・計画・仮想テストの数だけで完了宣言禁止。
4. **重複禁止**：着手前に現在の選択profileと正規Game/Combat/Host/Store/Remote/HUD/score/XP、既存PR/CLAIM/SourceLockを照合。同じ仕事なら元Issue/PRにJOINし、原作者の非重複範囲や独立QAを手伝う。並列化のために二重実装/新しい正式RCを作らない。
5. **権限迂回禁止**：認証やgrant、nonce、lease、独立review、CI、Studio/Android人間評価は捏造しない。他担当ファイルを無断上書き、force更新、同時Studio、mainの直接変更、未承認公開・課金・支出はしない。

## C. 各担当の標準手順
**1 READ FRESH**：正式RC branch rc/p0d-s1-kids-rc01 の最新Git SHA、AGENTS.md、#1011、本規約、ACTIVE_RUNTIME/PRIVATE_COMPANION、当該issueの最新コメント、現CLAIM/PR/CIを再GET。

**2 TRIAGE + OWNER**：根本原因・実際の再現と期待、影響した役職/分野、P0/P1/P2、FEATURE_ID/FB_ID、ISSUE_SHEPHERD、既存owner/PR/source pathsを記録。既存と重複なら合流。

**3 FIX ALLOWED WORK**：正当なスコープ内で現実のLuau/3D/テスト、Native/Rojo/source class/hash、負例、OFF rollbackを作成・修理。未認証なら読取・独立負例や許可された隔離範囲を進める。

**4 INDEPENDENT QA → ONE RC**：作者とは別のレビュー、真正CLAIM/認証、#220 writer/調整されたCodex親経由でfresh HEAD/非force CAS。正式同HEAD CI、Place/ZIP bytes、48旧項目と17群/source-lockの無損失を検証。PREP_READY=正式RC採用ではない。

**5 STUDIO & FUN**：採用した正式RCの固定SHAでSolo/2clientと必要なAndroid15分、ART、初見3分FUN、OWNER受入。失敗は同一IDで修理・再検証。未実測はNOT_TESTED。

**6 CLOSE**：OWNER_ACCEPTED、または証拠付きREJECT/DEFER/DUPLICATEだけが終結候補。HANDOFF_SENT、PR_CREATED、BLOCKED、CI候補緑は未解決のまま保つ。

## D. 未開放時の進め方
| 停止原因 | 禁止する操作 | 代わりに続ける許可済みの仕事 | 次の正規実行者 |
|---|---|---|---|
| CLAIM未付与/期限切れ/範囲外 | 保護ソース/他者branchへのwrite、grant創作 | 現行CLAIMと既存PRの照合、読取診断、非重複の純テスト・fixture・仕様/修正準備 | #218認証担当/元AUTHOR |
| #220 RC writer未開放 | RC直書き、別writer併走、force | SOURCE PRの真の修理、Native/Rojo、負例、diffとrollback、受入パケット | 実認証された単一writer |
| Studio占有/PC使用不可 | 別Studio起動、他者PID無断終了 | 本物のソース修正、非Studioテスト、低負荷ART修正、同SHA検証シナリオ | Studio排他オペレーター |
| CI/独立レビューRED | 失敗無視、古いGREEN流用、自己承認 | 実ログから原因修正、同PRへ負例追加、更新HEADで再CI | 作者 + 別担当REVIEWER |
| 資材/認証が真に欠落 | 原本・資格情報捏造、秘密無断公開 | 手元の実ファイル照合、再現fixture、必要な最小資材・権限の提示 | その資材/権限の保持者 |
| 適法な残作業が0 | 安全回避、無意味な繰返し監査 | 未解決ISSUEに具体的 blocker/失敗操作/必要条件/next actor/再開手順を保管 | 名指しした正規主体 |

**合法な作業がある限り、失敗表示だけで止まらない。** 合法な作業が本当に0件なら EXTERNAL_BLOCKED_NO_AUTHORIZED_WORK と記録し、課題を未完了のまま残す。安全ゲートに反した実行はしない。時間/枠切れ時にも同様にGitHubへ復帰可能なcheckpointを残す。保存は後日の自動稼働を意味しない。

## E. 並列作業の責任境界
- 同じ FEATURE/FB に ISSUE_SHEPHERD 1名、非重複の実装補助0〜N、別担当の独立reviewer、RC writer同時1名を割り当てる。
- ISSUE_SHEPHERD は引継ぎ後も、正規ACK・本物のRC受入・実機証拠まで追跡する。責任移転は from/to/accepted_by/next_action の実記録がある場合のみ。未ACKなら責任は元担当のまま。
- 作者ACKを毎回求めて止まらないが、真のCLAIM/許可は省略しない。未修復の本来の問題を「他者へ依頼済み」で終結しない。
- 新たな課題を増やすより、既に着手したP0の最も下流で詰まるゲートを修理する。必要なら別レーンの衝突しない仕事を選ぶ。

## F. GitHub checkpoint 必須テンプレート
~~~text
[EGGRUMBLE_PARALLEL_NO_STALL_V1]
observed_at_jst=
feature_id= fb_id= issue_url= shepherd= priority=
official_rc_branch=rc/p0d-s1-kids-rc01
official_rc_head=<fresh 40-hex SHA>
active_runtime= private_companion= source_paths=
existing_pr= claim_id= verified_grant= reviewer= writer=
symptom= expected_behavior= root_cause= evidence=
real_source_delta= real_test_delta= candidate_head=
native_rojo_lock_off=PASS|FAIL|NOT_TESTED
official_rc_adopted=YES|NO same_head_ci= place_zip_bytes=
studio_solo=PASS|FAIL|NOT_TESTED studio_2client=
android15= art= first3min_fun= owner_accepted=YES|NO
blocked_operation= exact_error= missing_permission_or_input=
authorized_work_done_while_blocked=
remaining_authorized_work= next_real_actor= next_exact_action=
status=IN_PROGRESS|BLOCKED_EXTERNAL|CLOSED_WITH_EVIDENCE
~~~

再開時は必ず同じIssueの最新checkpointと最新RC SHAを読み、前回の未完了地点から実作業を続ける。GitHubの保存内容が全チャット・既存の実行中Codexに自動注入されることはない。正規の再開時に参照されるようAGENTS.md/#1011にも参照を設ける。既存5定期タスクの設定を変更しない。
