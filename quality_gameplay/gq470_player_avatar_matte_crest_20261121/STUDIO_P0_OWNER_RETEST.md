# GQ470 #364 P0｜プレイヤー未出現・不透明度・カメラのStudio実機再検証

**優先：プレイヤーが出ないP0 ＞ #910一戦成立 ＞ #970 ART16 ＞ #976肩章。** この手順はゲームを修復したと偽らないための観察用です。通常ChatのGitHub上のA候補で、公式RCと公開ゲームを変更しません。

## 検証対象を混同しない

- 単一正式RC: `rc/p0d-s1-kids-rc01`、実測基準HEAD `e80973c354f14a0d0088577f3cc1a875454f0f8f`、PRIVATE_COMPANION `REAL69` (69本)。元Place `EGGRUMBLE_REAL69_PRIVATE.rbxlx` 798,390 bytes / SHA256 `fc63171149a86f6b39779ba6ebe7e18fcb7099fbde98ad2ec33a7cb92b3a9934`。
- 同一ブランチにある既存 S1 `rich51` は別の ACTIVE_RUNTIME。前者の source-pass を後者の挙動証明に利用しない。**検証したPlace名、Place ID、HEAD、起動プロファイル、試験機種を必ず保存**。
- #976の `REAL70` は **A-private候補Place** で、公式採用/ENGINE成功ではない。P0修正には使わず、P0回復後の見た目比較にのみ使う。

## 30秒の無変更ソロ／2クライアント観察

1. **ローカルのPrivateコピーだけ**をStudioで開く。元の正式Placeを上書きせず、公開・課金・Store操作を一切しない。
2. `StudioPlayerSpawnInspector.client.luau` を一時的な `LocalScript` として `StarterPlayer > StarterPlayerScripts` に配置。元のゲームソース69本や既存Host、Camera、Spawnを削除・置換しない。この診断用スクリプトは `RunService:IsStudio()` を満たさなければ即終了。
3. 「Play Solo」、続いて「Test > Start Server（2 Players）」で再試験。クライアントごとのOutputから `[GQ470_P0_STUDIO_PLAYER_APPEARANCE]` を検索し、`START`、`EVENT_CHARACTER_ADDED`、`STATE=`、`END` を時刻とともに記録。最大30回×1秒、自動終了、ゲーム状態は変更しない。
4. 再現時の画面キャプチャをPCとAndroid画角で保存。エラー行／Output／カメラの状態／Characterインスタンス有無／頭・胴体の可視状態を紐付ける。再現が消えた場合も成功扱いせず、リセット・ロビー→出撃→死亡→再戦の遷移で再試験。

## 状態別の次の調査

| Studio Output state | 調査ポイント |
| --- | --- |
| `CHARACTER_MISSING` | `PlayerAdded`、`CharacterAdded`、`CharacterAutoLoads`、ゲーム開始と`RoundReplay:LoadCharacter()`の競合 |
| `CHARACTER_INCOMPLETE` | Humanoid/RootPart生成待ち、キャラ破棄・streaming・出現位置 |
| `THIRD_PERSON_LOCAL_TRANSPARENCY_HIGH` | `ArtDistanceLOD`（4サイト）と`CombatFeel`（2サイト）がローカル人体を透明化していないか。競合有無はStudio privateコピーで逐次確認 |
| `CAMERA_MISSING`・`CAMERA_SUBJECT_REVIEW` | `CurrentCamera`、`CameraSubject`、`CameraType`の生値とローカルHumanoid |
| `ROOT_ANCHORED_REVIEW` | 意図的なロビー固定か、出撃後の固定解除漏れか |
| `SOURCE_STATE_APPEARS_VALID_ENGINE_VISUAL_STILL_NEEDS_OWNER` | これは**見えている証明ではない**。Mesh/Camera/Streaming/3D品質とユーザーの画面で再判断 |

この診断は第一人称視点で意図的に隠れる部位を誤報しないよう、**カメラ距離5stud以上／可視候補3part以上／ローカル不透明度補正0.95超が66%以上**の場合にだけ高リスク判定します。静的報告は `P0_PLAYER_SPAWN_SOURCE_TRACE.json`、いずれも**根本原因の確証ではない**。

## 修正受入ゲート

