# P0D-EGG-RELAY-001｜5卵モードだけの安全なパス遷移・V2

## 位置づけ

これは **#296 の CLASSIC（1卵）担当と重ならない、5卵側の補完部品**です。#296 の Game/HUD と、以前のこの作者の rc54_candidate/Game.patch は **同時に適用しない**でください。唯一の正式RC writerは #220。どちらか1つの Game ハンドラを決めた後、この H2-only パッチだけをその Game ハンドラに接続します。

- **変更対象1ファイルのみ**：既存の `H2FiveEggRules.luau` に `Rules.relayWithVersion` を追加。既存の `new/pickup/drop/deposit/advance/assertConserved` は**完全にバイト同一**。
- 元の公式RC55（保存済み武器熟練度まで採用）成功証拠：HEAD `0dd7f4418d06200e40688c79c8290745cb56834d`、Actions [43501488524](https://github.com/kk051780/toy-wars-factory/actions/runs/43501488524)、本物Place SHA256 `e439aa5d7372e77b0949bb681ed7342485a541c3738f7c7aceede1b6ea23b8c0`。
- 同Placeから抽出した実 H2 元ソース SHA256 `cdfb7c66f2857f7fba683869bc9fe94edd64d59730ecc0730e46969e77323aca`、Git Blob `0999d69391c176b9b95b04c5444d822e63d7ce04`。
- `H2OnlyRelayV2.patch` Git Blob `68f3df613ad548ab56e755adf91d797a979e8552`、SHA256 `19135a20ad8de703e68177b7d4c4764f9198caa2395d4bacdc5631a177e99777`。元ソースへの `patch -p1 --fuzz=0` 実行PASS。結果 H2 SHA256 `89e2f07e0000bb6338e44ad41ee812b054226718161136443e64382028558b00`、Git Blob `a3cc4894db6db04f760e1cd615c2ec5c9444734f`。
- `patch -R -p1 --fuzz=0` で **元ソースを1バイト単位で完全復元PASS**。元公式RCのGame/Score/Store/Remote/他スクリプトは書き換えていない。

## 遷移API
```luau
local ok, reason, newSeq = H2Score.relayWithVersion(
    h2ScoreState, eggId, expectedTransferSeq, fromUserId, toUserId, currentTeam
)
```

成功条件は、現ラウンドが有効、固定5卵ID、正の実ユーザーID、同一人ではない、想定した卵IDと現在の持主が一致、受取人は手ぶら、現在の卵 `transferSeq` が呼出側の期待値と一致、`controller` がチームと一致、全5卵の `Rules.assertConserved` が正しいことです。不正な世界状態なら**変更前に拒否**。成功時だけ `carryByPlayer[fromId]` を消して `carryByPlayer[toId]` をセット、`egg.holder` を更新、`transferSeq` と `events` を1増加。**得点・保持秒・卵の個数・HP/XP/保存は変更なし**。

この純粋処理は**キャラクターの生死、2プレイヤーのチーム、壁の衝突、射程、12秒のパスクールダウンを検査しません**。#220 の既存唯一Game側でサーバー情報を検証し、その後に本処理をyield無しで呼ぶ必要があります。信用してはいけないクライアント引数や別Remoteを受け取る設計にしないでください。

## 29件の実行検証

固定元の本物 H2 ソースにパッチを適用し、Luau特有の型注釈と compound assignment のみLua 5.4互換に変換した実ルールを、ローカル `liblua5.4.so.0` のC APIランナーで**29/29 PASS**。うち通常パス/二重得点/5卵保存/所持時間/イベント/失敗で不変/他人卵/旧version/無効ID/NaN/ラウンド終了/データ破損/二重所有/再送/納品のケースを実行しました。検証実体・生成スクリプトはオーナー向け同ターンZIPに格納します。

**これはLuau CLI / Roblox Studio の実行証拠ではありません。** 物理Promptと実Game配線、２クライアント、Android、OWNER FUN、正式RC CIは未実施です。正式RC採用・公開を宣言しません。

## #220へ最小引継ぎ

1. 最新正式RC HEADを再確認（他班が並行で進めている）。既存のH2原文SHAが上記と異なる場合は**自動パッチ中止**・再照合。
2. #296 の Game/HUD 1卵パスを先に採用するなら、**Game改造を重複させない**。同一Gameで5卵モード分岐に `H2Score.relayWithVersion(m,eggId,transferSeq,fromId,toId,side)` を追加し、返値が成功したときだけ Gameの既存 `carry[Player]` とVisualを一致させる。成功時にscoreやXPを加算しない。
3. 運搬者・受取人が存在／同チーム／生存／未拘束、水平8垂直4、fresh raycast LOS、卵ごとの12秒cooldown、ラウンドepochを既存Gameのサーバー権威で確認。元H2 `carryByPlayer` と `transferSeq` を信用して処理する。
4. 機能スイッチ `EGG_RELAY_V1` で完全OFF/従来の55-scriptへ切戻し可能にする。元唯一Remote/Store/Score保護、全体Luau native+Rojo SourceExact CIを#220独立RCで一度通し、初めてRC採用を台帳に追加。
5. OWNER V5は機能ごとのStudio試遊をRC採用の前提としないが、**公開前の人間FUN、2client、Android試遊は未達**のまま維持。

本レーンの旧 `rc54_candidate/Game.patch` と `rc55_rebase/rebuild_current_rc55.py` は #296 と競合する代替案なので、**以後はH2-only V2だけを第一推薦**。S1発売品質の最後の公式評価75/100 / FUN_NO_GOは不変です。


## 追加検証：最新RC56の本物ソース互換性（2026-11-14）

- 正式唯一RCのSAVED_BEAST_EVOLUTION採用済み初回成功コミット `947cddb5351ba95b9b27597b9ec1828a8297cd66`、本物Actions [43504336646](https://github.com/kk051780/toy-wars-factory/actions/runs/43504336646)、artifact 14075771698 から実`.rbxlx` を取得、SHA256 `3b8df96e32433a645a957604e7f50062a9ffd2e34831d8e6ba21f7ab2bfabc5c` と一致。実54→55→56本のうち**現行56本**を読んでH2原文 SHA256 `cdfb7c66f2857f7fba683869bc9fe94edd64d59730ecc0730e46969e77323aca` がRC55と**バイト同一**であることを実証。
- H2-only patch `H2OnlyRelayV2.patch` を最新RC56の抽出原文へ `--fuzz=0 --dry-run`→本適用し、結果SHA256 `89e2f07e0000bb6338e44ad41ee812b054226718161136443e64382028558b00` の完全一致PASS。
- **結果：最新RC56のBEAST進化/SAVED_PVE保存レベル/修行/秘境、Game、Store、Remote/HUDを変えずに、本H2純粋遷移だけを組み込める正確な差分が成立。** ただし実ゲームにパス用のGameハンドラを追加しなければユーザーはまだ遊べない。公式RCに本差分を適用した事実はない。
- 別レーンPR #296は通常1卵Game/HUD対応。Game本体は一本の統合だけを選ぶ。現在の正式企画到達率は別途 #220 の報告が正本であり、本候補では加点しない。
- この検証の固定証拠は `RC56_COMPATIBILITY_PROOF.json`、再実行可能なオーナー用ZIP `P0D_H2_EGG_RELAY_V2_READY_FOR_220.zip` に保管。


## V3：ネイティブLuau検証を独立CI化（2026-11-14）

正式RC56の5卵ルール原本の固定Git Blob `0999d69391c176b9b95b04c5444d822e63d7ce04` を**GitHub内にバイト同一のテストFixture**として配置しました。以前のH2-only差分 `68f3df613ad548ab56e755adf91d797a979e8552` は未変更です。

- `tests/H2FiveEggRules.AUTHOR_LOCKED.luau` — 元H2正本の完全固定ファイル
- `tests/native_h2_relay_cases.luau` — **48件の本物のLuau構文テストソース**。5卵×2チーム×3項目=30件、18個の独立負例・異常系。実ユーザー権限/距離/LOSは既存Game側の責任であり、純粋な5卵ルール内には捏造しない
- `tools/build_native_h2_runner.py` — 元ソース/新パッチ/48テストそれぞれGitBlob固定、fuzz=0で元ソースのパッチ適用→結果GitBlob確認→逆適用で原本100%復元を確認してから、**本来のLuau原文のまま**1つの実行ソースを出力
- `.github/workflows/p0d-h2-relay-v2-native-20261114.yml` — 作者隔離branch専用、Luau上流 `f46d879e28302a430029304f7f6a162aed66f103` を固定ビルドし、`luau-compile` / `luau`で48件実行、標識 `P0D_H2_RELAY_NATIVE_48_OF_48_PASS` を確かめる
- `NATIVE_48_CI_RECEIPT.json` — Source/CI/Roblox Studioの合否を別管理

**このターンの実測**：Pythonで元のRC56ソース/パッチの原本GitBlob・fuzz=0適用・厳密逆パッチを再検証（3/3 PASS）、従来実H2ロジックのLua5.4互換29/29を再実行してPASS。GitHubにおける48テストの存在と固定SHAは確認済み。

**未確認**：新CIの実行IDと成功結果、ネイティブLuau実行48/48、最新全RC内56+スクリプトRojo、Studio2client/Android/FUN。PRのみを返すGitHub commit-run照会結果0件を、push CIが失敗/未実施だと断定しない。**ここまでで正式RCへ採用済みという報告は禁止**。最新RCの唯一Game/Remote/Storeの改造は#220だけが行う。
