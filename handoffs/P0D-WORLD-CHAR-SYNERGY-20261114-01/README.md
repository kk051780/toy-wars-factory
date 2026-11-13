# P0D WCS V1 — 企画室キャラ×フィールド拡張

Issue: https://github.com/kk051780/toy-wars-factory/issues/293

## 今回の現物
- `WCS_CATALOG.json`: 新領域6種、新規中立キャラ12体の衝突しないID一覧。既存D18 100体のカウントには追加しない。
- `src/CrystalCanyon.server.luau`: **WCS-F01 クリスタル峡谷 + WCS-C01 橋掘りモグロン** の単独3D/ギミック実装。2岸・常設安全迂回路・橋・両岸NPC・光る結晶・ゲート14秒開放・4秒再開制限。NPCを操作した人のチームに依らず両軍利用可能。
- `tests/test_static_contract.py`: 読める範囲の静的検査。実Studioエンジン検証ではない。

## 正式RCにまだ入っていない
本ファイルを置いただけでは既存ゲームには現れない。#220のみ、配置競合・既存卵ルート・スマホ性能/操作を評価して、**独立feature flag付き**で組み込む。現行RC/profileの他の source、Game/Remote/HP/score/XP/Storeは変更禁止。

## 手動で確認する場合（OWNER直接Studio試遊か、最終一括QA）
1. 新しい隔離Placeの `Workspace` に **Part** `P0D_CrystalCanyonAnchor` を置く（直交水平・Anchored=true・CanCollide=false・Transparency=1）。既存世界と重ならない位置にする。Partの Attribute `P0DWorldOptIn` を **boolean true** とする。
2. ソースを `ServerScriptService` に Script として配置。Play でモデル `P0D_WCS_CrystalCanyon` が生成され、Part なし/opt-in=falseでは生成されないこと。
3. 左岸・右岸どちらのモグロンの ProximityPrompt 「橋をひらく」でも、中央ゲートが14秒開放されること。近道の床は消滅せず、ゲートのみ開閉する。
4. ゲートを通過中の人がいるとき14秒が過ぎても閉じず、安全になってから閉じる。連続操作で時間を延々引き延ばせない。
5. ずっと通れる遠回りの `AlwaysOpenSafeRoute` が残り、両陣営/全職が通れること。もし峡谷に落ちても下の床/帰還階段から出られるか実機で確認。
6. 2client/Android/卵運搬/フィールドとの衝突・フォールバック、低性能機での描画性能とFUNを実測してから正式採否を決める。

## 導入制限
- **S2+**、本ファイルは独立候補。実機未検証。
- ゲーム本体のダメージ、敵AI、データ保存、報酬、課金を追加しない。
- 新NPCを魔獣として所有/装備・100体カタログに加える場合、#283/#275/#280 の正式ID管理と許可が別途必要。
- 位置アンカーは既存MAPとは独立。#220がルートのバランス/他プレイヤーとの操作を認めるまでアクティブRC導入はしない。

## ステータス
A1: 設計カタログ作成／A2,A3: SOURCE生成／A4: static検査対象／A5: GitHub受渡し／A6: 公式RC & Studio & FUN 未完。公開・main・merge・有料化なし。
