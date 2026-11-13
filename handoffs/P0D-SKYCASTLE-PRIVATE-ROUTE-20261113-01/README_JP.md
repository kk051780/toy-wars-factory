# P0D H1天空城 — B42非公開・物理ルート試作

2026-11-13 JST / TRAP_RAIDERS (EGG RAID RUMBLE) / P0D-FUN-H1-001

## 目的と現物
直近のOWNER試遊で「陳腐」と評価されたS1を改善するため、B42 First90に**天空の寄り道と帰還路**を組み込み、卵運搬・追跡・護衛の遊びとして評価できる隔離候補を制作した。原B42はコミット `837853e66278e38bb79f6399c3e8bfc9a2403be6` に対応する未公開Rojo Place SHA256 `2b218936d5559680f21498fb190d79dfbd0b26b8671e4f71fe62d66efec008be`。今回の独立版は SHA256 `40666ff599f5ba0a88976688c0c752cbc9839ad02095fbd07f1ec0d62b2f233b`（402916 bytes）。元の42スクリプトのうち `H1FunWorld` **のみ**を変更し、残り41スクリプトのLuau原文はすべてバイト同一。今回のLuau原文のGit Blobは `0a6360392f4384dc2f0ab1e9afc1d840d66a22b8`、SHA256は `1955d51a1fb4d1d59639e93aa8d72b909acfe64d790ea8e81ea2f41161f17768`。

## ゲーム内で変わること
- 元の中央天空通路（高さ16）から赤青双方が利用できる登り道を2本新設。坂率が元の `path()` の0.55以下。
- 以前 `CanCollide=false` の遠景だった `FLOATING_SKY_ISLAND` を、上面Y=32の物理床（50×8×20 studs）に変更。外見の塔・光は装飾のまま。
- 島の両側から元の赤青スコア台近傍（X±82, Z22）へ戻る坂を2本追加。卵の新規生成、別の勝利条件、瞬間移動、課金通行権、職業制限は一切なし。
- 既存の `Game`・`MapBuilder`・First90・Horde・卵のサーバー権威・得点・HP・進化・XP・保存・Remoteは変更していない。**第二のGameや第二のH1_FUN_WORLDを作らない**。Studio限定ガードと従来の世界単一性assertを保持。

## 検査と限界
元のB42実ファイルから生成した独立Placeと原本をXML解析。実際に **28/28 Python元ソース・新ソース・対称性・坂率・原権威非改変・負例テストPASS**。発行ルートの原点/到達点・既存城壁AABBへの保守的サンプル衝突を確認。ただしこれは**ネイティブLuauコンパイル成功でも本物のRoblox物理/地形動線の証明でもない**。現B42に既にある実験的ゲーム世界にのみ作用、元の#248別branchを混在しない。こちらのパッチは未公開ローカルB42の完全XMLコピーで確認済み。

## Windowsでの非公開試遊の受入
1. 既存のPC Placeをバックアップし、ユーザー受領の `P0D_B42_SKYCASTLE_PLAYABLE_PRIVATE.rbxlx` を**別の未公開Studio Place**として開く。Robloxへの公開・本番保存なし。
2. 出力エラー、天空入口、物理床、両側の出口、カメラ/ジャンプ/落下救済を確認。
3. Studio2clientで赤/青からそれぞれ **元の敵卵を取得→天空城を上り下りして護衛/追跡→元の自陣スコア台へ届ける→勝敗/再戦** を確認。単一卵・5個得点戦の両方を確認。
4. 実Android横画面で導入90秒の誘導とUI、移動・攻撃・卵運搬、表示、負荷/FPSを記録。陳腐か・再戦したいかも本人評価する。
5. 坂に引っ掛かる、出口付近の城/score-pad衝突、サーバーの卵保持・落下/境界バグやスマホ視界問題があれば `NO_GO/REVISE` とし、原B42に戻す。元RCへの取り込みは必ず#250正式採用→#220唯一統合者がsource-lock/全ゲームQAを改めて確認してから。

## GitHubの担当境界
本 branch `feature/p0d-skycastle-private-route-20261113-01` は `handoffs/P0D-SKYCASTLE-PRIVATE-ROUTE-20261113-01/**` の独立ソースだけを所有。#248 WORLD、#218 FIRST90、#288 Horde、#220 RC writer、main、既存5自動化とP0-A/B/C CASは変更不可。企画室は採用まで追跡するが、この納品自身は `SOURCE_CANDIDATE_NOT_OFFICIAL_RC`。公式S1の最後の75/100は変更なし、OWNER FUNはNO_GOのまま。

進捗V3: G1 claim PASS / G2 exact frozen input PASS / G3 single-script private Place PASS / G4 local source QA 28/28 PASS / G5 GitHub source SHA/manifest PASS / G6 actual Studio 2client/Android/human FUN NOT_TESTED. 自担当の5/6=83.3%、ゲーム進捗率ではない。
