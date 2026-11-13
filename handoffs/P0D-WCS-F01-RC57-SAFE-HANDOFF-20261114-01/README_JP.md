# P0D RC57 → WCS-F01/C01 安全受け渡し

**SOURCE ONLY / 正式RCは未変更。** 完成度75/100・FUN_NO_GOは従来値を維持。

## 今回の実成果

- 正式RC固定HEAD `34d6d384d04ba1d4a394331a3e5c74f798e57a22`、同一HEAD GitHub Actions [43508562967](https://github.com/kk051780/toy-wars-factory/actions/runs/43508562967) SUCCESS。現57/57 LuauとRojo source-exactが成功した後に作った**追加機能ソース**であり、現RC自体には未搭載。
- `src/WCS_CrystalCanyon.server.luau` は、RC56時代の浮遊峡谷/実物理進入路を再利用し、#295の安全修正済み作者本文（Git blob `3edcb19d91de509afd3de227cbfbca5d75125ec2`）を**一回だけバイト一致で埋め込んだ**独立Script。結果のGit blobは `9b891ae8b0dd579ccf1cd477b8b012e03415c0b0`。
- ゲートが占有判定するのは本当の閉鎖部分（ローカルX±3.5、Z±8）、閉鎖時に4秒クールダウン開始。橋の別部分での待機による無期限開放を抑止。14秒開放・左右2モグロン・常設迂回路・転落復帰・2物理スロープとレールを保持。
- Source GitHub再取得で修正済み作者本文完全一致と13項目構造検査PASS。別途作成時に原本2点と16/16条件を実照合。Python負例テスト12件は**ソース作成のみ、実行未確認**。新しい58番目のNative Luau／Rojo／Roblox Studio／Android／FUNは**未検証**。

## #220 唯一のRC担当への次の一手

1. 最新 `rc/p0d-s1-kids-rc01` HEADを再取得し、最低57本の既存Game/Remote/Store/ScoutSpecies/SavedBEAST/WEAPONを絶対に旧ビルドで置換しない。
2. `WCS_CrystalCanyon.server.luau` を**独立Server Script 1本だけ**既存 `ServerScriptService.TrapRaidersS1` に追加。作者の古い `CrystalCanyon.server.luau` を重複追加しない。
3. `WCS_F01_C01_FLOATING_CANYON` を標準fastlaneに独立スイッチとして登録。OFFならこのScriptを完全省略し、元57本を再現する。Studio内だけ実行。SkyV5物理道がなければScript自体が退出。
4. 同一新HEADで **58/58 native Luau + source-exact Rojo + no second Game/Remote/Store + feature OFF rollback + 原ソースSHA**を確かめ、成功時だけ#250のRC採用へ更新。実機2client/Android/DataStore再ログイン/OWNER FUNは初回公開前の一括ゲート。

> **重要:** 旧RC56 + WCSを作った57本の私的Placeファイルを、最新RC57へそのままコピーしない。現在の保存魔獣進化とスカウト3種の進化/戦闘を失う。

作業ブランチは独立 `feature/p0d-wcs-f01-rc57-safe-handoff-20261114-01`。#293/#295作者ブランチ、#220正式RC、main、公開・課金・Automationsは一切変更しない。