P0修正は唯一の正規writer #220が最新正式HEADと権限を確認し、fresh expected SHA・nonforce CAS・同一HEAD Native/Rojo/Source-lock/rollback合格の後、Studio Solo/2clientで「キャラ出現→ロビー→職選択→出撃→卵を持つ→得点→勝敗→本人操作で再戦」を確認。修正前後のOutput・画面・ZIPサイズを#364と#470へ還流。実機不合格なら P0 OPEN。

肩章ARTの別ゲートは `ART_32_IMAGE_RETEST_MATRIX.json`：PC/Android × R6/R15 × RED/BLUE × 20/75stud = 16条件の旧新ペア32枚、現在**0/32**。Android 15分・FPS/熱、初見3分FUN、アート競合比較・Owner受入は **NOT_TESTED / ART_NO_GO** のままです。

## #976 肩章 REWORK 後の追加検査（静的修正は実機証明ではない）

修正ソースは「透明化時は肩章ゼロ」「遠距離では透明なPartを残さずゼロ」「近距離の実生成個数 Touch 最大2人=4 WedgeParts / PC最大3人=6 WedgeParts」を目標とする。これらは**コードの制約値**であり、Studio/Androidで実測済みとは言わない。キャラ未表示P0が解消するまでは初回導入しない。

- **2クライアント R6/R15・RED/BLUE**：敵／味方を66stud以内・外側に置き、距離外の肩章Partが実際に0、戻した時に新たに生成されることをExplorerとクライアントで確認する。赤は横幅広、青は縦に高い輪郭を画面で比較する。
- **暗殺者ステルス**：Player・CharacterそれぞれのStealthed/IsInvisible/AssassinCloaked/EGGRUMBLE_StealthedのONで装飾が即時破棄され、敵から位置が漏れないことを確認。R6のLeft Arm/Right Arm/Left Leg/Right Leg、R15手足のTransparency・LocalTransparencyModifier 0.5以上でも同様。OFF→近距離復帰時のみ復元。
- **最大負荷**：多数のプレイヤーを同画角に入れてTouchで2人/4Part・PCで3人/6Partを超えない。キャラ削除・死亡・チーム切替・再出現・Streaming・減員・カメラ消失時のパーツと監視接続残留がないか確認する。
- **優先度と重複**：#975（近くの味方Highlight）と#976（両陣営肩章）は競合する代替案。実画像・可読性・Android FPSで **どちらか一方または両方却下** を#250が決める。P0不可視/卵→城→得点→勝敗が未解決なら#976はDEFER。どちらも公式RCにはまだ採用しない。

- **低負荷／ストリーミング切替**：近距離で装飾を生成した状態から LocalPlayer の `EGGRUMBLE_ReducedEffects=true` に切り替え、再スキャンを待たずに肩章ゼロとなること。falseへ戻して再生成できること。R6/R15の腕・脚を既存Characterに後から追加／削除した瞬間も古い部位のWeldと肩章を破棄し、次の0.75秒の距離選別で安全に再生成できること（Studioログ・Explorerと動画を添付）。これは現時点ではNOT_TESTED。

RETEST記録欄：R6/R15 / Team / CameraDistance / CloakAttribute / BodyAlpha / Touch / CountClientWedges / CleanupBeforeAfter / FPS / StudioOutput / TestedPlaceSHA / EvidenceLink / OWNER_ACCEPTED。空欄は**NOT_TESTED**、0/32画像なら **ART_NO_GO**。

## 結果を記録する最小セット

```text
P0_REPRO_PLACE=...
TESTED_PROFILE=ACTIVE_RICH51 | PRIVATE_REAL69
TESTED_HEAD=...
SERVER_PLAYER_ADDED=...
CLIENT_CHARACTER_ADDED=...
CLIENT_STATE=...
CLIENT_CAMERA_SUBJECT=...
CLIENT_LOCAL_TRANSPARENCY=...
CLIENT_ROOT_ANCHORED=...
CLIENT_OUTPUT_LINK=...
SCREENSHOT_LINK=...
STUDIO_SOLO=PASS|FAIL
STUDIO_2CLIENT=PASS|FAIL
P0_ROOT_CAUSE=CONFIRMED|UNPROVEN
```

この診断ソース自体は任意のStudioローカル検証用であり、公式70源に数えず、公開しません。
