# P0D H1 / Studio天空城・同一卵・得点チェック V4（非公開）

2026-11-13 JST / 独立担当 `CHAT-P0D-B42V7-SKY-STUDIO-SOLO-PLAYTEST-20261113-01` / `P0D-FUN-H1-001`

## 実害を確認して修正
前回43-Luau版の `SCORE_AFTER_SKY` は、天空城で卵を持つ→途中で落とす／卵を持ち替える→同じ試合でスコアが増える、という流れでも4/4の誤成功が可能だった。採用判断に使える証拠ではなかったため診断専用LocalScript `P0DStudioTrialAudit` のみ差し替えた。残り42ゲームスクリプトは旧版と**バイト単位で完全一致**、元の試合・卵・得点・成長・無双V7・天空城のソースを一切変更しない。

## 正しい試遊チェックに必要な同時条件
1. サーバーが該当ラウンドで `ACTIVE` を通知している。
2. サーバーが**本人に**所持卵IDを送った。Studioではプレイヤー1人だけがログイン。
3. 所持した状態で実キャラが `FLOATING_SKY_ISLAND` 内に入り、足元へのRoblox `workspace:Raycast` が島の本物の床Partに当たり、Humanoidが接地している。
4. 天空到着後、サーバーの `SNAPSHOT` で卵IDを変更/喪失せず、キャラクター/ラウンドを変えない。落とした／持ち替えた／死亡・リスポーンした／ACTIVE終了なら即 `ROUTE_RESET` で天空チェックを消す。
5. 同じラウンド、同じ卵IDを直前まで所有していた本人のサーバースコアが増え、**その同じ得点スナップショットで所持卵が空**になったときのみ `SCORE_AFTER_SKY` と4/4。2人対戦時は誤認防止のためこの4/4判定の対象外。

元のゲーム側のサーバー権威は変更しない。これは**スナップショットとローカルRaycastを組み合わせた観測**であり、スナップショット間のすべてのイベント、移動した具体的ルート、実際のWindows Studio物理、Android、OWNER FUNは証明できない。OWNERの手動試遊が必須。

## 生のテスト証拠
- 修正診断スクリプト正本 Git Blob `ee96518a7eeaaaba98d2a8e2aff6dad780fae8c7`、SHA256 `8303b72d8e7bd64475cdbf47af9dfde03df6bc9a4651a7ff5f16565a13f48e21`。
- 実際の前版43-Luau Rojo Placeから**本物の**Game/HUD/H1FunWorld/Horde/V7ソースを保った新版。原本との独立XML比較は42/43スクリプト完全同一、更新は `P0DStudioTrialAudit` 1本だけ。
- GitHub Actions **COMPLETED SUCCESS** [run 43410261380](https://github.com/kk051780/toy-wars-factory/actions/runs/43410261380) / 証拠コミット `5a5ffad1f996f12c87e4790ba0deebb9e1e48895`。Source/negative Python = 33+28 = **61 tests PASS**。ピン留めされた本物Luau全 **43/43** 構文コンパイルPASS、元クライアントの純粋な条件関数を抽出して本物Luau VMで網羅実行した **792/792 assertions PASS**。ピン留めRojo7.7.1で実物 `.rbxlx` を再生成し、埋め込み43/43 source原文を確認。
- 生Place SHA256 `acf0437cbb285855f6c6a6e98afae31bacc4dec2ecd8857681445729df759ee2` (419734 bytes)、GitHub Actions artifact `14029461791`（未公開7日）。ユーザーへは同ファイルと旧版、受領ハッシュ、操作方法・空欄評価表を会話内で別途配布。ZIP SHA256 `eb34d8d5e3b3629691032bd0b7c6d25e1a686c7da22400bcd7ec3aa01b51270b`。
- 初期二回のCI失敗は「生成する792試験を468と誤算」「抽出マーカーコメントをLuauへ混入させた」検査生成器の欠陥。両方修正して実行し直し、最終成功を確認。失敗を隠していない。

## OWNER手動受入
配布した最新 `.rbxlx` を既存Placeと別のStudioファイルとして開き、`Test→Play`。画面右下の0/4→4/4とOutput `[P0D_STUDIO_FUN_CHECK]` を見る。まず通常の卵取得→天空城→納品を確認。次に**負例**として天空城へ行った後で落下・死亡・卵持ち替えを行い、`ROUTE_RESET` になり、同じ卵を持ってもう一度島へ登るまで4/4が成立しないこと。2player赤青・Android性能・実際の面白さも別ゲート。

## 公式採用境界
#250での正式製品選定はNO、#220は唯一の公式RC writerであり**この試作をRCに自動採用しない**。公式S1の直近評価75/100、FUN_NO_GO据置。Studio2client/Android/OWNER FUN=NOT_TESTED。main/公式RC/他作者ブランチ/公開/課金/PC/Codex/CAS/既存自動化への書き込みはゼロ。
