# P0D private60 — WCS + 7職PvE + 1卵リレーの実ソース結合候補

**SOURCE / PRIVATE CI候補のみ。#220正式RC・main・公開・課金は未変更。**

- 正式RC57 `34d6d384d04ba1d4a394331a3e5c74f798e57a22` を基盤とする PR #305 (WCS + SevenJobs) の59本に、[PR #296](https://github.com/kk051780/toy-wars-factory/pull/296) の原作者 `PATCH_OPS.json` (9 Game + 6 HUDの厳格アンカー) と原作者ポリシー Git blob `ef9b65bd6520231f299f21c5cfe2aa250798c8d0` を適用する。
- 7職業技と卵リレーはどちらも既存の唯一のGame/HUDを書き換えるため、単純な古い `.rbxlx` の上書きは禁止。59本の**現物Game/HUDへ固有アンカーを1回だけ照合して**差分注入する。重複・ソース変更・曖昧アンカーなら早期拒否、旧59を保全。
- Classic 1卵のみ有効・5卵モードはfail closed。serverの卵所有者/2人の運搬情報のみを変更し、卵得点/HP/Store/Remoteやデータ保存への新規権威を追加しない。
- ソースを組み込んだだけで勝手に試遊開始しない。**Studioで起動前に** `ServerStorage` へ BoolValue `P0D_RC_ENABLE_EGG_RELAY_CLASSIC` を作って `Value=true` の場合のみ起動。未作成・falseはOFF。ビルド側は `FEATURE_SWITCHES.features.EGG_RELAY_CLASSIC_V1.enabled` で独立ON/OFFできる。
- GitHub Actionsが新HEADで実行し、既存59本のうちGame/HUD以外の57本がbyte不変、EggRelayPolicy1本追加、単一Game/Remote/Store、ネイティブ全60本 + Rojo source-exact 60を確認した場合だけ**隔離RC60候補合格**とする。実機2client/Android/owner FUNは別。
- 競合でQA落ちした場合、違う場所へ無理にパッチを入れず、#297・#296作者の差分を精査した上でひとつのGameに再配置する。重複報酬・二重入力が疑われたら受入禁止。
- `P0D-007`卵リレーは既存企画行のまま SOURCE。WCS `P0D-059`も SOURCE、7職PvEは一部機能であり7職PvPフル完成とは数えない。現正式RC導入 **21/58**、S1公式過去監査75/100/FUN_NO_GOから加点しない。

## 原本
- [PR #305 同居59](https://github.com/kk051780/toy-wars-factory/pull/305)
- [PR #296 卵リレー作者](https://github.com/kk051780/toy-wars-factory/pull/296)
- [Issue #220 唯一正式RC](https://github.com/kk051780/toy-wars-factory/issues/220)

このブランチは試作品の保存・独立CIだけを行う。main push、正式RC書込、勝手なmerge、Roblox公開、課金、PC操作、追加支出は禁止。
