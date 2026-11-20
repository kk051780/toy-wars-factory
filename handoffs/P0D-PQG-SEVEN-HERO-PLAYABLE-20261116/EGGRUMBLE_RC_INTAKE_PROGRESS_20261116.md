# EGGRUMBLE V3 — RC統合までの正確な進捗（2026-11-16）

OWNER最新指令：他Chatと**同じものを再制作しない**。キャラ・フィールド・バトル・城・中立兵・アイテム・ロビー・バランスを均等に前進させ、毎回**正式RC統合までの現在地**を報告する。この台帳は既存隔離 Draft PR #482 のソース候補に限定したもの。#220の全体ゲーム完成率を勝手に更新しない。

## 本日 SOURCE 実変更の要点

- 7職21技/武器7種/ロビー7職+2モード、3攻略路、個人城/複数卵/撃破時解放/全城敗北、移動AI・中立兵110上限、HEAL/DASH/SHIELD 9点の既存実装は継続。アイテム作者が別途35秒再出現を追加したため、今回の結線テストは本体ソースを上書きせず最新チェックに合わせた。
- 別々だった**元の `EGGRUMBLE_NeutralStoneGiant.luau` を、V3 TEAMとBRの各セッションに1体だけ実SOURCE接続**。新しい巨人本体を製造せず、引数に任意 `isMatchActive` / `canEngage` を追加。従来の単独`Boss.spawn(workspace,at)` APIは保つ。
- 純ロジック `EGGRUMBLE_BossSessionFence.luau` を新設。SESSION終了、脱落、別モードからの攻撃と別モードへの28HP衝撃波を禁止。実装先は新ボスではなく、既存元ボスの2秒予兆/弱点HP900/コア付近の立体実体。
- 武神/魔法使い/暗殺者/超能力者/マッドサイエンティスト/魔獣使い/呪術師の固有A/B/Cすべてが、既存の **AttackGeometryの実FAN/LANE/CIRCLE + 固体LOS** を使って石巨人の弱点へダメージできる。正当なダメージのみボスHP減少。倒した場合は独立 `EGGRUMBLE_BossDefeats` を1加算し、通常雑兵の`Humanoid.Died` KOを水増ししない。死亡後/改戦/例外時に領域を汚さず任意ボス起動失敗は`YELLOW_BOSS_OPTIONAL`。
- 他作者の独立 `EnterableCastleInterior`・`ValleyLandmarkKit`・`LobbyUXPreview` はまだ**未合流**。既存V3城・地形・ロビーへそのまま重ねると城門二重/通行経路封鎖/キュー二重の可能性があり、既存担当のsource-selective修復とStudio現物確認を待つ。

## RC統合候補のチェックリスト：3/6 = 50%（公式全体完成率ではない）

| GATE | 何を証明するか | 状態／根拠 |
|---|---|---|
| 1. 非重複SOURCEを単一V3ホストへ結線 | 7職/個人城/卵/中立/アイテム/ロビー/ボス・2モードが1つのStudio用Rojo入力にあり、単独プレビューホストは二重起動しない | **PASS**：Draft #482、`EGGRUMBLE_V3_STUDIO.project.json` |
| 2. 構造/権限/回帰のSOURCE契約 | Pythonのソース結線、TEAM/BRボス境界と攻撃形状、元作者の35秒アイテム再出現を実装条件通りに検査 | **PASS**：Python **133/133**、GitHub Actions run **43794875735** |
| 3. 実LuauパーサとゲームルールVM | 全Luau構文、城/卵57件、21技プロフィール、9アイテム×両モード、ボス15条件の純Luau実行 | **PASS**：native GitHub Actions run **43794875734** |
| 4. 最新#482 HEADのsource-exact private Place再構成・独立照合 | #220の認証統合者がこの最新版を既存 #484/#485/#487 とのclaim/diffで突合し、実Rojo .rbxlxと同一HEAD manifest/rollbackを作る | **PENDING**。別担当の過去HEAD統合候補では**21/21 source-exact private Place**生成成功したが、今回の最新7職・ボスSource採用実績ではない |
| 5. Roblox Studio 2client・Android15分・視覚/ゲーム品質 | 独立した2モード、7職21技、城門/卵/風走り/AI/ボス2秒予兆/味方誤傷なし/実コアHP/35秒アイテム復活をStudioで実地確認。Androidでfps・温度・可読性・音・演出を測定 | **NOT_TESTED / NO_GO** |
| 6. #220唯一認証writerによる正式RCへのsource-selective CAS採用 | 版Lock・GitHub独立レビュー・元作者CLAIM・同HEAD証拠/rollback・公式RCへの受入commit | **NOT_INTEGRATED**（正式RC採用実績なし） |

**計算方法**：このSource候補のRC受入ゲート6個のうち確認済3つ。**50%** は証明項目の単純件数比であり、開発工数・ゲーム完成率・正式RCの達成率・市場成功率とは異なる。正式RCへの**採用＝0件**。Studio/Android/ARTとOWNER実試遊の品質ゲートは未合格。ここを達成前に「RC統合完了」と報告しない。

**公式RC全体との区別**：#222が参照する #220 の**2026-11-12 時点の65/100監査値**は歴史的な数字。今回確認できる最新 #220 コメントでは、#484/#485/#487を組み合わせた**私的21/21 place source-exact build**に成功した報告はあるが、正式RC採用やStudio/Android/OWNER受入完了の新しい認証報告はない。よって全体RC進捗を65%→増加したと推測しない。参考：#220 コメント 6905509221。

## 8領域の現在位置（独立制作を重複しない）

| カテゴリ | 現在SOURCE | 残るRC品質問題 |
|---|---|---|
| キャラ | 7職21技・7武器・21ローカルポーズ | 元作者Rig/Animator/AvatarJointUpgrade Studio実機・見た目 |
| フィールド | 3路・尾根・森林。独立LandmarkKitは未合流 | 地形とAI経路を同時に塞がない統合・実歩行 |
| バトル | 人間/BOT/中立兵/新ボスの実ダメージ、壁LOS | 雑兵数/爽快感/音/対人バランス・対ボス回避 |
| 城/卵 | 各自1000HP・複数卵・陥落/解放・公平な防衛予算 | 本物の門開閉/籠城・個人家の見た目と快適性 |
| 中立兵 | 110現物上限・本物のKO、**試合分離した元石巨人の2秒衝撃波・弱点** | 大群実fps、巨人/AIの同時現物戦闘とボスの報酬バランス |
| アイテム | HEAL/DASH/SHIELD 3路×3個、35秒復活（元作者） | 35秒復活が同一試合で正しく働くか、卵運搬中の効果 |
| ロビー | 7職/TEAM/BR実プロンプト・AI16枠不足補充 | UIサイズ、導線、キュー/再参加/他モード隔離 |
| バランス | 21技CD/威力/攻撃形状・城防衛+5%上限・対雑兵KO連撃 | 生存時間/撃破率/城攻め勝率の実測と初心者向け調整 |

**ルール**：このBranchは私人用非公開Play候補SOURCEであって、GitHubのmain・公式RC・Roblox Publish・有料課金/外部支出を変更しない。最新の認証RC統合は唯一 #220 が行う。
