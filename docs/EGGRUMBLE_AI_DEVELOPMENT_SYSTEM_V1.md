# EGGRUMBLE — Codex 主力 × Chat 並列開発規約 v1.1

> **適用:** EGGRUMBLE / `kk051780/toy-wars-factory`  
> **制定:** 2026-11-22  
> **OWNER正本:** [#1011](https://github.com/kk051780/toy-wars-factory/issues/1011)  
> **関連:** #839（全体）、#218（権限/CLAIM）、#219/#250（企画）、#364（試遊FB）、#470（ゲーム品質）、#420（ART/MOBILE/FUN）、#220（唯一RC統合）、#910（P0優先順位）
>
> 本文は実行指示と受入基準であり、**CLAIM_GRANTED、認証済RC writer、Studio操作権、MAIN_PROMOTION_APPROVED、Publish許可を新規発行するものではない**。最新OWNER指示と真正なGitHub/Studio証拠を優先する。

## 0. 成果定義と優先順位

最終目標は **本物のRoblox Studioで遊べる一戦の完成・子どもの楽しさ・高品質な3D・Androidの快適動作・将来の継続率**。PR数、Luau本数、CIの緑表示、生成資料数、REAL69という名称は完成率ではない。

最初のP0は **Join → 安全ロビー → 本人READY → 7職選択 → 出撃 → 敵卵奪取 → 自陣へ持帰り → サーバ権威の得点 → 城の陥落/勝敗 → 本人選択で再戦**。同時に敵味方AI/7職固有能力/無双/旗艦ワールドを非重複範囲で改善。次が初見3分/Android、最後に適正な収益設計。新機能量産より現在の一戦不成立・実機FBを優先。

## 1. 正本、初動、旧規約の扱い

各新規Codex/Chatセッションは最初に #1011、#839、#218、#219/#250、#364、#470、#420、#220、#910、現在の `AGENTS.md`、現在の正式RC HEAD、open PR/CLAIM、最新CI、構築profile、source-lock、OFF rollbackを実際に再GETする。過去の固定SHA、引継ぎ文、記憶を最新状態と見なさない。

**唯一の正式開発RC** は `rc/p0d-s1-kids-rc01`。プロファイルの `ACTIVE_RUNTIME rich51` と `PRIVATE_COMPANION REAL69` は混同しない。REALnnは選択Luau数であり完成度%・プレイヤー実行状態ではない。

旧 root `AGENTS.md` の TOY WARS factory と main 中心の記述は歴史的規約として保存する。**EGGRUMBLEの実行方針に矛盾する旧記述のみ、最新OWNER指示 #1011 と本書を優先**する。セキュリティ・認証・台帳保全・既存ソースの可逆性・独立QA・未実測NO_GOは弱めない。別の正式RC、二重Game/Host/Combat/Store/HUD/Remote/HP/Score/XP authorityは禁止。

## 2. 部隊と責任

| 部隊 | 実作業 | 受入責任 |
| --- | --- | --- |
| Codex G1 Gameplay | ロビー・7職選択・卵・得点・城・敵味方AI・勝敗・手動再戦 | サーバ権威の1試合実機検証 |
| Codex G2 Combat | 7職能力・攻撃・HP/KO・無双・アニメ・SE/VFX | 実ダメージと手応えの再現 |
| Codex G3 World | 城/海/森/地形/魔獣/エフェクト/旗艦マップ | ART規格・描画負荷 |
| Codex G4 Studio QA | 隔離StudioでSolo/2client・ログ/画面証拠・再検査 | 本物の実機受入（環境権限がある場合のみ） |
| Chat #219/#250 | 企画室の実装価値判定・優先順位・仕様整合 | ADOPT/REWORK/REJECT/DEFER |
| Chat #470 | 構想→実ゲーム差分・真のバグ修復・負例QA | 合法な独立実装からRC/Studio/OWNER受入まで追跡 |
| Chat #420 | 先行作品に対する自作ART・Android・初見FUN | 実画面/実FPS/人間受入 |
| #220 B writer | **唯一の認証済み公式RC書込** | fresh expected_SHA、force=false、同HEAD CI、ビルド/SourceLock/rollback |

CodexもChatもソースを書けるのは **#218で真正に許可されたスコープ**に限る。新Codex導入そのものは書込権限の増加ではない。Codex同士は独立worktree/隔離branch。ChatとCodexを含め同一ファイル・FEATURE_ID・FB_IDへの二重作者を防ぐ。Studio同一Placeへの操作はセッション所有者1者に限定。

## 3. CLAIMと小さな実装単位

着手前の1単位は
`FEATURE_ID | FB_ID | OWNER | SOURCE_PATHS | BASE_RC_HEAD | EXISTING_PR | CLAIM_STATUS | CHANGE_SCOPE | ACCEPTANCE | ROLLBACK`
で管理。#218の真正 grant、許可期限、source path、役割を確認する。SOFT_CLAIM/Issueコメント/OWNER一般方針/PR作成だけでは `CLAIM_GRANTED` と解釈しない。

既存PRが同じ課題を扱うなら**元PRへの限定追記・レビュー・独立検証を第一候補**とし、同一authorityへの重複実装を作らない。受入待ちでは衝突しないソース/テスト/仕様の安全な改善を続ける。認証なしでの正式RC直書き、他作者ブランチ上書き、実機証拠捏造はしない。

## 4. 高速エンドツーエンド・パイプライン

1. 最新OWNER規約/RC HEAD/FB/既存PR/CLAIMを再GET。
2. #910 P0または実機FBからボトルネックを一つ選び、価値・測定指標・失敗条件を明記。
3. 正当なスコープで独立branch/worktreeの最小Luau/3D差分を実装。原本の保全、旧48フラグ、17機能群、Server/Client authority、無課金/OFF rollbackを維持。
4. Native Luau、Rojo ON/OFF、source/path/class/hash、セキュリティ、偽Remote/二重得点/二重報酬/再戦・途中退出の負例、差分回帰を実行。
5. 変更を別の担当が独立レビュー。新鮮な固定SHA・同HEAD CI・SourceLock・rollbackを添えて `PREP_READY` 候補にする。
6. **#220の真正なB writerのみ**が最新の正式RC HEADを再読して expected_SHA一致・force=false CASで最小差分採用。他作者はその承認/認証を偽らない。
7. 新しい正式HEADのCI、公式Place/ZIP実測bytes、source受付/既存機能回帰、rollbackを記録。
8. **Studioへのアクセス権がある実行主体のみ**が隔離環境で Solo/2client、卵・得点・城・AI・勝敗・手動再戦を実際にPlay/Stopし、ログ・映像・固定SHAで検証。
9. #420でPC/Android旧新32枚、Android15分FPS/熱/クラッシュ、初見3分理解とFUNを節目ごとに実測。失敗は同じFEATURE/FBへREOPEN、修復→再試験。
10. OWNER本人の受入を別記録。**完了は実機の改善であり、PR/Sourceだけでは完了しない**。

## 5. 品質の客観ゲート

- **ゲーム:** ロビー安全、7職（プレイヤー向け「暗殺者」、内部`NINJA`維持）、攻撃・HP/KO、正規卵・城スコア、同陣営/敵AI、勝敗、再戦同意、2clientの負例を実証する。Soloと2clientは別ゲート。
- **アート:** 城/地形/海/森/空/中立/魔獣/キャラ/装備/アニメ/戦闘VFX/HUDの視認性・造形・一体感。箱/球/Neon/文字だけを美観合格扱いしない。競合作品の素材・著作物をコピーしない。
- **モバイル:** 内部目標は低性能Android 15分 median FPS≥30、p10≥25、熱劣化≤20%、クラッシュ0。機種/画質/測定環境の実数必須。
- **子どもFUN:** 15秒で移動、45秒で攻撃手応え、75秒で実敵ダメージ、180秒で卵/城目標理解。満足4/5以上は内部目標であり未測定ならPASS不可。
- **判定:** `SOURCE_QA_PASS`、`OFFICIAL_RC_ADOPTED`、`STUDIO_SOLO`、`STUDIO_2CLIENT`、`ART`、`ANDROID_15M`、`FIRST3MIN_FUN`、`OWNER_ACCEPTED` を分離。`NOT_TESTED` は失敗を隠すための `PASS` ではない。

## 6. main昇格は固定SHAごとに別承認

正式RCを継続開発し、mainは直接編集しない。

- M0: **昇格対象RC 40桁SHA固定**、同SHAのNative/Rojo/台帳/rollback/公式CIが真正合格。
- M1: Studio Solo/2clientで一試合（卵→得点→城勝敗→本人再戦）の実機証拠、7職/AI/サーバ権威/負例合格。
- M2: ART/PC/Android/FUN、P0ゼロ、独立QA、OWNER_ACCEPTED。
- M3: OWNERが**その固定SHAを指定**した `MAIN_PROMOTION_APPROVED` を明示的に記録。
- M4: main保護PR、独立レビュー・必須CI・差分保全・権限者による非force統合・統合後検証。

どれか欠落なら `MAIN_NO_GO`。mainへの昇格とRoblox Publish/収益化・Robux課金の承認は別。追加支出も本人承認のみ。

## 7. 報告と速度KPI

毎回最低限
`observed_at_jst | official_branch@HEAD | ACTIVE/PRIVATE profile | changed_source+PR@SHA | CLAIM/CI | official Place bytes | official ZIP bytes (KiBも) | P0 loop | 7jobs/AI | ART | Studio solo/2client | Android15m | FIRST3MIN_FUN | OWNER_ACCEPTED | MAIN_NO_GO/READY | next blocker/actor`
を明記する。**同一HEAD以外のartifact容量を正式RC容量として流用しない**。測れなければ `UNKNOWN`、Studio/Androidに行けなければ `NOT_TESTED` とその理由を記録。

主KPIは「正式RCで実機検証されたP0の改善」「FB受付→実機受入までの日数」「P0残件」「初見FUN・ART・Androidの改善」。PR量産をKPIにしない。

## 8. セッション引継ぎ・利用枠

- 1回のセッションは最大限実装→QA→受入依頼まで進める。ただし**Chat/Codexが実際にバックグラウンド稼働する保証はない**。進行・停止・利用枠は真実の状態を示す。
- 既存のChat定期タスク5本の周期・実行先を勝手に変更しない。Workの枠、新規モデル、有料契約、外部サービスを無断利用しない。
- Codexは更新済み `AGENTS.md` を**新しいセッション開始時**に読んだことを確認。旧セッションが自動で再読したと仮定しない。
- Writer認証・CLAIM・Studio環境が欠ける場合は、偽の権限やreceiptを作らず非重複の安全な改善に切替え、**不足フィールド・実行主体・受入条件**を具体的に渡す。

**終端原則:** 高速開発は、真正なRC採用→実機で遊べる機能の増加→ユーザー受入で測る。安全な唯一RCとmain保護を維持しつつ、Codex/Chatの実制作を最大化する。
