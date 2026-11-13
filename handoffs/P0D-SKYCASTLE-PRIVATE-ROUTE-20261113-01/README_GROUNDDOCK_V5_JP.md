# P0D 天空城 H1 — 地上接続坂V5 非公開・実ゲーム比較候補

2026-11-13 JST | P0D-FUN-H1-001 | 独立スライス `CHAT-P0D-SKYCASTLE-PRIVATE-SCENE-PHYSICAL-ROUTE-20261113-01`

## 何が実際にゲーム内で変わるか
旧V4の元フィールドソースで `MapBuilder.GrassArena` は中心Y=-3 / 厚4→地上床の上面Y=-1。一方、既存 `SKY_RAMP_RED/BLUE` と `SKY_FORT_ESCAPE_RED/BLUE` の下端は中心Y=0、傾斜部の物理上面は概ねY=+0.89で、約1.89stud段差がある。Roblox Studio実機でジャンプ不要かは未測定だが、子供が進入/帰還しにくいリスクが残る。

今回のV5は**同じ元H1FunWorld 1本だけ**に対し、全て両陣営無料・実衝突Partで、オリジナル物理坂に地上から上がる低勾配の4本を追加した。
- SKY_GROUND_BOOT_RED: `(-78,-2,18)→(-62,0,18)`、SKY_GROUND_BOOT_BLUE: `(78,-2,18)→(62,0,18)`、幅10。
- SKY_SCORE_DOCK_RED: `(-64,-2,33)→(-82,0,22)`、SKY_SCORE_DOCK_BLUE: `(64,-2,33)→(82,0,22)`、幅8。
- 接続坂の地上端の上面約Y=-1.0、元のスカイ坂との接続差約0.1stud、勾配約0.13以下。いずれもSource幾何計算であり、ユーザー実機の移動確認ではない。
- 世界の元7ルート・物理天空城・卵/scorePad位置・Game・Remote・戦闘・XP・進化・永続セーブは不変更。元のS1正式RCや#248他作者の地形ソースへの追記無し。単一 `H1_FUN_WORLD` と単一 `Game` を維持。

## 本物の固定入力・ビルドの受入記録
- H0：実43-Luau **B42 First90 + V7 Horde + SkyCastle + Studio solo + strict4step diagnostic** の原本 `.rbxlx` SHA256 `acf0437cbb285855f6c6a6e98afae31bacc4dec2ecd8857681445729df759ee2`。
- 新V5：`src/H1FunWorld_SKYCASTLE_GROUNDDOCK_V5.server.luau` GitBlob `7a90affd4eb7eebcdfba39d833a2875ff665d5cf`, SHA256 `3bfb8d08cb305a93c5f63eba3f3157273097ce99e0f877e23959e5f69155d67a`。
- 元B42+V7+Sky source author exact SHA `a3dfc9b98f22b8edf0a7d0d978d65b1072aed933`、元StudioSolo+4step audit exact SHA `634c26a6b698c25a339fc948169c58c4773e9810` を別々に**イミュータブルチェックアウト**して新ゲームを再構築、そこにV5世界だけを上書き。
- **GitHub Actions [43413884038](https://github.com/kk051780/toy-wars-factory/actions/runs/43413884038) COMPLETED SUCCESS**、検証対象Head `daec4da0f19e1170178f0ed121aa7fc1fb4bc3ee`。ソース・幾何学・負例QA **20/20 PASS**、ピン留めした本物のネイティブLuau全**43/43コンパイルPASS**、ピン留めRojo7.7.1で実Place .rbxlxを生成、埋込43/43ソース完全一致、元H0との独立した実XML比較で**変更はH1FunWorldだけ、残り42ゲームソースは完全同一**。
- 本物のRojoPlace SHA256 `ab4987a91a79c82ca520630085215bdee8b3c99bb00f4a3535627856cb79166a`、420594 bytes、private actions artifact `14030802234`。GitHubにはバイナリではなく変更源と出所/固定SHAを保存。本会話内で配布したH0/V5比較キット ZIP SHA256 `44d35e4e0ed7f558a70468edf77a1292cf3df7c89c872a7aec8162ce086da5c8`。

## OWNERのプライベート試遊判定
Windows Studioに旧V4とV5を**別々の未公開Place**として開き、1人 Test→Play で本物の敵卵を持ち、天空城を通って元scorePadへ納品する。同じコースで **V4と比べてジャンプ不要か、赤青の地上進入口/下り口で引っかからないか、scorePadのProximityPrompt表示に障害がないか**を見比べる。次にStudio2clientと実Android横画面も検査。Output `[P0D_STUDIO_FUN_CHECK]` の実ログと自分のFUN評価を必ず別々に記録する。

FAILの場合は原本H0に即ロールバック。本スライスの独立 source+QA+private artifactは完了したが、OWNER Studio/Android/FUNは**NOT_TESTED**、公式#250の選定は原B42 PRIVATE_TRIAL_SELECTEDのみ、**V5は未選定**。公式S1は直近75/100 FUN_NO_GOで変わらない。#220だけが元RCを正式更新できる。main/RC/他作者branch/merge/公開/課金/PC/Codex/P0ABC CAS/既存5 automationsへ無断write無し。
