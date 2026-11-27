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

## 第2弾 WCS-F02/C03 — 逆さま天空研究所と逆さフクロル（SOURCE ONLY）
- 実体: `src/InvertedSkyLab.server.luau`。新しいアンカー `Workspace.P0D_InvertedSkyAnchor` の boolean attribute `P0DWorldOptIn=true` が無い場合は**何も生成しない**。F01とは独立して ON/OFF 可能。
- 各岸の「逆さフクロル」に話すと共通の反重力ジャンプ床2台が20秒だけ有効化。再起動は終了後4秒のクールダウン。ジャンプ床の連打はplayer単位で3秒制限。
- 高架通路・左右の常設階段・常設地上橋・手すり・落下復帰床を配置。どの職業も両岸から到達可能。フクロルは非戦闘の中立案内で、攻撃・勝敗・報酬・保存に関与しない。
- パッドの飛行方向は、水平なアンカーCFrameを基準にセンターへ向ける。アンカーは**水平・Anchored・透明・無衝突**にする。既存城/卵/復活地点と物理干渉が無い独立座標に配置する。
- **QAに残す実機問題**：ジャンプの着地座標と既存Gameの移動能力、スマホ操作性、横向き画面・FPS/ネットワーク遅延、卵運搬中の着地/落下復帰、2client同時Pad使用、座標変換・Map Streaming。実際のRobloxエンジンで確認するまで完了とはしない。
- 新テスト: `tests/test_sky_contract.py` は8件の静的契約テスト。Native Luau/Studio試験の代替ではない。
- SOURCE候補と実装ステージは `WCS_CATALOG.json` で F02 + C03 のみSOURCE。F02のもう1体C04と他4領域はIDEA。既存D18の所有・図鑑・プレイアブル数とは別カウント。
- 統合依頼先はこれまで通り #220 唯一のRC writer。公式RCを書き換えない。F01のゲート閉鎖安全修正候補 #295 と競合しない独立新規ソース。

## 検証手順（第2弾）
1. 独立Placeに水平な `P0D_InvertedSkyAnchor` Part を置いて `P0DWorldOptIn`=true、`InvertedSkyLab.server.luau` を ServerScriptServiceのScriptに設定。
2. Playで `P0D_WCS_InvertedSkyLab` / 西東フクロル / 西東パッド / 連続した地上橋・階段・高架通路が生成されること。
3. 西東それぞれのフクロルから風を起こし、20秒だけ両方のパッドが起動すること。風終了後に無反応になること。
4. 2client同時使用、繰り返し接触、アバター死亡/座り/離脱時に予期しない発射やメモリ保持が無いこと。
5. 落下復帰床から同じ岸に戻ること、通常階段・地上橋で強制ジャンプなしに通過できること。
6. 実対戦の卵/救出/HP/カメラ/Android/通信遅延による問題を検証。最終のFUN判定はOWNER本人。
