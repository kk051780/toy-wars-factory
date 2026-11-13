# P0D #220：B42＋V7無双＋天空城／1人Studio試遊＋診断（未公開）

## これは何か
本ゲームの旧S1ではなく、B42の卵／First90誘導・XP・進化、V7無双敵のダメージとKO、実際の物理天空城を含む**企画室の充実版**を使った試遊候補です。正式RC・公開サーバーには採用していません。

- 原本: 42本・固定HEAD `a3dfc9b98f22b8edf0a7d0d978d65b1072aed933`
- 既存作者のソースは41/42本を完全に保持。元の単一Gameのみ、Studio内の1人試遊条件を変更。
- 新規サーバールールは `StudioSoloPreviewRules.luau` 1本。**1人で始まった試合かをラッチ**し、2人から途中退出で1人になっても通常試合の終了判定を使います。公開環境は従来どおり2人＋両チーム必須です。
- さらに作者の更新版（固定コミット `2033fc1eff730c416474792510c431270775e639`）として納品された `P0DStudioTrialAudit.client.luau`（Git Blob `b09e5fa2b3374cb88cad789b2c4966d4c777b3ef`）を**改変なし**で追加し、元のHUDに重ならないOutput用診断を使います。
- 合計**44本**（Game/Remote各1、World1、LocalScript6）。実装内の卵・HP・score・XP・進化・保存は元の権限を維持。診断側はスナップショットを見るだけでFireServerしません。

## 検証済み
GitHub Actions `p0d-integrator-b42-v7-sky-solo-20261113.yml` にて原作者のSkyCastle16件・V7 8件＋独立統合9件＝**33件**、ネイティブLuau **44/44構文**、Soloラッチの実行 **40/40アサート**、Rojo出力XMLで**44/44ソース一致**、唯一Game・World・診断各1を検査しました。

## 手動試遊：Windows Roblox Studio
1. GitHub Actionsの最新成功ランから `P0D-B42-V7-SKYCASTLE-LATCHED-SOLO-AUDIT-44-PRIVATE-PLACE` を取得し、ZIPを展開して `.rbxlx` を開きます。**公開は押さない**でください。
2. Studio → `View` → `Output` を表示、`Test` → `Play` を1名で開始。`[P0D_STUDIO_FUN_CHECK]` で始まるログを確認します。
3. `PHASE LOBBY → COUNTDOWN → ACTIVE` の順に遷移すること、`FIRST90` で初回の卵目的地が表示されることを確認します。出ない場合はOutput全文の当該ログと再現手順を控えます。
4. 実際に敵城へ歩いて卵を取得します。`EGG_CARRIED` が出てから自陣へ運び、得点時に `SCORE_CONFIRMED` が出ることを確認します。卵を落としただけでは得点になりません。
5. 画面右下の **0/4→4/4** 診断を使います。①ACTIVE、②敵卵所持（サーバーSNAPSHOT）、③卵を保持した状態で天空城の床に実際のHumanoidが接地（端末のローカル観測）、④同じ試合でサーバーの得点増加を観測、の4段階です。途中で失敗した段階が分かります。**4/4でも、卵を途切れず運搬したことや歩行可能性の独立証明ではありません。**
6. V7敵を攻撃して実ダメージ数値とKOを見ます。天空城の登り坂・上面・脱出坂が**実際に歩けるか**確認します。`SKY_SOURCE` は部品の存在検査で、移動可否の証明ではありません。
7. 別のテストではStudio内に2人を用意して対戦を開始し、片方を退出させます。**元が2人試合なら練習モードに変わらず終了する**ことを確認します。

## ログの意味と注意
- `[P0D_STUDIO_FUN_CHECK] BLOCKED` は原本の構成要素が見つからない等の試遊障害候補。
- `EGG_CARRIED` と `SCORE_CONFIRMED` は**サーバーのSNAPSHOTに基づいたクライアントの観測記録**であり、信頼できる独立サーバー監査ログそのものではありません。
- 右下の診断枠はStudio専用の読み取り表示で、HUD/HP/得点を操作しません。Outputには `SKY_WITH_EGG` と `SCORE_AFTER_SKY` が現れます。`SCORE_AFTER_SKY` は同一ラウンドのスコア変化を意味し、運搬の連続性まで証明しません。
- 診断はStudio外で動作せず、最大110件。ユーザーID・名前のログを追加していません。Output共有時はその他の個人情報を含む行を除いてください。
- 検証済みなのは**ソース／ネイティブLuau／Rojo Place生成**です。Windows Studio 1人・2人実プレイ、Android操作、FUN合否はすべて**NOT_TESTED**。本試遊をして初めて判定できます。

## 採用・権限
`#250 product_private_trial_selected=B42` を上書きしません。`product_official_rc_selected=NO` のため公式RC `1263a03701211a652b99b91d2339575dc8104eff` は未変更、最後のS1評価 **75/100／FUN_NO_GO** 維持。採用判断後に#220唯一のRC writerが公式差分を審査します。公開・merge・追加課金・PC Codex実行は禁止事項として維持します。
