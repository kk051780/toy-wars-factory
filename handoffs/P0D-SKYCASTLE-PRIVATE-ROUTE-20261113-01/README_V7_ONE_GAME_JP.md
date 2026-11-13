# EGG RAID RUMBLE｜B42 First90 + 無双V7 + 天空城 — PRIVATE FULL PLACE 検証納品

**2026-11-13 JST** | 親製品採用 ID: `P0D-FUN-H1-001` | unique owned sub-slice `CHAT-P0D-SKYCASTLE-PRIVATE-SCENE-PHYSICAL-ROUTE-20261113-01`

## 親ソース・現物
今回、別作者の最新成功 [First90+MusouV7 one-game source](https://github.com/kk051780/toy-wars-factory/tree/70714a081a555d716832bb6a640611e05a1f3eca/handoffs/P0D-FIRST90-MUSOUV7-UPGRADE-20261113-01) を固定源に選び、成功したネイティブ42本/ゲームRojo42本[CI](https://github.com/kk051780/toy-wars-factory/actions/runs/43395492066) の原本アーティファクト ID `14023301437` を実際にダウンロードした。ZIPのCRC、`PLACE_RECEIPT.json`、`SOURCE_LOCK.json`、原本Place SHA256 `236d111664559cbe9943db3212ccdefa3abec957eead652eb55003895148a32e` を相互照合。元作者の本番書込み・課金・公開はない。

**今回の成果**: オリジナル元Place（42本）中の `H1FunWorld` だけを、前回本スライスで作成し Git Blob `0a6360392f4384dc2f0ab1e9afc1d840d66a22b8` の [天空城ゲーム世界源](https://github.com/kk051780/toy-wars-factory/blob/7a00fc1d90af10fa1c21473998496fc2b55c88d6/handoffs/P0D-SKYCASTLE-PRIVATE-ROUTE-20261113-01/src/H1FunWorld_SKY_CASTLE_TEST.server.luau) に置き換えた。残り41/42の全実際ソース（単一 `Game` / `Remote` / `MapBuilder` / `First90WaypointRules` / `MusouHorde V7` / `PersistentHatchStore` / XP/進化）は**元のV7版バイナリと完全同一の文字列**。

作成したユーザーへの新しい非公開Place：`P0D_B42_MUSOUV7_SKYCASTLE_PRIVATE.rbxlx`
- 本Place **sha256 = `c9f2cb947b21bb50b50457d9de32078b5e47043474607b120673383f653bd425`** / 407960 bytes / embedded original Luau 42.
- 自分の新スクリプトは元の `H1_FUN_WORLD` を1回だけ作る、独立シーン著者。新Game, Remote, egg, loot, XP, store, combat authority、paid仕様は付与しない。
- 元のB42 First90ガイドとHorde V7ダメージ表示・撃破演出・元卵1/5戦・持帰り/進化を全て保持する**一つの民間Studio試遊候補**。旧B42+天空城のまま無双V5に留まっていない。

## どのように遊びが変わるか
以前非衝突の遠景 `FLOATING_SKY_ISLAND` を topY32 の実衝突可能床に変え、元 SKY_WALKWAY (y16) から登る両陣営対称の2斜路、新床から実 MapBuilder の自陣 ScorePad (x±82,z20) 付近への下降2斜路。地下/陸の従来経路と併存し、独占クラス/課金/別得点なし。元の赤青両陣営で卵奪取→上り→中央→下り→帰還という**地形としての戦術選択肢**がソースに存在。天空島独自の城HP・得点や天空生物図鑑への本物の接続は別機能であり、実装済みだと主張しない。

## 実際に実行したQA / 限界
- **旧原V7 Place・新生成Placeの実XML差分とゲーム源をPythonで実行し 40/40 PASS**。SHA/CRC/1Game/42脚本、41脚本不変、V7元Horde blob`fc6ca46d36bb81ce5f1cd3d327ad2ab714b4be38`保護、First90/XP/save、実 MapBuilder の壁+得点台座標、4斜路の坂率/両陣営対称/原空中路からの接続/境界/衝突候補と意図的な悪い幅・高さ拒否をチェック。
- 今回の**新H1FunWorldの実Luauソース**について別途ネイティブコンパイラをGitHub Actionsで本当に実行済み。SHA `0e76e2b6fc55427c13d937079ac71a510850efe3`、[成功run43398551414](https://github.com/kk051780/toy-wars-factory/actions/runs/43398551414) の steps: pinned Luauチェックアウト、native compilerビルド、源16件ユニット検証、当該新H1 scriptコンパイル全て success。これは**源コードの構文検証**である。
- 元のV7 full42 Luau/実Rojo42/42は元作者の成功CI証拠があるが、今回の**新しい全体42版を改めてRojoから再生成/ゲームエンジン実行したわけではない**。統合版としてのRoblox Studio, 2client, Android, FPS, 人間の楽しさは未測定。成功を装わない。
- 9項目ユーザー向けZIP: 新Place/原V7 GitHubアーティファクト/原 authored H1 script/固定SHA/生成スクリプト/ローカル40件QA+ログ/受入CSV/README。 ZIP SHA256 = `d85bfb25883dea4c8ac406ad44b2f675ce261c9d80949368590b75f587e17075`。 ZIPとPlaceは本チャットで配布、GitHubには公開バイナリを無断投入せずハッシュとソースだけ固定。
- [固定 JSON](V7_SKYCASTLE_PRIVATE_SOURCE_LOCK.json) は各実験結果を明示。

## どう検証して正式統合へ行くか
1. OWNER手動で配布の新Placeを**既存のPC作業ファイルとは別に**非公開Studioで開き、エラー・実坂・床・視界を確認する。地形が見えるだけならFUN合格ではない。
2. 実2client 赤青双方、ClassicとScore5の両モードで「敵卵取得→天空城→元自陣納品台→勝敗/再戦」を試す。所持卵の境界処理・体力/敵V7・90秒案内を確認。Android横画面は別項目。
3. 元B42比較で再戦欲や陳腐さが改善しなければ `REVISE`。必要なら `#222` WORLD原作者が別の演出/ルートについて受入判断。
4. `#250` はこの新世界を**私的実験候補**としてのみ登録。公式採用にはOWNERの試遊証拠とQAが必要。ソース選択は `#250`、正式RCの唯一の書込みは `#220`。完了済みの統合や本番ソース改変とは言わない。

## 現在のステータス（P0D_PROGRESS_V3）
`feature_slice_progress=5/6=83.3%`、G1 source claim / G2 frozen original / G3 genuine candidate .rbxlx / G4 actual Python40+native source compile / G5 immutable GH receipt+handoff まで完了、G6 OWNER real physical 2client/Android/FUN は未実施。**公式S1進捗は最後の#220監査値75/100・OWNER_FUN=NO_GO**。別担当H1 RC-first90 adapter native QA進展は、今回の隔離H1が公式RCに反映された証拠ではない。

No main write/merge/Roblox publish/paid/PC Codex auto/P0 A-B-C CAS/5 automations変更。
