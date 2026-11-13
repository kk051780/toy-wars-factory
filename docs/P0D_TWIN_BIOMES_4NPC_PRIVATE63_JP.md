# P0D 企画室実装｜深海珊瑚庭園＋雷雲観測台＋4種NPC

**PRIVATE63 SOURCE候補。正式RCではない。** 最終的に #220 sole authenticated writer が現在の公式RC HEADを基準に分割採用・同HEAD CI確認するまで RC採用数を増やさない。

## 何が増えたか

| フィールド | 2陣営への設置 | 遊びの仕掛け |
|---|---|---|
| 深海珊瑚庭園 F03 | WCSの西岸と東岸に同じ庭園各1 | アワリンの16秒泡幕、サンゴルの16秒ルート案内灯。表示は既存モグロン門と星の橋の公開状態だけ |
| 雷雲観測台 F04 | WCSの西岸と東岸に同じ見張り台各1 | 常設6段の安全階段・柵付き観測デッキ。ライコの雷光灯、クモノンの雲の方位信号、各16秒 |

| 新しい中立キャラ | 初期レア度 | 誘発アクション |
|---|---|---|
| アワリン (AWARIN) | COMMON | 泡幕 TIDE_VEIL |
| サンゴル (SANGORU) | RARE | モグロン門/星の橋の状態を公開表示する ROUTE_LANTERN |
| ライコ (RAIKO) | EPIC | 稲妻のビジュアル信号 THUNDER_SIGNAL |
| クモノン (KUMONON) | LEGENDARY | 観測台の雲方位信号 CLOUD_COMPASS |

各NPCは西東1体ずつ=計8体。フィールド2テーマは西東に鏡写しで計4サイト。レア度は**将来の図鑑・育成の設計用識別子**であり、捕獲・ガチャ・永続所有や課金をまだ実装していない。あえて本体の卵・得点・HP・経験値・保存権限を変更しない。

## 実装と安全境界

- 作者ソース `rc_fastlane/features/twin_biomes/TwinBiomes.server.luau` Git blob `0958e7743669e670cc499035fa6446b7819cea6a`、独立Script1本としてのみ追加。既存Game/HUD/Remote/Storeは一切増やさない。
- private62（峡谷・七職PvE・1卵パス・星橋・流星橋＋スマホHUD改善）から parent 62 Script → candidate63 Script に積み上げる。既存62 Scriptのバイト一致・SOURCE_LOCK/FEATURE_LOCK、Rojoソース一致を要求。
- `ServerStorage.P0D_ENABLE_TWIN_BIOMES_V1` は明示的な BoolValue true がある**Studioのみ**起動。未指定／false／Studio外はOFF。WCS本体や安全渡橋・2岸が欠ける時も失敗側停止。
- 接触イベントでなく NPC ProximityPrompt を使用。実プレイヤー・生存・座っていない・root固定でないこと・12 stud以内をserver検証。4秒再使用待ち、16秒のみ演出。8体全体で1秒周期の**1タスクだけ**使用。無限スポーン・physics kick・無断XP/HP/egg報酬なし。
- サンゴサイトを峡谷bankローカルZ=-24、雷雲サイトはZ=+16付近に設置。実際に既存WCS bankが正しい中心・面積であることをチェック。両陣営のスペースと恒久安全橋を維持。雷雲デッキは常設階段で登れる仕組み。Studio物理/カメラ/人物衝突/横長・縦長Androidの検証は**未実施**。
- 独立OFF: `FEATURE_SWITCHES.features.TWIN_BIOMES_4NPC_V1.enabled=false`なら script追加・設定変更をせず、private62 sourceをバイト完全保持。1PRにつき1新Scriptとし、既存の峡谷・星橋・流星橋の実装と重ねない。

## 企画台帳（過大報告しない）

- 子候補カタログに **P0D-063 =珊瑚庭園SOURCE、P0D-064 =雷雲観測台SOURCE、P0D-065 =NPC4種SOURCE** の3案を追加。P0D-062は別の星かけら候補側のIDとして保持し本PRでは使用しない。
- 公式RCは現在57本、**21/58 =36.2%正式採用、企画工程加重47.4%、SOURCE以上48/58 =82.8%**。このプライベート63を作っただけで公式数を増やさない。
- PRIVATE候補の台帳は独自に61+3=64案（うち3件新SOURCE）、数え方は正式RCと別。システム観点の将来の進化・捕獲実装は P0D-029等へ接続する未完の別工程。

## 受け渡し・検査

- `rc_fastlane/test_twin_biomes.py`：26ケース静的・境界・安全契約。実際のGitHub Actionsで ALL source63/63 を pinned Luau compilerに通す。さらに pinned Rojoで63 embedded Luauをチェック、起動BoolValue唯一true、既存Game・Store・Remote唯一、WCS/Star/meteor元ソース全維持と byte-exact rollback検証。
- `rc_fastlane/rc_capacity.py`：実物のRojo `.rbxlx` 本体サイズ・61/63ソース数・SHA256を BUILD_RECEIPTと突合、 `RC_CAPACITY_REPORT.json/md` を生成。配布ZIPサイズはActions artifact metaから後で計測。
- SourceryがPRに投稿するレビューガイドだけでは品質承認としない。P0/P1実指摘があれば既存REVIEWERへ。Studio2-client・Android・実DataStore再入場・所有者FUNは未検証。
- **正式RC / main / PRマージ / Roblox公開 / 実課金 / 追加費用 / PC操作 / 既存自動タスク変更は行わない。**

ゲーム画面としての見栄えや面白さの評価は現物Studio試遊が必要。イメージ写真や合成イラストは実装スクリーンショットではない。
