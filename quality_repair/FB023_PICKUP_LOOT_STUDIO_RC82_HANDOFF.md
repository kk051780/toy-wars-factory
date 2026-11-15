# FB023：RC82拾得武器・回復・飛行・攻城アイテムの実コード成果

2026-11-15 OWNER「つぎ」／#364 P0試遊FB、新規FB-020-D（既存#219/#470企画）。

## 再現可能な本物のPRIVATE Studioゲームビルド
- 親FB022 Place 799478B SHA256 `b84486fe8c4f80e3a7806180b538c9ddab4429f658193ba4fd2d172ebe8b0ca3`。
- 新FB023 `TRAP_RAIDERS_RC82_FB023_LOOT_PLAYTEST.rbxlx` **809461 B** SHA256 `113b9e33b8ec80cc3d41bdaa13ee40bcbece7a9597f6cea6e9ef3beaa8211677`。
- OWNERに渡した `TRAP_RAIDERS_RC82_FB023_LOOT_PLAYTEST.zip` **227553 B** SHA256 `a0adef919ee323ac07e050a80cf8ebbd6677fa9266713e89686e415239ecc3d8`。
- ZIPには完全 `SOURCE_PATCH.py`（元FB022 Place固定SHA→同82-sourcePlace再生成）、`RECEIPT.json`、Studio .rbxlx を含む。公開GitHubへ元全Place/元Game全文はpushしていない。新実装ソースの正本はユーザーに渡したZIP内。
- 真正82-script Placeで **2 source changed / 80 source byte-exact**、変更前後Git blob:
  - `Game`: `58fa069a01be430579a83782e684e7c60e72d7eb` → `522d07bb79c3262b97c791a41092a75261353463`
  - `Owner361CastleBattlefield`: `9e30498bd55ecf46036c6806177e10b98594ccfb` → `5fba01d8f9c18f16e2c0c87ef09cac182e8aeb11`
- 親SHA/Script inventory/他80源同値/元Game権威/既存7職・風走り・赤青城/4 Tool種類/8 spawn/距離/セキュリティ/ZIP byte match/2重適用防止等、静的 **52/52 PASS**。
- **Native Luau / Rojo / Roblox Studio solo・2client / Android / OWNER FUN：NOT_RUN**。実際の動作は未実証、正式RC採用0。Source XML PASSと楽しいゲームを混同しない。

## 実装した本来のゲーム機能
1. **城内と広域フィールドに8実物spawn**（4種類各2。赤青対称）。3D回収台＋ProximityPrompt（E/タップ）。Activeかつ自チーム所属/生存/実距離12stud/所持2以下のみ取得。取得後24secリスポーン。
2. **🔥烈火剣**：Server Tool.Activated時にキャラへ30secブースト。GameがHorde実ダメージを計算する地点だけStudio限定1.4倍。PvP/卵/城HP/保存/KOs権威に2重のイベントは作らない。
3. **💚回復薬**：本物のHumanoid.HealthをMaxHealthまで最大+40回復、満タンでは消費されない。
4. **🪽飛行の羽**：Roblox LinearVelocityで6sec空中移動し、PC/AndroidネイティブTool.Activated。卵所持・時間外・圏外・死亡・高高度禁止、12sec CD、各飛行に期限・境界・自動Destroy/切断。Android実機では未検証。
5. **🔨攻城槌**：敵城の前回FB022門を壊す**既存actualSiegeBreach()**に同一team/ACTIVE/距離/生存/CD制約で接続する。独立CastleHP/勝敗権威は作らない。
6. 旧セッション終了時のTool/翼/攻撃バフ清掃、永続倉庫やガチャ課金は作らない。従来の7武器を奪わず、Pickup Toolは一時的な追加装備。

## 統合／次
#297 Game作者と #366/Owner361城作者は同一最新版の修正源に2ファイルの**最小差分だけ**選択rebase。#220認証RC統合が同HEAD native Luau/Rojo + source-lockを検査して公式RCへ非force CAS。YELLOWは原因/flag/rollback記録して非公開RC進行、RED（native compile/Rojo/authority/CAS）停止。#470品質ライターがStudio実機→Android→OWNER再試遊で修復継続。新しい企画追加よりこの一試合を優先。

**未完:** 独立の城内AI戦術、魔獣Follow/Guard/Attack/騎乗/見た目、7職フル固有技、3D物理出撃ロビー。
