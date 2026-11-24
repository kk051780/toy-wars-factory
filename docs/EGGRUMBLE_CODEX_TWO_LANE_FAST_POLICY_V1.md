# EGGRUMBLE — Codex標準・2班高速開発運用 V1（OWNER正式指示 2026-11-25）

> **正本指示:** [#1011 OWNER 2026-11-25](https://github.com/kk051780/toy-wars-factory/issues/1011#issuecomment-7143853435)  
> **本ファイル:** 規約反映候補。正式RCへの採用は独立レビューと#220の唯一の認証writer経由に限定。GitHub上でOWNER指示が発効したことと、本ファイルの正式RC統合／実行中セッションへの自動適用は区別する。
>
> **対象:** `kk051780/toy-wars-factory` / 唯一の正式開発RC `rc/p0d-s1-kids-rc01`  
> **従来規約:** `AGENTS.md`, `docs/EGGRUMBLE_AI_DEVELOPMENT_SYSTEM_V1.md`, #839/#218/#219/#220/#364/#420/#470/#910/#1011 を保持。本V1はモデル選好と作業分掌・冗長検証の頻度だけ更新し、既存の真正認証/CLAIM/lease/CAS・独立QA・公開停止を緩和しない。

## 1. 成果基準と運用人数

**目的:** 作業時間の消費・PR数ではなく、正式RCの実ゲーム改善を最速で増やす。主KPIは「正式RC採用後、同SHAのStudioで改善を確認したP0/FB件数／実稼働時間」。未測定をPASS扱いしない。

- **標準:** Codex、モデルは通常 `SOL High`。局所の難題で必要なら `SOL Extra High`、構造的難題で `Astra` を選択可能。モデル選択はOWNERの運用方針であり、既存タスクのモデル設定を勝手に変更しない。180分は検証目標であり稼働保証でない。
- **並列は原則2本**。大量のチャット並列化はしない。2班は固有worktree/責務に分離し、同じfeature、FB、source path、Studio、RC writerを同時に占有しない。

| 班 | 実行範囲 | 禁止 |
| --- | --- | --- |
| **Studio班**（1本） | 唯一のRoblox Studio操作、固定SHA製品のSolo/2client・目視/動作検査、動画・画面・ログ、P0再現/同SHA再試験、FB記録 | 正式RCの直接write、別SHAへの検証証拠流用、他班のStudio起動 |
| **RC統合班**（1本） | 既存FB/PRの再利用、隔離branchで素材/Luau/テストを製作、Native/Rojo/影響範囲CI、独立レビュー手配、認証済みwriterを介した正式RC受入、同SHA成果物作成とStudio班への受渡 | Roblox Studio起動、別の正式RC作成、未認証RC/main書込、自己を独立レビューと偽る |

RC統合班に正規の#220書込権限が付与されていない場合、「RC統合」役名だけで権限を得た扱いにしない。**保護writeのみBLOCKEDにして他の許可済み非重複作業を続行**し、実認証・スコープ・正規writerを記録する。

## 2. Studioは1つ・各試験後に完全終了（絶対条件）

- 最大**1 Studioウィンドウ/インスタンス**。2client試験の必須server/clientプロセスは同じ1検証として扱い、並列に別のStudioテストを起動しない。
- 検証対象を `RC_SHA(40桁) + profile(ACTIVE_RUNTIME / PRIVATE_COMPANION) + build artifact + Place SHA/bytes` に固定。テスト途中に正式RCが更新されても、その検証の証拠は当初SHAに属する。
- **毎試験** `結果/スクリーンショット/ログと未保存変更を保存 → Play/Run/server/client停止 → Studioのウィンドウを通常終了 → 所有対象のStudioとテストclient全PID消失を確認 → 終了時刻/結果を記録`。PlayのStopや最小化だけでは終了ではない。
- 残留PID/未保存/フリーズは `STUDIO_CLOSE_PENDING` または `STUDIO_HUNG`。新しいStudioを起動せず、安全な所有範囲の解消まで待機。所有不明の別ユーザーStudioを勝手に終了しない。
- Studioにアクセスできなかった検証は `NOT_TESTED`。画面・FPS・FUNを架空のPASSにしない。

## 3. 高速化の原則（ゲート弱体化禁止）

1. **初回調査は必須、反復は差分確認。** 新しいセッションではAGENTS/#1011/現RC HEAD/適用CLAIM/既存PRと重要CIを読んで状態を把握する。同一セッションで同じ全体棚卸し・他チャット確認・長文報告を反復しない。ただし正式採用直前はRC HEAD・真正writer/claim/CI・競合と影響範囲を必ず新鮮に確認する。
2. **一件の変更は1つの検証可能なゲーム上の増分**を原則とし、既存PR/FEATURE_IDを優先する。資料だけ、形式PRだけ、仮Placeだけを開発完了にしない。
3. **自動で検出可能な不具合はCI化して任せる。** 変更pathと依存関係から対象のNative/Rojo/negative/rollbackテストを優先実行し、失敗ならログから修正候補を特定して再検証。未実装の検出器を「自動検出できる」と誤認しない。既存required CIを無効化せず、全検証を通したと虚偽報告しない。
4. **二速ゲート:** 低リスクの独立UI文字・限定素材・非ランタイム文書は対象テスト＋従来の必須CI、独立レビューと正常なRC採用で開発を進め、毎回のStudio全面再試験・32画像・Android15分・初見FUNは省略して節目でバッチ化する（その間はStudio/FUN `NOT_TESTED`）。外観が主目的の場合、視覚品質の合格判定には実画面の比較が必要。
5. **高リスクの即時ゲート:** Game/Host/Remote/Store/Score/HP/KO/卵/城勝敗/保存、source/profile選択、安全権威、rollback/manifest、実機再現の重大P0は関係する正/負例・独立レビュー・該当エンジン実証を省かない。重大P0がStudio固有なら、その修正をStudioで再確認する。Soloと2client/Androidは互換ではない。
6. **使い回せる証拠は条件固定の場合のみ再利用。** 既存QA結果は検証された `SHA, source lock, 実行profile, dependencies, tests, build/toolchain, configuration` と変更影響範囲が一致する場合のみ有効。公式RCの新HEADでは、既存要件どおり**同じ新HEADの必須CI/Place/ZIP**を確認する。
7. **待ち時間を実装へ移す。** CI・独立レビュー・Studio枠・writer受入を待つ間、権限内の未競合修正・テストを進める。Studio班は利用可能な固定SHAの試験をまとめて進めるが、開始・終了の排他ゲートは絶対に省かない。
8. **品質判定の真偽を維持。** `SOURCE_QA_PASS`, `OFFICIAL_RC_ADOPTED`, `STUDIO_SOLO`, `STUDIO_2CLIENT`, `ART`, `ANDROID_15M`, `FIRST3MIN_FUN`, `OWNER_ACCEPTED` は別々。未実施は `NOT_TESTED`、必要な合格が欠ける製品は `NO_GO`。

## 4. 具体的なパイプライン

```text
初回確認（現RC HEAD・P0/FB・既存PR/CLAIM）
  ↓
RC統合班：対象P0を選択 → 既存実装再利用 → 隔離修正/素材 → affected Native/Rojo/negative + source-lock/OFF rollback
  ↓
独立レビュー → 真正CLAIM/認証 + #220唯一writer → fresh expected_SHA / force=false による一件ずつ採用
  ↓
新しい正式RC HEADの必須CI・実Place/ZIP bytes・差分影響を検証 → 固定SHA成果物を引渡し
  ↓
Studio班：必要なRC節目/P0を固定SHAで実試遊・外観/体験評価 → 証拠保存・全PID終了
  ↓
PASS：FBと採用台帳へ記録  |  FAIL：同じFB/FEATUREをREOPENして修理
  ↖━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┘
```

- 一件のRC正式採用で完了ではなく、**同SHAでの改善再現**を一次ゴールとする。MOBILE/FUN/OWNERの本受入は別ゲート。
- 役割が2本でも、コード作者と独立Reviewer、唯一RC writerの制御は分離する。資格のないStudio班・統合班が権限やレビュー結果を自己発行しない。
- 未認証/CLAIM待ちで合法な実作業が尽きた場合は、正確な不足field・拒否された操作・次の正規実行者・未完了checkpointを残し、無限に失敗を再試行しない。

## 5. 180分トライアル・省力化の測定

実時間はGitHubコミット/ActionsとStudioの開始・終了ログの**実観測値**で計測する。時間を指定したことだけで実稼働/成果と呼ばない。

| KPI | 定義 |
| --- | --- |
| 正式RC採用スループット | 採用された独立修正件数 / 合計実稼働時間 |
| 実機改善スループット | 同SHAのStudioで改善が実証されたP0/FB件数 / 実稼働時間 |
| 循環時間 | 最初のFB登録からStudio受入までの時間（未受入は未完了） |
| 非生産工数 | 同一変更による余分なCI再実行、Studio再起動、重複調査の数 |
| 退行率 | 新規採用によるP0/P1回帰の再発件数 |

最低限の受渡しレコードは以下。1行で残してもよく、必要時だけ詳細ログ/画像にリンクする。

```text
observed_at_jst | ROLE | FEATURE_ID/FB_ID | official_RC_SHA | profile |
PR+source_SHA | claim/reviewer/writer_status | official_CI_run+result |
Place_bytes | ZIP_bytes | Studio_test_ID/PID_EXIT | observed_behavior |
SOURCE/RC/STUDIO/ANDROID/FUN/OWNER status | blocker | next_action
```

## 6. 停止しないための保護不変条件

- 書込み前の#218真正CLAIM/lease、#220唯一writer、独立レビュー、最新HEAD非force/CAS、source lock/OFF rollbackを維持。
- 正式RCは唯一。MAINへの昇格は別の固定SHA所有者承認・保護PR。Roblox Publish、課金、有料購入、追加支出は禁止（別の明示的承認なし）。定期automations 5件は変更しない。
- **本政策の登録やDraft PRは、正式RCファイル採用・自動設定・実機PASS・24時間無人稼働を証明しない。** ローカルStudio操作はアクセス権限がある場合だけ。
