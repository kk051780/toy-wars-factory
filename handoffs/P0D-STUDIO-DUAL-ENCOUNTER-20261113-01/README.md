# 企画室から実ゲームへ：H2「星ジャンプ × まもりの門獣」連続体験

**IDEA_CARD** `P0D-STUDIO-DUAL-ENCOUNTER-001` / 2026-11-13 JST / [Issue #269](https://github.com/kk051780/toy-wars-factory/issues/269) / 隔離Studio専用実験・**初回S1に未採用**。

## 何を試すか

「卵を奪って逃げる」という目的に対して、既に企画室が作った二つの戦術を**同じ一つのゲーム内に実装**する。D18展示キャラや豪華なだけの背景を増やすのが目的ではない。

- **最初の選択：** 両チームが海岸寄りの星ジャンプ台を使い、中央に素早く入る／敵を追う。元の #267 のタップ/E入力・サーバー距離判定・12秒再使用制限を**バイト単位で保持**。
- **次の変化：** 中央に近づくと、元の #268 中立魔獣「まもりの門獣」が目を覚ます。2秒警告→安全に限って中央の壁を5秒作り、8秒間休む。
- **反応する行動：** そのまま中央でぶつかるか、元の #262 の海／空／地上経路を選ぶかを考える。すべてRED/BLUE両チームで対称。卵を持っている場合も本来のサーバー判定のみが勝敗を支配する。
- **子どもに必要な情報：** 長文チュートリアルではなく、ジャンプ台の「とびだせ！」、魔獣の黄色・赤の目と「うみ・そらへ まわれるよ」という短い動機。D18案内役は元のまま。
- **商業・権限：** ガチャ、課金、報酬、新Remote、第二Game、HP/攻撃/卵/スコアの付与はゼロ。既存の無料操作だけで遊べる。

## 企画の採否は実データで判断

**一次情報**：Roblox公式 [Onboarding](https://create.roblox.com/docs/production/game-design/onboarding)、[Discovery](https://create.roblox.com/docs/discovery)、[Securing the client/server boundary](https://create.roblox.com/docs/scripting/security/client-server-boundary) に基づき、最初の行動と公平で予想できる仕掛けを重視。競合のキャラ/世界観/音源/作品名はコピーしない。

**仮説（未実測）**：単独H1と比較して、初見15秒以内に行動する割合、90秒以内に1回自分で脱出ルートを選ぶ割合、「もう1回」という反応が良くなる可能性がある。ただし追加要素で卵の目的が分かりにくくなったら採用しない。再戦率・DAU・収益への影響は **UNKNOWN**。

**A/Bの基準**：A = 原本H1 #262、B = 今回のH1 + 星ジャンプ + 門獣。因果を分解したい時だけC = #267 星のみ、D = #268 門獣のみとも比較。全て非公開のStudioで個別 Place として開く。二人対戦・スマホ横画面で、初回卵取得、中央通路、海・空迂回、納品、勝敗、再戦まで確認。子どもが説明なしに意味を理解するか優先する。

**棄却・変更条件**：最初の卵の目標がぼやける／ジャンプ後に地面・城壁に挟まる／門獣の閉門で詰む／逃げるチームと追うチームの公平性が破綻／頻繁な閉門で苛立つ／スマホでタップしづらい／物理負荷・FPS悪化。ソースQAが成功してもこの評価の代わりにならない。

## 原本保護と統合コード

- H1 #262、正本 `8f2a4aed7f6483f0bd00e31fcd733a823aa5c008`：**28本の実ゲームソースを完全保存**。空海短距離、2体の元の動く幻獣、D18案内、役職、卵、勝敗、子ども向けHUDまで保持。
- 星ジャンプ #267、正本 `af0d4eca02a48c64e530761401145b20ffcd86e7`：`H2StarLaunchPolicy.luau` blob `2879b6fc8b1547a4d13db19a616da756c04180d7`、`H2StarLaunch.server.luau` blob `b122c49f2072e383d27b1452d0bdda108f05f915`。
- 門獣 #268、正本 `e3aaadf6940397f74bb89d8bd54190260deb298d`：`H2GateBeastPolicy.luau` blob `0aee2fc29b376cb9be5362f5230245fdf634ddff`、`H2NeutralGateBeast.server.luau` blob `747c363f65aaa969af9266813fc79f6457d8e533`。
- 新規に企画・実装をやり直すのではなく、**既存原作者の4本を1バイトも変えず**に、実ゲームの同じ `ServerScriptService.TrapRaidersS1` 下で各1本ずつ実行する。合計32本、Game/Remoteは元から1つ。
- 新規の成果物と実験QAのみ `handoffs/P0D-STUDIO-DUAL-ENCOUNTER-20261113-01/**` と専用CIに書く。#219作者,#220統合者,公式RC/main,他のチャットの原本を上書きしない。

```bash
python3 -B handoffs/P0D-STUDIO-DUAL-ENCOUNTER-20261113-01/tools/assemble.py --assemble
```

GitHub CIはRojo7.7.1の実 `.rbxlx` 32/32ソースXML照合、ピン止めnative Luauの32本コンパイル、元の門獣ポリシー58項目と不正変異8件、さらに**両ポリシーを同じLuauの世界で動かす連続シナリオと9件の意図的危険改変**を検証する。これはRoblox実機とは異なる**ソース・ルール・生成試験**。

## 現時点の必須ゲート

`ISOLATED_REAL_SOURCE` および `INDEPENDENT_SOURCE_QA` が通っても、`REAL_PRIVATE_PLAY`、`OWNER_FUN_REVIEW`、`SOLE_RC_INTEGRATION`、`OWNER_RELEASE_APPROVAL` は別途必要。Studioの落下・物理衝突・二人接続・スマホ画面・人間の楽しさは**NOT_TESTED**。

これはS2のオプションであり、初回H1の人間実機テストを遅らせない。試遊結果が悪ければ**追加した4本だけを取り外し**、既存の完全H1にすぐ戻す。P0D全体の最後の公式監査は75/100、OWNERの楽しさゲートはNO_GO。
