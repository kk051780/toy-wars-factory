# EGGRUMBLE V3 #470 独立の「構想67件 × 8領域」品質ゲート

このPRはゲームの実装や原作者ソースを複製しない。正式RC writer #220の代わりに公式RCへ書かない。
既存 #471（競合比較）、#490（実行制約）、#491（源来歴）、#493（ネイティブ挙動）、#521（Rojo混合）に対し、
**企画室の FEATURE_CATALOG 全件を現RC事実と誤同一視しない設計追跡**だけを固有担当とする。
ソフトCLAIM: #218 comment 6909927578; CLAIM_GRANTED は確認されていない。

## 対象・確認できた事実
- 正本: RC HEAD `d2f3ed1a47558fdaf07be0181c83c698bdb2ce34` の
  `rc_fastlane/FEATURE_CATALOG.json`（Git blob `0d125d45fb5d2724539e0e119a586024aa47818b`）。
  **67行 / 旧カタログステージ RC31, SOURCE26, IDEA10**。これはV3の現在の採用数を意味しない。
- #220公式RC78 同HEAD source build [Actions 43677046865](https://github.com/kk051780/toy-wars-factory/actions/runs/43677046865) SUCCESS。
  **Studio/Android/OWNER FUNは未測定**。
- V3元ゲーム #482 HEAD `fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9` は別の**DRAFT**。
- 漏れの例: 原作者の `EGGRUMBLE_SevenRoleCombat.luau` は魔法使いの生存者回復 +25 のみで、
  `characterOf` が死者を除外するため蘇生未実装。別PR #510 は回復の壁LOSであり蘇生ではない。
  #482の原作者に同一PR内で実Luau/Studio修正を求める。こちらでは役割本体をforkしない。
- 建築士の真正壁・橋は元#482にはなく、既存独立 #522 が候補を制作中。
  他の既存担当 #485/#489/#494/#500/#501/#503/#504/#517/#518/#520/#523/#524 を再利用する。

## ファイル
- `DESIGN_TO_GAME_TRACE_MATRIX.json`: 67特徴行、8領域、正本のreleaseステージ、現RC HEAD、
  候補の実ソースGit blob、エンジン/端末/美術/競合/OWNER証拠、GAP種別、担当/次手。
- `check_trace.py`: **実行可能な**整合ゲート。ID欠落・重複・8領域欠落・古いRC SHA偽称・
  7職のS2+例外扱い・根拠不明の正式RC採用/OWNER合格の水増しをNGにする。
- `test_trace.py`: 9件の負例を含む source/trace 回帰テスト。
- 専用Actions workflow: 読み取りのみ。ソースとカタログの混同を即検出。

```sh
python3 quality_gameplay/v3_design_trace_20261116/check_trace.py
python3 -m unittest discover -s quality_gameplay/v3_design_trace_20261116 -p 'test_trace.py' -v
```

## 現在の厳密な進捗（このPRは実ゲーム変更ゼロ）
- 設計カバレッジ: 67/67企画・8/8領域**行が揃っただけ**。
- 今回追加した本体Luau/3D: **0**。既存原作者のゲーム実装や修復件数に加算しない。
- V3正式RCへの新規採用を確認したFEATURE: **0**。現在の公式RC78と混同しない。
- V3 OWNER受入: **0**。ART/FUN/Android はNO_GO。
- B #220への引渡し: source-only行を確定 → #482等原作者修復 → CLAIM/安全確認 → nonforce CAS
  → 同HEAD公式Rojo/Native/Place ZIP bytes → Studio/Android → OWNER実機確認。
- 巻き戻し: このフォルダと専用workflowを削除するだけ。Game/RC/課金/公開は一切変更しない。

**このPRをRCへ丸ごとmergeしない。** #220のみが必要な品質チェックを正式RCへ source-selective に導入する。

## 第2段：実際の原作者5 Luauソースを読む負例プローブ（2026-11-16）
旧版の67件表だけを充足させても、7職が本当に原案どおり動くことは確認できない。
`probe_v3_author_source.py` は #482 固定HEAD から実ソース5本を取得して
それぞれ**Git blob SHA-1**と一致するまで、開発中の原作者 branch や偽のfixtureを受け入れない。
そのうえで **キャラ・地形・戦闘・城・中立・アイテム・ロビー・バランス**
に紐づく原作者実Luauのアンカー存在を8/8領域で確認する。
これは**文字列ソースの存在確認**であり、Studioで技能が機能するという主張ではない。

ソースから確定した8件の構想差分を同じ `DESIGN_TO_GAME_TRACE_MATRIX.json` へ更新：
P0D-008/010/011/012/013/014/015/019。MAGE蘇生なし、
NINJA透明は属性のみ・レンダリング不明、TRAPPER設置罠なし、
BUILDERの実壁/橋は元作者ではVFXのみ（#522独立候補）、
BEAST召喚Follower/乗物なし、ZOMBIE実AI指揮なし。V3原作者の現プレビューが
各能力の完成物であると数えてはならない。現原作者ソースと異なる結果が出たら
**テストNGとして差分精査**し、成功に見せかけるために固定字句を書き足さない。
原作者の実修正・本人試遊・正式RC採用により初めてGAPを閉じる。

専用Actionsは固定#482原作者HEAD `fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9` の
5 Luaを読み取り専用でダウンロードし、再検査する。
`test_source_probe.py` は8つの偽証/欠落例を試す。
本PRの新しい実ゲームLuau/3D書き込みは **0**。


## 第3段：公式RCのLIVE同一HEAD認証（2026-11-16）
- `check_rc_freshness.py` はGitHub APIから**正式RC branch HEADと公式Actions runを別々にGET**。
- 本追跡表の40桁HEAD・run URL/ID・実runのHEAD/branch/repository/status/conclusionを全て突合する。
- 旧HEADの成功runや別branch/別repoの成功runを最新RCの成功証拠として使えない。RC更新時には台帳のピンを更新し再検証。
- アーティファクトZIP容量、Studio・Android・OWNER FUNはこの検証で測れないためUNKNOWN/NO_GOを維持する。
- `test_rc_freshness.py` は10種類の偽証・競合更新・失敗状態を拒否する負例テスト。
- **本作業は既存#526所有フォルダと読取専用CIだけ**。正式RCへのゲームLuau新規採用数0、主Game/HUD・他担当PR無変更。
