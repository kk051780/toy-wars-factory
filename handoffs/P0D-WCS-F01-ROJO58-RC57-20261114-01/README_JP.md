# P0D クリスタル峡谷：正式RCへ渡せる実ビルド検収

**工程：SOURCE_Native58_成功 / 正式RC採用は未完了。** 2026年11月14日 JST

## 今回、実際に完了したこと

元企画室作者の [PR #298](https://github.com/kk051780/toy-wars-factory/pull/298) は変更せず、その子ブランチ [Draft PR #301](https://github.com/kk051780/toy-wars-factory/pull/301) で最新公式57本RCを一度組み立て、そのうえに**クリスタル峡谷を1本だけ追加**した。作者ソースGitBlobは `9b891ae8b0dd579ccf1cd477b8b012e03415c0b0`、#295の安全ゲート修正込み。

**実ビルド**：固定sourceコミット `6ad5a999413080a66e6ea9b73880d025024fd377` に対し、[GitHub Actions #43515233758](https://github.com/kk051780/toy-wars-factory/actions/runs/43515233758) が **completed SUCCESS**。ジョブ132195410935、ログ直接確認。元57本同一、作者Python負例12/12、OFF時元57とbyte-exact、実Luau58/58コンパイル、checksum固定Rojo7.7.1で新規`.rbxlx`をビルドし**Rojo埋込ソース58/58完全一致**。生成された[未公開Studio Place成果物](https://github.com/kk051780/toy-wars-factory/actions/runs/43515233758/artifacts/14079019166)も確認。証拠は `QA_REAL_NATIVE_ROJO58_SUCCESS.json`。

## 実際のRC受渡し条件

- **担当はIssue #220唯一の正式RC writer**。現在のRC HEADを再確認し、古いRC Placeを丸ごと置き換えない。既存Game/HUD/Store/Remote/ScoutSpecies/保存武器/保存魔獣/RealmHuntはソースbyte同一で守る。
- `rc_fastlane` の既存ビルダへ **元作者 WCS_CrystalCanyon.server.luau 1本だけ**差し込む。個別OFF `WCS_F01_C01_FLOATING_CANYON`を公式FEATURE_SWITCHESに設定し、元RCを再現できるsource lock・負例・Rojo検査も追加。**PR #301/298を全体mergeしてRC採用したことにしない**。
- 新しい**正式RC HEADと一致する**ネイティブLuau／Rojo／元ソース不変検査が緑になってからのみ登録台帳でRC採用へ。未登録の企画なら新しい一意の企画IDにする（既存P0D-058を上書きしない）。
- WCSはStudio限定で、`ServerStorage.P0D_RC_ENABLE_WCS_F01_C01=false`を起動前設定するとランタイムOFFになる。起動途中のステージ消去はしない。

**未完了**：Roblox Studio実機移動・ゲート占有の物理挙動・2クライアント・Android・OWNER FUN。正規RC最新の導入率は **21/58=36.2%**、制作着手率 **48/58=82.8%**。これはローカル評価したゲーム完成度ではなく企画案件段階の件数比。前回S1評価は75/100 FUN_NO_GO。

## 他のRC候補との順番

1. まず、この**Gameを書き換えない**WCSを#220が正規RCビルダへ採用。
2. 次に [PR #297 7職PvE](https://github.com/kk051780/toy-wars-factory/pull/297) のGame/HUDを**新RCへ再リベース**し、ネイティブ検証して採用。
3. 最後に [PR #296 1卵リレー](https://github.com/kk051780/toy-wars-factory/pull/296) と別途のH2 5卵ルールを、**二重Gameパッチなし**で統合。1卵パスには30/30 native Game関数テストが成功済みだが、5卵同時ゲーム統合は未実施。

**絶対禁止**：main変更、未承認merge、公開、課金、追加費用、別Game／Remote／Store writerを増やすこと。
