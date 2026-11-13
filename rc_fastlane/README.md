# P0D FAST-RC — 1本のRCを成長させる（OWNER 2026-11-14）
**正本はこの branch の `rc_fastlane/ACTIVE.json` と `rc_fastlane` 用GitHub Actions。** 前の21本S1は immutable commit `1263a03701211a652b99b91d2339575dc8104eff` に保存し、`releases/P0D_S1_KIDS_RC01/`の原本は上書きしない。

## 方針
- 「企画 → 企画室プレビュー → 人間の試遊 → 再採用会議 → RC組み直し」を**廃止**。採用済・依存を満たすソースは#220唯一のRC writerがこの本線のビルドprofileへ即時採用。GitHub Actionsが同じ源からStudio用`.rbxlx`を出す。OWNERの試遊は**後でまとめて**よい。
- 人間の楽しい/面白いゲート、Studio 2client・Androidは**RCの積み増しの必要条件にしない**。公開前のゲートとしてだけ残す。ゲームのバグは報告後OFF/切戻し→改善。
- 停止条件は本物の危険だけ：Game/Remote/HP/score/XP/Storeの二重権威、アンチ複製違反、保存データ消失、他人のコード変更、ビルド不一致、main/公開/課金の無断実行。
- #250は個々の機能の**追跡台帳**であり、同じ機能を再実装する第二工場ではない。#219企画室が各機能のownerと修復を追い、#220だけがRCを更新。重複レビューチケットで開発を停滞させない。

