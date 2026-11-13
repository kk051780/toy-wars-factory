# 正式RC rich51：6分野セーブ用の正本Store互換性検査

**2026-11-14 JST / QA兼受渡し。#220唯一のRC書き手への証拠であり、本ファイル自体はRCを変更しない。**

## 新しいOWNER優先方針を遵守

正式RC正本 `rc/p0d-s1-kids-rc01` `rc_fastlane/ACTIVE.json`。現在のrich51のソース固定SHA `79123d35cd7afdd5f4f9941675bc2d2cf382ac4e`、正式RC検収HEAD `50bf5b4851fc0eb7c16052f578d6360ec54cd63a`、実物GitHub Actions `43483997763`成功。1機能毎のOWNER人間FUN試遊はRC積上げ要件ではない（公開要件では引き続き必要）。

## 実物正式RCから抽出し、正しくパッチできることを確定

- 本物の公式rich51未公開Studio `.rbxlx` **469021 bytes / SHA256 `6c9d36d6944301c4fb7317e087f877f5cdeb513b38213608976da4cce1c6bb65`**。GitHub Actions original artifact **14066132178**。
- 実際の `ModuleScript PersistentHatchStore` は **20277 bytes、SHA256 `2485b6e5c0f14383c03d2ee7f3a6a38eebbd05793630497cf54a34254c57fa8a`**。現行rich51の魔獣/武器道場はセッションLvで、後発の保存H1用25KB Storeとは別物。
- 他作者元の正本 `518ced360018c10c0773787c14a2e2332a82d2ca` にある `proposed/PersistentHatchStore.patch` を **GitBlob SHA1 `1f6e10dba053a2120e4fb303224241da0511d885` のまま**このQA branchへ固定再利用。四つのhunkが **patch --fuzz=0 / exact contextで4/4適用PASS**。このパッチは現行Storeに適合する。
- 実物に適用された新Storeは **SHA256 `a1c9c64b9d564473392d76d35b67128922f522c1e724dafb981745ed26101511`**。先行の独立「保存付きプライベート51」作者が51 native compile / Store mock69で確認した保存Store source SHA256と **完全一致**。現行Storeからの再現性が確認できた。
- 不適合な**H1保存付き25KB Store**向けの後発patch `922abf...`を現行20KBの公式Storeに混用しない。元作者が実証した通り、逆方向（20KB patchを25KB Store）でも4 hunk中3件が失敗する。Store適用前は実バイトSHAを必須にし、fuzz0の不一致は停止。
- Studio実データ保存、positive UserIdのAPI成功、ログアウト/再入場、Android、OWNER FUNは **未実測**。SOURCE/FAKE UpdateAsync のPASSはRoblox DataStore実機PASSではない。

## 今回、このチャットで独立に実行した再現テスト

本物の公式rich51 `.rbxlx` を開いて Luau 実ソースを抽出するPythonガード `P0D_RICH51_SIXSKILL_STORE_GUARD.py` と **16ケース**をローカル実行、**16/16 PASS**。項目: 
- 公式Place SHA、Script数51、原Store SHA、新Store SHA（完全一致）。
- patch元作者GitBlobと四hunk、fuzz0。
- 元Gameを変えない／Original Remote handler 1本。
- 同一 `U_<real UserId>` key / schema=1 / 単一Store UpdateAsync。追加でSetAsync禁止。
- 既存卵の入手、装備、報酬、XP、進化のStore public methods保持。
- trainingV4のvalid/normalized clone/証明済みreceiptの同一key UpdateAsync。
- 改ざんされた本物のPlaceと、改ざんされたStore patchを各1ケース fail-closed拒否。

**実際にGameの訓練認定・DataStore保存処理はまだ接続していない。** Store candidate単体を正式RCへ取り込むだけでは六技能レベルは保存されない。Gameのauthorが既存唯一Game内に次の機能を実装し、単一profileで既存所有物を保護する必要あり。

## 次の#220 sole RC writer仕様（重要なデータ破損防止）

1. 先行の純粋 `SixSkillAtomicProfile.luau`（原作者GitBlob `aeadd5a8e0d367ddfa639df161843f9a74637c87`）を既存`ServerScriptService.TrapRaidersS1`に追加。**二つ目のStore/DataStoreキー/Game/Remoteを作らない**。
2. 保存前に既存Gameのみが安全なRED/BLUE各道場に立ち、本人/同team/生存/卵非所持/試合RESULTSでないこと、実時間経過30～120秒（JST日付境界をまたがず分割）、友達同サーバー＋非同期実判定を検証し、ユニークな`T...:<seq>`を生成。クライアントの報告値を信頼しない。
3. 同じプロフィール`U_<positive real UserId>`をStore.settleSixSkillでUpdateAsyncし、旧 owned/equipped/receipts/progress/evolution と新 trainingV4 を正規化保存。既存saved-H1 dojo Lv5 と別体系を同期なしで自動変換・消去しない。
4. 重複receipt・UpdateAsyncの再入・同時別機能grant/equip/evolve・再入場のセーブ競合がデータ破損しないテストをNative/FakeStoreで実行。保存失敗のHUDはPENDING/FAILED、確認後のみSAVED。**実機ではない**時にSAVEDと表示禁止。
5. 元作者のプライベート保存候補 `5efed96cf74fb5ae4d9acf0a8f3ff771420ce283`はGame/Storeの別路線だが、Store source SHAが今回の実パッチ結果と同一と独立検証された。**Gameパッチ本体はGitHubに保存されず、元作者の会話ZIPに存在**。そのGameコードの借用可否を正確に再取得できるまで、ないものをGitHubで導入済みと主張しない。
6. その後のみ#220 sole writerが正本RCのPINNED_SOURCE_SHAを新しい統合sourceへ更新し、同じRC Actionsで本物のRojo各source lockを実行。元rich51の独立profile rollbackを保持。Studio2client/Android/FUNは公開ゲートへ移行したまま。

## 進捗の事実分離

- **今回のStore元実物への原作者パッチ一致、独立ガード16/16: PASS。**
- **元の著者のLuau Native69/69, 先行保存付き私的51のLuau51/51は別件証拠。今回のパッチに一致するsourceだが今回Nativeは未実行。**
- 現在ACTIVE rich51は **6skill XP session-only**、永続saved XPとJST30分枠は NOT_IN_RC。新ゲームの正式公開・課金・main変更は実施していない。
- 公式S1評価 **75/100 FUN_NO_GO** は最後の公開品質監査の値で、source検証だけで上げない。

README/元パッチはこのbranchのみ。OWNERはGitHub正本を使えばよく、旧版別Placeを何度も再建する必要なし。
