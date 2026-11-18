# GQ8 P0 | 最新正式REAL59の対戦ホスト未起動を修復

**FEATURE_ID:** `GQ8_REAL59_HOST_AUTOSTART_P0_20261119`

2026-11-19 JSTの最新正式RCは `rc/p0d-s1-kids-rc01` HEAD `38d11f0bf311491ba76fe03f818948e5d4b06889`、**REAL59 private companion**（旧Real55 + 4本 HUD/Fog）、[同HEAD GitHub Actions #44401178585](https://github.com/kk051780/toy-wars-factory/actions/runs/44401178585) SOURCE/Rojo成功。正式アーティファクト #14473365566 を実ダウンロードして静的解析。59本の中で **唯一の本ゲームHost `ServerScriptService/EGGRUMBLE_LobbyCastleModesPreview` が ModuleScript であり、他の58本がrequireしていない**。実セッション生成・ロビー・TEAM/BR入場のトップレベルコードは自動起動されず、従来のSource/Class検査成功を「遊べる」と報告できないP0不具合。

## 実修正

- `repair_real59.py` は本当に公式Real59 Placeにシリアライズされた**全59 Luau Source**を読取り、各実体のRojoクラス/ルート/SHA256を **公式 `GQ828_REAL59_RECEIPT.json` の59エントリ**と照合する。ファイル名から推定せず実バイト単位の照合。
- OFF59用Rojoプロジェクトと全ソースを復元。元Hostバイト列をそのまま `.server.luau` に複写し、**同じRoblox HostルートのクラスをModuleScript→Scriptのみ変更**。55本の旧機能とREAL59追加HUD・Fog4本、計59本すべて保持。58ルートは無変更。新たなRemote/Combat/Host/Store/課金なし。
- `test_real59.py` は実公式PlaceをRED negative fixtureとし、唯一のHostクラス修正、原ソースSHA保持を検証。CIはRojo 7.7.1固定でON59 PlaceがScriptになること、OFF59 Placeが元の実公式59 Placeと**バイト完全一致**することを検証。実Studioテストではない。

## 採用/保護

- 正式採用ではない。#220 B認証writerのみがfresh expected_SHA nonforce CASで単一`rc/p0d-s1-kids-rc01`へ採用し、同NEW-HEAD SOURCE/Rojo/OFFの証跡を残す。#839命名ルール、#810最新指示に従い他の候補REAL56/REAL57を落とさない。
- Roblox公開、mainへの書込、課金・支出、Work/Codex利用禁止。
- 実機合格は `STUDIO_SOLO=NOT_TESTED`, `STUDIO_TWO_CLIENT=NOT_TESTED`, `ANDROID_15MIN=NOT_TESTED`, `FUN=NO_GO`。試遊でロビー→職選択→TEAM/BR→中立兵KO→卵奪取/納入→城破壊→終了/再戦を実測すること。

**注意**：今後RC HEADが再更新されれば、本固定基準に対するCIは意図的にRED。最新正式RCに再合成し、以前の版へ戻して「合格」にしない。
