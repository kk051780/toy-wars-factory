# OWNER 2026-11-20 — EGGRUMBLE 唯一の正式RC・高速積上式 V2

本契約は [#839](https://github.com/kk051780/toy-wars-factory/issues/839) の最上位規則を、実装班の短い受入手順に落としたもの。旧 [TWO_LANE_DEVELOPMENT.md](TWO_LANE_DEVELOPMENT.md) と矛盾する箇所は本2026-11-20規則を優先する。

## 何を一本化するか
- **採用先のみ一つ**：`rc/p0d-s1-kids-rc01` の最新 HEAD。企画・実装・品質候補の **隔離branch/PRは並列で存在してよい**が、第二の「正式RC」は作らない。main、force、ローカルRoblox公開、課金、支出を禁止。
- REAL65はV3の正規継承元。確認時点の後継 REAL69 にREAL65の69本選択ソース、旧RC85/RC86の有用な選別実装を積んできた。**65に巻き戻してREAL69の採用済み機能を消さない。** REAL数字はソース本数で、完成率ではない。
- 旧85本・86本のPlaceや旧S1 Game/HUD/Storeは、比較/移植元とOFFロールバックであり二重の実行権威として採用しない。旧48フラグ台帳と17群ソース保全ゲートを毎回通す。最新版として追跡する台帳は `quality_gameplay/gq8_rc85_rc86_real69_feature_truth_20261120/legacy48.json`、親を更新するときはデータと検証器をセットで変更する。
- `rich51` ACTIVE_RUNTIME と V3 REAL69 PRIVATE_COMPANION は**異なるビルドプロファイル**。同じGitブランチにあることは同一ゲーム内で動くことの証明ではない。二つの実ランタイムが本当に統合されるまでは `RUNTIME_UNIFIED=NO`。

## 速度最優先の一本の流路
1. **優先順位**：#361 ゲーム成立P0・#364 Studio欠陥 P0/P1・#420 アート/モバイル重大NGを先に修復。次に #219 企画室の新案。案の価値は「卵争奪・7職・無双・初回3分・モバイル操作・再戦・公平な収益機会」で評価。弱い/冗長/重い案は廃止可。
2. **企画と品質を同時進行**：#219 が既存カタログと照合し、`FEATURE_ID/価値仮説/ユーザー体験上の1つの差分/効果指標/優先度` を同じ #250 カードへ記入。#470 品質ライターは設計差分を確認し、できるだけ **同じfeature branch/同じPR** にLuau/3D・負例/回帰テストを書き足す。別作者のACKを待たず、#218の重複CLAIMを確認して引き継ぐ。
3. **毎回の採否**：#250 に `ADOPT / REWORK / REJECT / DEFER` と理由を1行で記録。旧版と同じもの、好ましくないものはADOPTしない。採用候補にだけ `P0D_PREP_READY_V1` と `OWNER_FAST_ADMISSION_V2` の両契約をPR本文に添える（下記）。
4. **候補を並列・採用は逐次**：A班は独立ブランチで1 PR ≈ 1検証可能な遊びの増分を作る。B班 #220 は唯一の公式writer。候補の `Game/Remote/Combat/Host/Swarm/Store/HP/Score/HUD` 一意性、原本source-lock、旧48フラグ、17群無損失、Rollback、最新SHA、CIを確認して **fresh expected_SHA・force=false** で一件ずつ正式RCへマージ。公式HEAD移動時は候補を新HEADへ追従・再CI。stale候補、重複PRを無理に採用しない。
5. **二速ゲート**：小PRごとに Native/Rojo/source class/hash/パス/負例/rollback/保存権限の高速CI。CIがGREENなら、Bは逐次採用し **新公式HEADの同HEAD CIと唯一の最新Studio ZIP・Place bytes** を確認。Studio solo/2client、Android15分FPS/熱、初回3分FUN、アートの旧新32枚・競合比較は **RC節目ごと** にまとめる。ただし重大なP0が実機依存ならその場で再試遊が必要。SOURCE_PASS ≠ GAMEPLAY_PASS/ART_GO/OWNER_ACCEPTED。
6. **循環**：採用直後に #250 へPR/HEAD/run/artifact/byteを記載し、#219/#470へ採用結果と未解決FBを返す。実機NGの場合は同じFEATURE_IDを修正し、別RCを作らない。企画室は完成したゲームの不足を点検し、#470は欠落を実装して続ける。会議、試作Placeの乱造、承認待ちだけで停止しない。

## 新規PREP PR本文に追加する最低契約
旧 `P0D_PREP_READY_V1` の5フィールドを維持した上で、次の4フィールドを付ける。これは読取専用の高速候補選別器でチェックされる。**このテキスト自体は人間のQA承認やCI成功の代替ではない。**

```text
OWNER_FAST_ADMISSION_V2
DECISION: ADOPT
DESIGN_SOURCE: https://github.com/kk051780/toy-wars-factory/issues/219
QUALITY_EVIDENCE: https://github.com/kk051780/toy-wars-factory/issues/470
VALUE_DELTA: 旧実装より卵争奪の操作を分かりやすく改善する
```

- `DESIGN_SOURCE` は #219 または #250 の実際の仕様/採否記録リンク、`QUALITY_EVIDENCE` は #470 / #420 の監査結果または該当PRのQA証拠リンクに差し替える。単にトップIssueを貼るだけではBの最終承認にしない。
- `ADOPT` 以外は自動採用候補から除外する。採用判断後に品質不合格となったら `REWORK` へ戻す。
- PREP selectorが受入「候補」を選ぶのは形式・同HEAD CI・fast-forwardの条件を満たした場合のみ。正式ブランチへの自動mergeを認めない。source-only改修の品質を実プレイ品質と誤認しない。

## 毎回の進捗数値（分子・分母・検証範囲を明記）
- `historical_flag_inventory_pct = ledgerに存在する旧RC85/RC86フラグ数 / 48`（台帳管理率）。
- `historical_source_marker_pct = 最新公式成果物の旧フラグ由来検証マーカー件数 / 48`（移植ソース根拠率）。analogue-only、gap、QA-onlyを同じ「採用済」に足さない。
- `adoption_decision_pct = ADOPTまたはREJECTに明示確定したゲーム機能 / 旧48中のゲーム機能46`。不明なら UNKNOWN。
- `feature_rc_pass_pct = 正式同HEAD source&QA PASS機能数 / 採用対象機能数`。対象未確定なら UNKNOWN。別の `Studio/FUN` パス率も証拠が無ければ NOT_TESTED。
- **公表用ゲーム完成率を、REALのソース本数、旧台帳48/48、PR数、元S1の旧75/100から推計しない**。

## 安全
通常ChatのGitHub接続でのみ作業。Work / Codex / Computer Use を起動・フォールバックしてWork枠を消費しない。main/publish/paid/storeの本番切替・forceは禁止。権限不足時はREAD_ONLY/未採用を明記。規則が存在することと、未統合機能が実ゲームへ接続されたことは別。OWNERの本人確認と #220 Writer/CLAIM/CAS 条件を維持する。