## 2026-11-14 最初の直結
`rich51` を現行RC主開発profileに選択（最新の51本ソース・自動ビルドの対象）。厳密固定SHA `79123d35cd7afdd5f4f9941675bc2d2cf382ac4e`。
- 51本は既存47本のGame/Storeを**バイト同一**に保ち、セッション限定6技能修行台4ファイルを追加。前回元branch CI成功の証拠： https://github.com/kk051780/toy-wars-factory/actions/runs/43479603989
- **本RCで初回ビルドが実際にPASS済み**：RC SHA `5a0864fe9d3980dd6e0fdd9aa44f4d0169009166`、Actions [43483022604](https://github.com/kk051780/toy-wars-factory/actions/runs/43483022604)、51/51 RojoバイナリSourceExact、Game 1本。以後のHEADは毎回独立ビルドで再判定。Studio実プレイ・Android・人間FUNは依然NOT_TESTED。元候補の未確認事項を持ち越す。
- **6技能の永続保存/日次30分枠/追加4技能の実戦能力は未完成**。元H1 2技能LvとV4セッションLvはまだ別体系。保存統合は元Store担当が互換性・移行を処理するまで禁止。

## 追加済みの可逆修正：V4_IDLE_FRIEND_SAFE_FIX（Studio専用）

正式RC `rich51` の51本のうち、6技能道場の**既存2本だけ**を固定原作者版に差し替えます。元の49本（唯一のGame・Store・Remote権限を含む）は1バイトも変更しません。

- サーバー：フレンド確認を非推奨の `IsFriendsWith` から `IsFriendsWithAsync` に移し、元の `task.spawn+pcall` と同サーバー確認を維持。無料XPボーナスのルールや倍率は変更しません。
- クライアント：実際の人間操作がなくなったとき、Robloxの無操作切断が近いことを知らせる警告。**自動操作・擬似入力・AFK回避は一切しません**。保存されていない6技能XPや日次30分の継続利用を保証するものではありません。
- 作者の元ソース固定：`b7de8f8b7b4cccfb49d2d81c1ee4438d13a4b286`、GitBlob `dbb7171add2b29e337171e547bc40101c2b0dce4` / `7ad4ce4fa9d545cb33836c06dc56c0a03e384666`。既存RC源 `79123d35cd7afdd5f4f9941675bc2d2cf382ac4e` の51本を先に完全再構築した後、RC HEAD内の `rc_fastlane/apply_overlays.py` が強制ソースSHA照合して差し替え。差し替え後も51本をRojoとGit blobで完全照合します。
- **個別OFF**：`rc_fastlane/ACTIVE.json` の `feature_switches.V4_IDLE_FRIEND_SAFE_FIX.enabled` を `false` に変更し、同じRC CIを再実行。ソース差し替えを行わず以前の51本のバイトへ完全復帰します。既存6技能そのものを外したければ `rich47` profile。メインGameや他H1機能の独立OFFスイッチはまだ未実装。
- 公式RCのCI成功は**Studio実機2クライアント・Android・面白さの検証を意味しません**。公開前のゲートとして維持。

## 切り離し方法（現時点）
1. `ACTIVE.json`のprofileを`rich47`へ変更すると、**V4セッション修行追加4本を外す**（元47本をそのまま使う）。
2. `legacy21`なら**旧S1に戻す**。前の正式RC `1263a03701211a652b99b91d2339575dc8104eff` は永久に復元可能。
3. H1の無双/天空/卵1/5等の**単体機能ON/OFFはまだ未実装**。次のRC改修はGameを単一権威のまま、サーバー正本のfeature IDで切替できるようにする。現段階で「全部個別に切り離せる」とは言わない。

## ビルド
`.github/workflows/p0d-rc-fastlane.yml` をRC branchへpushすると active profile `rich51` が自動ビルドされ、`P0D-CANONICAL-RC-STUDIO` artifactに`.rbxlx`と検査receiptが出る。source SHA一致→元作者のassemble→Rojo 7.7.1 checksumピン→51/51 XMLソース一致/一意のGame確認という **1回だけの検査**。
`workflow_dispatch` で `rich47` / `legacy21` を個別ビルドもできる（RC本線profileは変えない）。本workflowはRead-only、main変更/merge/Publish/課金/PC操作を行わない。

新機能の実装／ロールバック粒度は [`FEATURE_REGISTRY.json`](FEATURE_REGISTRY.json) に記録し、個別スイッチ未実装を隠さない。

## 次の統合優先
1. ACTIVE `rich51`新RCのビルド成否確認と修正（同一source SHAの再生成だけ）。
2. 6技能の本物のレベル/保存統合・1つのゲーム権威の内部feature flags化（保存データ破損の検証必須）。
3. 卵リレー/進化実戦/7職/巨大ボスなど既存ソースの**小さな実機能**を、#220が同一RCへ追加。先に人間試遊は要求しない。
4. 一括Studio試遊→改善→公開可否はOWNER別承認。

**公式S1進捗75/100は最終監査値。新しいprofileの選択だけで数値を増やさない。**

## RC追加機能：REALM_HUNT_V1（天空・海・炎・星）
4個の秘密の印を実際のマップに配置。生きたプレイヤーが近付いて発見プロンプトを押すと、サーバーのセッション用探索数が1/4ずつ増え、4/4で22秒の金色の演出が発動。Studio内のカウンターはサーバー属性で更新。卵/スコア/HP/戦闘/永続保存/課金は触らない。独立2スクリプト、元の51スクリプトは変更なし。機能スイッチは `rc_fastlane/FEATURE_SWITCHES.json` で無効化可能。実Roblox Studioは未試験。

### 2026-11-14 実証済みRC：修行改善+4秘境探索
1つのRCで51本作者ソースを起点に、V4修行の2本をソース固定で差し替え（残り49本は不変）、REALM_HUNT_V1の2本を追加。最終計53本。GitHub Actions [43488586444](https://github.com/kk051780/toy-wars-factory/actions/runs/43488586444) でLuauネイティブ新規2本、検査、53ソース完全照合、Rojoによる未公開Studio用Placeの生成すべてSUCCESS。実機/FUNはNOT_TESTED。秘境機能OFFは `rc_fastlane/FEATURE_SWITCHES.json`、修行改善OFFは `ACTIVE.json.feature_switches` で独立に切戻し可能。企画台帳のP0D-055はRCに昇格し、17/55件に増加。

## 2026-11-14 次のRC候補：6技能の本物の保存（DEVのみ）

独立作者の検証済み `Game.patch`/`PersistentHatchStore.patch` と純粋 `SixSkillAtomicProfile.luau` を**原本SHAでピン留め**して、元の唯一の Game/Store のみが更新を行う方式で統合。強い安全条件があるため **現在はRC同一HEAD CI結果が出るまで採用数を増やさない**。
- 元のStudio DEV DataStoreの U_<本物のUserId> キーだけを使用。別保存キーも新writerも新Remoteも作らない。
- serverが本人、同じチームの実パッド・30秒連続・卵を持っていない・友達数を検証し、重複保存しない更新トークンを生成。1件1 UpdateAsync、曖昧応答も同トークンで再試行。
- Serverのみ署名したカウンターを画面に伝える。実Saveの確認が取れない限り「保存成功」と表示しない。
- 旧保存データの未対応フィールドは**上書きで失わない**よう、不明レガシーの形はfail-closed。
- READY_TO_TRAIN/SAVEDはAPI応答が実際に成功した場合のみ。GitHub CI SUCCESSも本物のRoblox DataStore/API試験にはならない。
- 正式RCから独立OFF：`FEATURE_SWITCHES.json.features.SIX_SKILL_DURABLE.enabled=false` で元の53本へ戻せる。

### 最新確定：RC rich54（Studio開発用保存コード）
54/54 native Luau + Rojo exact-source SUCCESS: https://github.com/kk051780/toy-wars-factory/actions/runs/43491029567  固定成功HEAD `2e86ac4fd0d4cb67fd7c673dc4e891b2af6bdc2c`。ゲームの第一保存キーは変更せず、Game/Store/UIのみ差分・純粋Ledger1本追加。RC工程でソース実装に進んだ項目は P0D-051、**18/55**。保存・再ログインの実Roblox Studio APIテストはまだ行っていないので、保存機能の完全完成宣言ではない。公開・課金はしない。

## 追加機能：保存済み武器レベル→PvE攻撃強化
元のGameが唯一のサーバー戦闘責任者。Studio DEVの既存保存データ `trainingV4.totalsMicro.WEAPON` から純粋ポリシーがLvを確認して、Lv5=+5%、Lv10=+10%、Lv20=+15%、Lv30=+20%を中立ハード（Horde MINION）への実際の攻撃にだけ適用。従来の一時的な覚醒強化と掛け算しない（強い方を選択・既存倍率最大3.8）。卵を持っているとき、セーブ未確認、Studio外、対人戦では効果なし。新Remote/Store writer/課金なし。独立フラグOFFで既存54本に戻せる。
実際の中立敵を倒したときの効果を確認するStudio 2client/Android/FUNおよびDEV DataStoreの実際の保存/再ログインは未試験。ソース・CIと実機を混同しない。

**既存戦闘の保存**：元の中立PvE倍率は覚醒倍率×短期道場の武器Lv倍率。この積を元の baseline として保持し、その倍率とDEV保存武器Lvの倍率（最大1.20）の大きい方を採る。最終上限は3.8、対人・BEAST召喚/城攻撃は一切変更なし。Game/HUDの唯一authorityは従来どおり。

**実証済みSOURCE/Place**：保存武器Lv→中立PvE強化。<https://github.com/kk051780/toy-wars-factory/actions/runs/43501488524> にて全55 Luauネイティブコンパイル、既存Game/Store/Remote唯一性、完全ソース入りRojo未公開Studio PlaceまでPASS。前54本のうちGameだけ更新・純粋な新Module1本を追加。実際のRobloxエンジンのSave/再ログイン/中立敵戦闘試験は未完了。55企画から56企画、RC18→19件。

## 保存魔獣Lv → 進化済みスカウトの実戦強化（RC検証中）
Lv5/10/20/30で既存の進化ステージ2/3 ASSAULTスカウト対中立Mob威力をx1.05/1.10/1.15/1.20。短期BEAST道場との高い方を採用し倍率を重複させない。stage>=2の本物の進化スカウト頭上にDEV保存済みランクを表示。元の単一Game/Store/Remoteと保存形式・公開/課金禁止は保持。Studio実機検証は未実施。

**2026-11-14最新確定**: HEAD 947cddb5351ba95b9b27597b9ec1828a8297cd66、GitHub Actions 43504336646で全56本Luauコンパイル、Rojo源完全一致、Studio用未公開Place生成成功。RC機能P0D-057採用、20/57件=35.1%。2client/Android/人間FUN/実際のDataStore往復はNOT_TESTED、公式S1過去評価75/100からの更新は未実施。

## SCOUT_SPECIES_V1（現在CI検証中）
既存の3種のスカウト（通常・森林・星）を、同じ元のGameの既存5秒召喚／進化2分岐に直接統合。星の強い一撃（基礎+12%）・守護+1秒、森の素早い2回攻撃（単発0.58倍、合計上限1.16倍）・守護+1回、通常は元の戦闘。元の保存BEAST倍率・道場効果は上限付きで維持する。3種専用の角/翼と種別ラベルを実際のサーバーModelに生成する。獲得可能な別アイテム3種を新規追加する機能ではない。システム複製や新Remote、別のDataStore writer、課金、対人ダメージ変更なし。単独OFFで以前のrich56に戻せる。実際の2client/Androidと実機FUNは未試験。

**元Game実動作に合わせた枝分かれ安全修正**：実RCの進化攻撃は「命中時フラグ evolvedStrikeUsed」で終わる方式。新種族はそれを既存の1か所で命中数上限（標準1・森2・星1）と命中間隔へ変更し、追加のhordeオーナーは作らない。ガード効果は元スカウト生存中5秒のみなので、星は時間延長ではなく+2吸収回数、森は+1回、標準は元の3/5回に変更。元の命中なし再試行を維持。

**SCOUT_SPECIES_V1正式RC SOURCE採用**：固定head 639da1af22f8fcee1e609a2637ef3bbcabf33d6f、Actions https://github.com/kk051780/toy-wars-factory/actions/runs/43508325263 で57/57ネイティブLuauとRojo完全ソース一致、未公開Studio Place成功。以前の56ソースのうちGameのみ変更、純粋1モジュール追加。アイデア総数58・実RC搭載21（36.2%）。3種は既存魔獣であり、新しく獲得可能な個体や進化分岐を無断追加していない。実機・Android・DataStore・FUNは未試験。
