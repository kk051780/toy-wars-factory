# P0D卵リレー：最新正式RC55実体への最小差分リベース（未統合）

- 出発点：#220 正式RC `SAVED_PVE_MASTERY` 追加済み **55-source** Actions [43501488524](https://github.com/kk051780/toy-wars-factory/actions/runs/43501488524) の本物の `.rbxlx`（artifact 14074311951）、SHA256 `e439aa5d7372e77b0949bb681ed7342485a541c3738f7c7aceede1b6ea23b8c0`、成功対象固定HEAD `0dd7f4418d06200e40688c79c8290745cb56834d`。
- 旧54向け作者の**同一2パッチ**を、新しい55本実ソースに `patch --fuzz=0` で適用し直せることを**実測**。最小差分で隔離56-source Studio XML候補に再構築し、SHA256 `d9b594bc869fee10dd2d2f7fadfb316f655fedc1316425e639ab437dd8c77afc` を確認。
- **元55の53本はバイト同一**（`SavedPveMasteryPolicy`・`SixSkillAtomicProfile`・`PersistentHatchStore`・秘境/世界/敵・元HUD含む）。変更した既存ソースは**唯一のGameとH2FiveEggRulesの2本だけ**。新規作者pure `EggRelayPolicy` ModuleScriptを1本足す。Score/HP/XP/Save/Remote権威を増やさない。
- このターンの実行：新しい本物のRC55 XMLを使ったソース差分/負例 **Python16/16 PASS**。元H2Score+新relay本体のLua5.4互換実行 **20/20 PASS**（納品後の得点1回、5卵保存、相手チーム拒否、二重渡し拒否、タイムアウト）。ゲーム全体を本物のLuau native56/56コンパイル/Rojo/Studio 2-clientで動かしたとは**言わない**。元の公式RCは改造していない。
- 実ファイルが必要なら本ChatGPTターン内配布ZIPを利用。GitHub上の再生成器 `rebuild_current_rc55.py --original-place <実原本.rbxlx> --output <隔離出力.rbxlx>` と、作者専用 `../rc54_candidate/Game.patch`、`H2FiveEggRules.patch`、`../src/EggRelayPolicy.luau`、本 `SOURCE_LOCK.json` から構築できる。
- **並列重複に注意**：別作者の Draft PR [#296](https://github.com/kk051780/toy-wars-factory/pull/296) はCLASSIC 1卵用のGame/HUDパス案を提出済み、H2 5卵は明示的未対応。**両Gameパッチを重ねて導入禁止**。#220が安全性/操作UXを比較し、Game側は一方式のみ選ぶこと。こちらの独立した `H2FiveEggRules.relay` の保持者・卵version保存遷移は、その不足分として採用可能。
- OWNER V5：単一正式RCブランチ `rc/p0d-s1-kids-rc01` の唯一writerは#220。Studioで毎回試遊してからRC統合する旧方式は廃止。**現在のRC HEADから全ソース再組立＋本物Luau/Rojo一括CI＋可逆機能OFF**が必要。実Studio2client/Android/FUNは**公開前**の未達ゲート。
- このブランチの原本候補は公開・課金・main/merge・他作者改変をしていない。公式最新の実RC採用率は #220 による **19/56 (33.9%)**（この卵リレー未カウント）。S1発売準備の旧品質評価は75/100、FUN_NO_GOを維持。
