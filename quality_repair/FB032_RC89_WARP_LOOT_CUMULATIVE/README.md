# FB032 RC89 — 既存のワープ拡張と壁越し拾得/攻撃防止を一本化

これは **実Roblox Studio Place** の SOURCE-EXACT private candidate。正式RCではない。

## 実際に統合したコード

真正親は、PR #481 の [Native86+Rojo86 PASS Actions #43754971010](https://github.com/kk051780/toy-wars-factory/actions/runs/43754971010) artifact #14178002762 に含まれる RC88 Place **846,753 B** / SHA256 `e207a79b777d3b0814ec9580bc9f7ffaffeb07581d6b1010ac89b2846c2accd8`。その `TrapperWarpService` は広域フィールド/床高さでの2端点ワープを実修正している。元の86本のうち **`ServerScriptService/TrapRaidersS1/StagePickupLoot` の本文だけ**を変更し、残り85本とscript class/pathを完全保持した。

`StagePickupLoot` にサーバー所有の同一LOSヘルパーを追加し、二つの既存不具合を修復する。
1. 拾得時、プレイヤーからペデスタルへのRaycastで閉門/壁があれば拾得を拒否する。元の10stud距離制限と死亡/陣営/卵/時刻などのGame権限は変更しない。
2. 疾風の槍/雷光の弩の射程強化で attack origin を前進する前に、元originから延長先までの実線分をRaycast。閉門/壁に阻まれた場合は元originを返し、既存の中立horde命中・遮蔽物判定へ渡す。

これらは別の旧RC86で確認済みのFB030 `StagePickupLoot` 実源修正を、**後発の本物のRC88に統合**したもので、既存機能の重複実装ではない。

## 成果物・検証

- PLACE: `P0D_RC89_WIDEFIELD_WARP_STAGE_LOOT_WALL_SAFE_PRIVATE.rbxlx` **847,767 B** / SHA256 `03bba976334b188897f4e771d04473229bd82a81db8f6a6fdc44a99d26a14bc9`
- 全86 Luau元class/path/Source元文字列照合。差分 `StagePickupLoot` 1源のみ、新 GitBlob `c4bce228571140913d9dc01aed39050a96addbcb`。
- Python 25/25 `test_rc89.py` source-exact XML、許可機能、wrong parent/二重patch/anchor drift等の負例検査PASS。
- `python3 build_rc89.py && python3 -m unittest -q test_rc89.py` で完全再生成。`extract_rojo.py PLACE SOURCE_LOCK.json /tmp/rojo` で86本の真のRojo treeとmanfiestを抽出。GitHub Actionsのnative Luau / Rojoを実行し合格記録するまでネイティブPASSは主張しない。
- 新Game/Remote、Store、HP/KO/egg/score ownerを作らず、元の7武器・AI・ゾンビ3体・風走り・城・卵戦・2端点ワープを保持。

## 未完・採用判断

[PR #476](https://github.com/kk051780/toy-wars-factory/pull/476)の**別系統** private FB020-029には、物理ロビー・4種拾得・7職X/C・魔法蘇生・建築士橋・魔獣騎乗がある。その完全な非公開実Place・5つの変更源がこの親RC88の86本に含まれると主張しない。PR #476のGame/HUD/他class-sourceをこの古い累積Placeで上書きせず、#220唯一の正式RC authorが最新HEADにsource-selectしてCAS統合する。

**現在**: SOURCE/LOCAL_QA PASS、Studio1/2・Android・FUN・ART・OWNER受入 NOT_RUN。正式RC/mainの変更、merge、公開、追加課金は一切行わない。Studioで門前の槍HIT、防壁の拾得拒否、広域ワープ、2client卵戦を実際に試す必要がある。
