# TRAP RAIDERS S1 V6 — 本物のMapBuilder＋Guardian罠＋Game.server結合QA

固定 S1 RC: `1263a03701211a652b99b91d2339575dc8104eff`

独立QA packet: `P0D-S1-V6-REAL-MAP-TRAP-COMPOSITE-20261112-01`
既存の独立検証: 実マップ＋旧Game 5dc6 → `b2ae7828b641ab5acccc279117d36c6c413b543b`（前バージョンに限定）。罠の個別QA → Issue #226（MapBuilderはフェイク）。

## 今回の新しい検証境界

実際の最新版 Game.server / MapBuilder / S1Rules / LobbyTeamRecovery / Config / S1TrapRules の **6本を原本のまま** 固定Gitコミットから取得し、バイトSHA1 Blob一致を確認。以前の実マップ検証器を固定バイトで読み出して拡張する。Luau内では本物のGame.serverが本物のMapBuilderが生成した卵・城・配達場・スポーンPartとPromptにアクセスし、本物のS1TrapRulesでGuardian罠の設置・解除・減速を判定する。

拡張するのは外部Roblox Instance/Players/Servicesのテストダブルと、Luauの検証アサーションだけ。元Game/Map/Rules/TrapRules source fileは変更しない。本番Roblox Studioを模した主張はしない。

### 特に検証すること

- 旧マップが生成する27 Parts・3 Folderに対しV6の罠Folderが正しく付いて **4 Folder** となる。
- 青Guardの卵の正規座標を使用した設置拒否。クライアントからの偽座標が無視され、青陣地の正しい座標にのみ罠が生成される。
- 罠が既存3Dマップの子として配置され、Raycast・移動を妨げる衝突体にならない。
- 敵RAIDERだけ移動速度が低下し、同陣営Guardianは遅くならない。時間経過後復元される。実マップ・試合勝敗・再戦が壊れない。
- 地図改ざん・不正Prompt・危険な罠クリアランス除去・クライアント座標信頼・Raycast遮蔽の **5つの不正変異** が検出できる。

### 実行

```sh
python3 handoffs/P0D-S1-V6-REAL-MAP-TRAP-COMPOSED-20261112-01/tools/run_v6_game_map_trap.py --selftest
python3 -m unittest discover -s handoffs/P0D-S1-V6-REAL-MAP-TRAP-COMPOSED-20261112-01/tests -v
python3 handoffs/P0D-S1-V6-REAL-MAP-TRAP-COMPOSED-20261112-01/tools/run_v6_game_map_trap.py --repo . --luau /path/to/native/luau
```

正規ネイティブLuau CLIは公式ソース `luau-lang/luau@f46d879e28302a430029304f7f6a162aed66f103` を取得してGitHub Actionsでコンパイルする。結果はCIの成功ログ・元ソースSHA照合・危険変異検知に限る。**Studio 2client・スマホ・性能・実人間の試遊・本番公開は別ゲートでNOT_TESTED**。進捗スコアは公式 #220 の監査を転載し、独断で75%を変更しない。

担当 #228 https://github.com/kk051780/toy-wars-factory/issues/228
共有 #218 https://github.com/kk051780/toy-wars-factory/issues/218
統合 #220 https://github.com/kk051780/toy-wars-factory/issues/220

禁止: main直書き、公式RCへのwrite、無承認merge、Roblox本番公開、課金/支出、Windows Codexの逐次試験、保護中P0A/B/C・自動化5件の改変。
