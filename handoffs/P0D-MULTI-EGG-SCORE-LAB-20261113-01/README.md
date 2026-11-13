# P0D H2企画室 — エッグ・スコアバトル 5個卵 実行可能試験

**これは現行H1/公式RCではない。** ユーザーが2026-11-13に発案した「卵を複数持って点数を稼ぐ。城に納めたらもっと高得点。自陣卵も抱えて逃げられる」を、既存企画室 #219 の設計カード（comment6842809217）を読んだうえで、**隔離された実際のLuaサーバールール＋元々の5卵を手で拾えるRoblox Studio検証Place**に変えた。新規Issue #272。唯一の公式RC書き込み #220 や既存H1のGame/egg/round権限を壊さない。

## 体験：4分5個卵
赤2個（R1/R2）、青2個（B1/B2）、真ん中レア1個（N1）。相手卵/真ん中卵を盗んで自陣の黄色い金庫へ運ぶと得点、保持したまま逃げても時間で小さく得点、自分の卵を奪われそうなら先に持って逃げてよい。

**製品企画時点の仮数値。実機バランスは未検証。**

| 状態 | 暫定得点 |
| --- | --- |
| 敵所有卵を持っている | +1点/10秒 |
| 敵所有卵を自陣金庫へ初回納入 | +12点/卵×チーム/1試合のみ |
| 敵所有卵が自陣金庫で保管中 | +3点/10秒 |
| 自分の卵が自陣金庫/初期保管中 | +1点/20秒 |
| 自分の卵を抱えて護衛・逃走 | +1点/30秒 |
| 中立卵を持っている | +1点/10秒 |
| 中立卵の自陣初回納入 | +10点/チーム×卵/1試合のみ |
| 中立卵を自陣金庫で保管中 | +2点/10秒 |
| 自分の卵を実際に敵支配から奪還し保管 | +2点（同一卵は試合に1回まで） |

得点は1秒整数tickで計算し、保持・保管の継続時間は**状態移行で毎回ゼロから**再計測。卵を同時に2人が持つ/1人で2個持つ/同じ卵を繰り返し出入れして納入ボーナスを稼ぐ/切断や死亡で卵が複製/試合終了後得点を稼ぐことはサーバーモデルで拒否する。タイム240秒で点数勝ち。実験Labの同点はDRAWとし、既存の企画カードにある延長30秒（中央卵を巡る争い）は**まだ未実装**と明記する。

## ソースと権限
- `src/server/MultiEggRules.luau`：本物の server-only scoring state machine。1卵1ID/1ホルダー/transferSeq単調増加/5個保存検査。
- `src/server/MultiEggLab.server.luau`：**Roblox Studio内だけ**起動する完全独立の小型対称フィールド、5つの実際のPart卵、赤/青の金庫、サーバー検証のE/タップ ProximityPrompt、卵を腕に装着、死亡・切断でDROP、4分点数集計。チームは参加順で安全に均等配分。StudioではUserIdが負数になり得るためサーバーのみが採番した正のholderIdを使用する。
- `src/client/MultiEggHUD.client.luau`：サーバーからReplicatedStorage属性で読み取る点数/残秒/自軍/子ども向け説明のみ。FireServerなし、スコア操作・遠隔命令なし。
- `default.project.json`：**実Roblox Place 3 Luau**（Script1, ModuleScript1, LocalScript1）。H1の元コード28/30/32本を同居させない、公式ステージ/職業/魔獣/天空・海の表現はこの小型Labには搭載しない。独立のゲーム性試作であり、そのまま本編リリースしてはいけない。
- `tests/generate_native_test.py`：元Luaソースを直接包み、Luau正規ネイティブインタープリタでRED/BLUE・5個保存/二重Pickup/所持1個/出し入れ不正/継続点/敵金庫/奪還点/中立金庫/死亡切断DROP/時間終了/古いチーム騙り/終了後加点なしを検査。
- `tests/check_studio_place.py`：実Rojo XMLにサーバー1＋共有ルール1＋クライアント1の**厳密な3/3ソース一致**を確認。新しい不正Remote/Marketplace/DataStore不可。
- GitHub Actions `.github/workflows/p0d-h2-five-egg-score-lab-20261113.yml`：Rojo7.7.1 SHA256固定、upstream公式Luau固定f46d879e28302a430029304f7f6a162aed66f103、3ファイルの本物のLuau native compile＋pure module実行、非公開Studio Place artifact。

## Windows Roblox Studio試遊
1. CIが成功した場合のみ、そのActions artifactの `P0D_H2_MULTI_EGG_SCORE_LAB_STUDIO_ONLY.rbxlx` を開く（公開せず試す）。
2. Test → Server + 2 Clients を起動。赤と青に割当。黄色いパッドへ自分/敵/中央卵を運ぶ。
3. 左右対称に敵卵を運んだ得点を照合、中央卵の奪い合い、死んだときのDROP、拾い直し、二重得点不可、タッチ範囲、モバイル横画面・FPS・4分決着を記録。
4. 現行H1/H0の対戦体験と直接比較し「得点ルールが子どもにも分かるか」「守る/逃げる/奪うの3つを自主的に試したか」「もう一試合したくなるか」を評価。結果不明なら正式H1を変えない。

**特に未実装の重要事項**：既存H1の唯一のGame.serverを使った5卵切替/現行の職業・トラップ・キャラ/海・空・城壁/本体サーバーの試合勝敗/永続保存への統合、実負荷の2client確認、実Android、OWNERの90秒面白さ評価、勝敗の延長タイブレーク。今回Labの成功をこれらの完了と誤表示しない。まず既存H1の実際のFUN評価を優先する。

公式#220 P0D全体最後の監査75/100、FUN_GATE=NO_GO。main・正式RC・他企画室 #219ソース・GitHub merge・Roblox publish・課金・所有者PC/Codex・P0A/B/C CAS・既存5 automationsは変更しない。
