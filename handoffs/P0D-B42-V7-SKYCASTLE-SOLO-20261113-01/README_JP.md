# EGG RAID RUMBLE / P0D — B42 + 無双V7 + 天空城 + 1人Studio練習版

2026-11-13 JST。**Roblox本番公開版ではなく、OWNER非公開Studioで試す候補**。

## 統合の目的
直前の非公開一体型 B42/V7/SkyCastle は、卵・敵・天空城まで実ソースで42スクリプトに統合され、CIを通過した。一方、実ゲームGame.serverは通常通り **MinPlayers=2、赤青両チーム存在**を要求し、OWNERが1人でStudioを起動すると試合がLOBBYから進まず、卵取得や中立敵戦闘を体感できない。

## 今回追加した機能と厳格な境界
- #220 sole RC統合担当が独立した純Luauモジュール **StudioSoloPreviewRules.luau**（原Git Blob `22e7e22e8837dbf44c57fdfb30efd480457022fb`）を隔離ビルドへ**そのまま**使用。
- ORIGINAL B42の Game.server 1本だけに、既存のLOBBY開始条件、COUNTDOWN維持、ACTIVE敵チーム欠員処理の3箇所を最小接続。
- **RunService:IsStudio()=true かつ参加者が1人でRED/BLUEの片側のみ在籍する場合だけ**練習を開始可能にし、敵側プレイヤー不在で試合が直後終了することを防ぐ。
- Studioで2人以上なら従来どおり赤青両方が必要。公開/通常サーバーは従来の2人以上・両陣営必須・チーム欠員終了を変更しない。
- 赤青の卵の元ルール、server-owned score/HP/XP, 1卵/5卵、First90誘導・経験値・進化、V7実ダメージ/KO、天空城の既存Worldは変えない。新Game/Remote/score/scheduler無し。
- 旧42本のうち41本は厳密にバイト同一。1本だけGameを最小変更し、1つ純ModuleScript追加した **43本版**。

## 検査
own source-contract checks / original sky-castle geometry checks / previous B42 progression and V7 regression; 43 genuine native Luau compiler、#220元ソース純solo module実行30 assertions、V7本物の敵挙動79、First90 48、Waypoint39、およびRojo exact-source 43/43 によりビルドをゲート。成果物内SOURCE_LOCKとPLACE_RECEIPTでSHA検証する。

**重要：native testsは本物のRoblox Studio起動ではない。** 実際のStudio単独開始・敵卵を持って天空城へ登り赤/青scorePadに戻る物理連結・Android/FPS・2client対人勝敗・人間によるFUN判定は未検証。

## OWNER実機試遊の最短手順
1. 既存Studioゲームをバックアップし、CIから得た専用 .rbxlx を**別の未公開Place**で開く。本番へのPublishは禁止。
2. **まず1クライアント**でPlay。LOBBY→COUNTDOWN→ACTIVEに進み、初回90秒の案内、敵卵獲得、帰還スコア、中立敵8体+精鋭1体への攻撃・ダメージ数字/KO、進化・無料魔獣を確認。
3. 天空城の両側の登り坂・床・下り坂を歩き、卵を保持したまま自陣得点台へ持ち帰れるか。引っ掛かり・落下・復帰やFPSを記録。
4. 次にStudio **2クライアント**でRED/BLUEが正しく分配され、従来の得点・役割・捕縛・復帰・勝敗を妨げないことを確認。
5. 実Androidの横持ちでHUD重複、タッチ操作、敵/卵/天空入口の視認性、FPS、もう一度遊びたいかを採点する。

## ガード
全作業は隔離branchの新しいhand-offフォルダと固有CIのみ。#220公式RC、main、他作者の正本、ユーザーWindows PC、Roblox本番/有料機能、P0A/B/C/CAS、既存Automationの変更なし。正式S1完成率は最後の75/100、FUN_NO_GOのまま。最終採否は#250、正式RCへのSource採用は#220唯一writer、OWNER Studio実測まで採用済を名乗らない。
