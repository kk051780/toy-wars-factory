# P0D FAST RC: 6技能と天空城を個別に切り替える

2026-11-14 JST。#220正式RCの高速一本化方針に従う**非公開ソース候補**。#220のRCブランチは変更しない。StudioやFUNは公開前の一括ゲートに残し、機能追加の度に試遊を必須とはしない。

## 基準の正式RC
Current rich51 source 79123d35cd7afdd5f4f9941675bc2d2cf382ac4e、最後に確認できたRC head 50bf5b4851fc0eb7c16052f578d6360ec54cd63a、成功した正式RCビルド run43483997763。元の実物rbxlx SHA256 6c9d36d6944301c4fb7317e087f877f5cdeb513b38213608976da4cce1c6bb65。

## 2つの実際のサーバーフラグ
- ServerStorage attribute **P0D_RC_ENABLE_V4_SESSION**: 未設定/trueでON（元の51互換）、falseで追加V4セッション修行XP・試作訓練台・試作UIを停止。停止中の時間をON時に遡及加算しない。元Gameの魔獣/武器道場・永続化には触れない。
- ServerStorage attribute **P0D_RC_ENABLE_H1_SKYV5**: **サーバー起動前**にtrue/未設定なら天空城を生成、falseなら天空ルート・浮島・雲を生成しない。海ルート・幻想生物・元Gameの得点・卵・HPは維持。試合途中で実体の足場を消す動的切替は行わない。

元51本の**48本は完全に同じ**。変更対象は元の H1FunWorld / V4TrainingBridge / V4TrialOverlayの3本だけ。Game/PersistentHatchStore/元Remote/egg/score/HPは完全保持。天空城GitBlob 7a90affd4eb7eebcdfba39d833a2875ff665d5cf→6e8324bba70a25ba0348a3dfae807f9c9a2e827a。

## 実行済み検査
実物正式RC XMLから自作した非公開51スクリプトPlace SHA256 **1ecabaad4a52c6107ac30b4dfe3740373a9afcff35708b0cca94013a53a54d1d**。固定版native Luau51/51 compile PASS、17/17 Python local unit/negative PASS。実際のRoblox Studio・2人・Android・FUNは NOT_TESTED。6技能永久保存/戦闘強化も未実装。オーナー用バイナリ/QA ZIPは当チャットにあり、GitHubソースにPlaceはアップロードしていない。

## #220 RC一本化への引き継ぎ
1. このown root内 tools/assemble_two_switches.py --assemble を利用。元rich51著者の51本を一度組み上げ、元のSOURCE_LOCKを確かめ、独立DISTで3本のみ差し替える。元作者branch/sourceは未変更。
2. tests/test_two_switch_source.py で元48本の不変・固定GitBlob・2スイッチ・海/幻想生物維持・単一Game/Remote・禁止権威をチェック。
3. #220唯一のwriterが新固定commitをrc_fastlane/ACTIVE.jsonと元の1本のRC Actionsのsource-pin/assemble/DISTに設定して、SOURCE_EXACT51/51・Game唯一・RojoバイナリPASSを一度だけ実行。両機能のみFEATURE_REGISTRYのswitchを真として登録。
4. 失敗時は元rich51 source SHA 79123d35...へ復帰。rich47/legacy21は触らない。天空城以外のH1個別機能切替は未実装。

**RC_ADOPTED=NO、PUBLISHED=NO、MAIN_CHANGE=NO、PAID=NO。最後の公開品質75/100 FUN_NO_GO据え置き。**
