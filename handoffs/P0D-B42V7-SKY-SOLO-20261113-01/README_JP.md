# B42＋無双V7＋天空城｜1人でStudioを試せる非公開版

2026-11-13 JST｜P0D-FUN-H1-001｜独立ソース・試遊用、正式RC未採用

## 修正した本物の詰まり
前の42-Luau統合Gameは `Config.MinPlayers=2` と赤青チーム両方がいることを、LOBBY→COUNTDOWN・COUNTDOWN→ACTIVE・ACTIVE中のTEAM_EMPTYで厳格に検証する。Windows Roblox Studioで1人の通常Playを押しただけでは試合の内部に入れず、卵やFirst90や天空城を正しく試せない。

本版は `RunService:IsStudio()` かつ `Players:GetPlayers()` が**ちょうど1人の本物の参加者**かつ既存の RED/BLUE どちらかに配属済みの場合にだけ、同じGame内のLOBBY/COUNTDOWN開始とACTIVE時の空き敵チーム扱いを許可する。1人試合かは開始時にラッチし、元々2人で始めた試合から1人が抜けた場合には従来のTEAM_EMPTY判定を維持。非Studioの場合の「2人以上・赤青両陣営」の本来条件を一切解除しない。偽プレイヤー/ボット/新Remote/別Gameは追加しない。

## 現物・源
- 既存 #219 作者の本物のB42+無双V7+天空城42-Luau Rojo一体版 `a3dfc9b98f22b8edf0a7d0d978d65b1072aed933` をイミュータブルにチェックアウトし、作者のアセンブラで再構築。元原本の社外未公開Sourceと別作者のRCには書き込んでいない。
- 41/42スクリプトは**バイト同一**。唯一 Game.server.luau を、完全原本SHA256 `81bc7a05ec0ab613c61f6030966dfeae7eab0c04122325f2a50eadf512d1a9c2` から、修正版SHA256 `4b17afecb16bb1c394603eae5bb17d7dac354ee0ade7e5dc16d3a3b8383b24f2` へ。天空城 / H1FunWorld・無双 V7 / MusouHorde・First90ガイド・卵得点・成長/進化・保存は作者原文のまま。
- 独立版の**本物のRojo出力 .rbxlx** SHA256 `45329aff9e60b1063296cb2c84af8566614a009754f2f676bf73509fd88ea6db`、407212B。GitHub Actions元生成アーティファクト `14025701485`。ローカルXMLプレビューとは別バイナリで、含まれる42/42のLuau原文は精密一致。
- 本物のCI **[run43401844661 COMPLETED SUCCESS](https://github.com/kk051780/toy-wars-factory/actions/runs/43401844661)**、元Author固定commitアセンブラで42ソース再現、実Python源/非Studio負例33件PASS、固定Luauネイティブコンパイラ42/42 PASS、固定Rojo 7.7.1/42原文完全一致・Game1・World1。別ローカルの本物の元Place/修正Place＆状況表42/42 Python PASS。

## Windows所有者のための試し方
1. 本チャットで配布の `P0D_B42_V7_SKYCASTLE_STUDIO_SOLO_ROJO_PRIVATE.rbxlx` をWindows Roblox Studioで別の未公開Placeとして開く。**既存の進行中のPC Placeを上書きしない・Roblox公開しない**。
2. `Test → Play` で1人入る。設計どおりなら、カウントダウン経由でACTIVEに入る。試合に入った時刻とStudio Outputの警告・エラーを記録する。
3. 赤なら敵側の青卵を取得し、天空道～高さ32の天空城を通り、赤の元の納品台へ戻す。案内90秒・中立敵/精鋭・攻撃ダメージ表示・獲得XP・進化も確認する。1卵/5卵モード双方を比較する。
4. 次にStudio `Test → Start Server + 2 Players` 等の2クライアント機能で、RED/BLUE対戦が元どおり起動・得点・勝敗・再戦できるか確認する。Android横画面FPS/操作/HUDは別検証。
5. 1人でも再現不能なら、Output全文/スクリーンショット/卵所持・得点挙動を #219 企画室へ報告してREVISE。**Studio実機結果をこのソース検査から捏造しない**。

## 前提と制約
これは**Roblox Studio内の仮想的な1人試合を認めるだけ**。本番1人オンラインプレイ対応ではない。試合開始可能でも、実環境で得点・進化・天空島の物理動線が作動した保証はまだない。本番2人対戦・スマホ・面白さについてはOWNER実測まで全てNOT_TESTED。元S1公式RCのS1 75/100、FUN_NO_GO維持。正式採用は #250 PRODUCT SELECT 後に **#220唯一RC writer** が安全差分で行う。

既存main、別作者のRC、P0A/B/C CAS、既存5自動化、Roblox公開/課金、PC/Codex実行は変更していない。

## ステータス
独立スライスの作業G1 claim/G2固定元証拠/G3Studioソロ差分/G4native+Rojo実検証/G5オーナーへの実ファイル引渡しは完了。G6 OWNER 本当のStudio/2client/Android/FUNは未実施。スライス進捗=5/6（83.3%）は**S1ゲームの完成率ではない**。
