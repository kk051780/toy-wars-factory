# P0D 企画室 H1｜短い海・天空ルート × 卵ゲット演出 一本化

**ISOLATED PRIVATE ROBLOX STUDIO ONLY — 本編公式RC・公開版ではない。**

## 子どもの楽しい一試合（仮説）
「敵の卵を盗む → 地上・海・天空の近道を選ぶ → 追いかける／逃げる → 持ち帰って得点 → 仲間と喜ぶ」。操作を増やさず、**逃走ルートの選択**と**成功の喜び**を同時に体験できるH1候補。製品採用カードは既存 **P0D-FUN-H1-001** #250、企画室成果 #266 と地形 #262 の独立結合 Issue #270。

**原本28ソースを一切編集しない。** 入力ゲーム：#262 immutable SHA `8f2a4aed7f6483f0bd00e31fcd733a823aa5c008`（全28本Rojo/native PASS）。オリジナルGame、卵、勝敗、RAIDER風走り、GUARDIAN罠、運搬中ボタン無効化、D18熔炉の角竜、動くSPACE/CELESTIAL魔獣2体、MapBuilderをすべて残す。SEA/SKY近道の修正世界スクリプト GitBlob `7aaa2a48d3e58c7c00bc805b74d0c9d8737217ea` は差し替えずそのまま使用。

追加のみ：#266 完成済み本物の2クライアントソース（`EggJoyRules.luau` GitBlob `d467ab80f6b514026b9583d48c44cb6fe5019bc3`、`EggJoy.client.luau` GitBlob `4066bf4ab5b157be39c14d1d57a7a0f0af107139`）から、既存の確定サーバーSNAPSHOTの「敵卵取得」「チーム得点」「自軍勝利」を1.57秒以内の小さな8宝石GUIで表現。初期同期／古いUpdateId／新試合／敵得点／引分／敗北では誤表示しない。Remoteを新設せず、FireServer、報酬、HP、魔獣戦闘、課金、保存や宣伝はしない。

## 統合・受け入れ
```
python3 handoffs/P0D-H1-FAST-JOY-COMBINED-20261113-01/tools/assemble.py --assemble
```
#262の実ソースを28本ビルドし、その全部をバイト固定検査した後で2個の原本を増やす。**完全なLuau 30本**（ServerScript 2 / LocalScript 5 / ModuleScript 23）、正確なRojoプロジェクトを独立 `dist/TRAP_RAIDERS_H1_FAST_SEA_SKY_JOY_STUDIO_ONLY` 以下に作る。他担当のソースは読み取り専用。

専用CI：`.github/workflows/p0d-h1-fast-sea-sky-egg-joy-20261113.yml`。原本8個GitBlob厳格照合、#262の城壁・岩と近道の24件source regression、#266の真Luau39イベント・敵対入力チェック、すべてのLuau30本をピン留め公式native compiler、Rojo7.7.1完全Place生成＋XMLに埋め込まれた30/30バイト一致を検証し非公開Studio用artifactを出す。**CI完了前に合格宣言をしない。**

## 子ども実機で判断すべき問い（未検証）

1. 15秒で「どちらの卵をどの陣地へ持ち帰るか」がわかるか
2. 90秒で「海・天空が近道」だと気づくか。直進より有意義な作戦か
3. 卵を奪った1.57秒演出がゲームに集中する邪魔にならず楽しいか
4. 2clientで両チームが卵を運べるか。実スマホのLandscape HUD/カメラ/落下/占有FPSが問題ないか
5. 「もう一試合遊びたいか」、H0 vs #260 vs #262 vs #270 の実測コメントや録画で判断。数字は目標・未計測であり実績を作らない

この候補は試遊素材であり、最初の公開を遅らせる必要はない。#220 sole writerが採否選択するまでは正式RCへ取り込まない。**公式全体進捗75%、FUN_GATE=NO_GO（実機未試験）**。main・公式RC・merge・Roblox公開・課金・PC Codex・P0A/B/C CAS・5 Automationsを編集しない。
