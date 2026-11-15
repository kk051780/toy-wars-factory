# P0D 7職業PvE v1 — 正式RC54への実コード差分

2026-11-14 JST / source ownerの独立候補。正式RC未採用・未公開・無課金。

## 実際に追加したゲームプレイ

現行RC54は本来 RAIDER/GUARDIAN の2つの基本PvPロールのみ。今回、元の唯一Game/Remoteへ下記7職業を重ねる初期PvE戦闘システムを実装した。

| 職業 | 技 | クールダウン |
| --- | --- | --- |
| 戦士 WARRIOR | 正面重撃・最大40ダメージ | 8秒 |
| 魔法使い MAGE | 前方3方向の魔法射撃 | 14秒 |
| 忍者 NINJA | 前方から背後への二段影刃 | 10秒 |
| 罠師 TRAPPER | 4方向へ中立敵の衝撃罠 | 14秒 |
| 建築士 BUILDER | 4秒の仮設砲台と中立敵追撃2回 | 18秒 |
| 魔獣使い BEAST_TAMER | 魔獣突進と0.8秒後の追撃 | 15秒 |
| ゾンビ使い NECROMANCER | 亡者の3段攻撃 | 18秒 |

ロビーでJキーか「職業選択」画面ボタンから選ぶ。各チーム同じ職業は1人まで。対戦中はQキーまたは「職業技」画面ボタンで技を使う。クライアントは職業と使用意思のみ送信し、敵の位置・威力・時間を指定できない。元Gameが生存/同一チーム/非卵運搬/非拘束/旧シーケンス再送拒否/技CDとLobby選択を検証し、元の中立Horde:hitだけを実行する。

これは「7職業のPvE操作が遊べる初期版」であり、7職業の固有HP/速度・対人魔法・本物の罠拘束・永続召喚獣・建築物の実戦破壊、魔法属性と6分野育成連動は未実装。既存の旧PvPロールと真のGame/Store/egg/score処理は変えない。建築砲台は CanCollide/CanTouch/CanQuery=false の装飾・中立攻撃のみで、卵や城の動線を塞がない。

## 実物 source authority と安全なOFF

固定ベース：正式RC54 first verified SHA 2e86ac4fd0d4cb67fd7c673dc4e891b2af6bdc2c、Place SHA256 1afdb2661b47eafa97985b27eaab5b0236d15f6f6e21863d089cebaf7e745758。既存54のうち52ソースは**バイト同一**、変更多GameとHUDの2本、純Luau SevenJobsRulesを1本追加して計55。元の唯一Game、唯一Remote、PersistentHatchStoreと進化・6分野DEV保存・Sky・Realm Hunt、既存NPC元ソース不変。追加DataStore/Remote/課金/公開操作なし。

独立スイッチ：StudioのServerStorage属性 P0D_RC_ENABLE_SEVEN_JOBS_PVE=false にすると追加7職業の選択・発動・HUDを拒否・非表示。未設定/trueならStudio環境限定で動作。公開サーバーは常時無効。既存旧ロールや通常攻撃への影響なし。

## 実施検査と統合方法

LOCAL: genuine RC54 Roblox XMLを実際に読み、55本にして再解析。Python独立24/24 PASS（未改変52、1 Game/Remote、Store byte同一、職業7種、JOB_PICK/JOB_SKILLの既存Remote、PvE限定、非侵入砲台、改変テスト）。これはソース構造証拠でありRoblox Studio実機PASSではない。

GitHub source handoffには以下のsourceをSHA固定で保存：
- src/SevenJobsRules.luau … pure server eligibility and 7 cooldowns、GitBlob a7253d36cb67df47d4ba65d35af212ed1eb7b5b2
- patches/Game.patch.zlib.b64 … 元54 Gameへの圧縮unified diff、解凍後SHA256 dace60e6a60a9de0960e2b2f91a39033264e8a7e7ed9b83f5c5ddb014176e39c
- patches/HUD.patch.zlib.b64 … 元54 HUDへの圧縮unified diff、解凍後SHA256 ba56402a37e318c9102a15c7217659bf4a0297fb27fd4c71a5ae81c0cc6c05e2
- tools/apply_seven_jobs.py … ベース54 Game/HUD byte SHA一致→zlib/base64解凍+patch --fuzz=0→砲台CanQuery=false一行安全修正→最終Game/HUD/SERVER新Module SHA照合→既存52 byte完全保持のFail Closed
- tests/SevenJobsNative.luau …純Luauの33ケース。ワークフローはNative55の実コンパイル+Rojo55実ソース一致を目標に登録。

二つの圧縮ファイルはzlib+base64テキストであり、Pythonの zlib.decompress(base64.b64decode(data)) から通常のreview可能unified diffへ完全復元できる。GitHub Blobも一致検証済み。別のRCに未検証のまま当てない。

**Native Luau55/55、GitHub Actions成功、実Rojo55、Studio1/2、Android、OWNER FUNはワークフローの結果を確認するまで未検証。** 本ChatGPT会話のローカル55 .rbxlxはXML source構造の試遊候補であり、Studio実動作未確認。正式RCは54のままで、新しい7職業は未採用。

## #220 sole writer向け

最新RC HEADのGame/HUD SHAが固定ベースと一致するか必ずチェック。正本54のソースロックが一致した場合だけ、今回の1Module+2パッチを同じrc_fastlane builderの54出力に挿入し、既存の一本化されたRC CIでnative55/55、Rojo55、元Game/Remote/Store一意を検収。実際にPASSした後のみFeatureRegistryへ SEVEN_JOBS_PVE_V1 と独立OFF switchを登録。エラー時は公式54へ切戻す。毎回のStudio試遊をRC統合前の必須ゲートにはしないが、公開前にはOWNERバッチ試遊/Android/2client/FUNが必要。main merge/Roblox publish/paid/spend/PC/CAS/既存automations変更禁止。

公式公開品質評価75/100 FUN_NO_GOは上げない。現状を完成した7職業として紹介しない。