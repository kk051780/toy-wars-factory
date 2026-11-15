# TRAP RAIDERS：最新正式RC55 → 7職業PvE付き56本への再ベース（2026-11-14）

**最新の受渡し正本。従来の README_JP.md にある「54→55」は古いベースの履歴であり、今回の正式統合には使わない。**

## 現行正式RCを維持する

- 最新正式RCのビルド成功基点：`0dd7f4418d06200e40688c79c8290745cb56834d`、GitHub Actions `43501488524` SUCCESS。実物 `.rbxlx` **55ソース**、SHA256 `e439aa5d7372e77b0949bb681ed7342485a541c3738f7c7aceede1b6ea23b8c0`。このRCは `SAVED_PVE_MASTERY`、つまり保存済WEAPONレベルによる中立Horde強化を含む。
- **こちらで実際に作った新56ソース・プライベートStudio候補** `P0D_RICH56_7JOBS_WITH_SAVED_WEAPON_PRIVATE.rbxlx`、実体サイズ 514787 bytes、SHA256 `cbd373a004c00049306dc3b87cf17b57df5b6171ef54615e4f3b0b0b6d39fd5c`。所有者への自己完結ZIP `P0D_RICH56_7JOBS_LATEST_RC_HANDOFF.zip` SHA256 `36c281df5cb23f253787b2db186ca53477c252ee4c190fcdf23356b643188ef5`（公式55実体、私的56実体、元Game/HUD差分、元々の職業ルール、26ケース独立テスト、receipt収録）。**このZIPは元ChatGPT会話のダウンロードのみ**であり、GitHubにバイナリを入れたとは主張しない。
- **旧55→新56の完全なXMLソース比較**：元55のうち53本バイト完全一致。既存2本の `Game` と `TrapRaidersHUD` のみ編集し、元作者の純 `SevenJobsRules` を1本追加。元の `SavedPveMasteryPolicy`、`PersistentHatchStore`、六技能DEV永続保存、卵1/5、SkyV5、MusouV7、Realm Hunt2、元Remote／報酬／進化は不変。唯一Game・唯一Remote・唯一Store権威を保持。
- 旧RC54をベースに開発したGame.patchは**実際のRC55 GameにもGNU patch `--fuzz=0` で8/8ハンク適用成功**。元の保存武器強化の `SavedPvePolicy.mergeWithEarned` 呼出を消していない。仕上げの一行 `CanQuery=false` によって仮設砲台がRaycastを邪魔しない。
- 最新builder `tools/apply_seven_jobs.py` は **RC55 Game SHA256 `652cd71f824d6926a09c1042461f907d9a9427cb74919191002381bcef3a187e`、HUD `3f2654199c2531bea34371a4ea33beecf65d1e306ecd91e86f5164ab3ddca06d` を必須**とし、出来上がり Game `aa1f72d48311e133024a138344f1f9f995e59ca4de647e450e07dfdbd1a6dc9e` をロック。不一致なら処理を止める。新55→56の元53スクリプトは変更不可。
- **LOCAL 実行**：`python /mnt/data/p0d_work54/test_latest_rc56.py` 実物2つを検査して **26/26 PASS**（原本SHA、55/56 XML、53バイト不変、唯一Game/Remote、旧Store同一、保存PvE残存、7職、選択/攻撃、負例改造Place拒否等）。これは**実物ソースに対するローカル静的・構造検査**であり、native Luauの正常実行やStudio engineの確認ではない。
- **GitHub CIソース** `.github/workflows/p0d-sevenjobs-private55-native-20261114.yml`（ファイル名の「55」は旧名称、内容は**公式55→私的56**）。著者H1原始51→固定公式55の正式 overlay4段→自分の56 builder→native Luau56/56コンパイル＋33テスト→固定Rojo7.7.1→XML exact56で出力する。**ワークフローを設置した事実と、GitHub Actionsの成功は別**。現時点でCIの成功run ID／実際のLuau56実行は確認できていないため、`NATIVE=UNVERIFIED / ROJO56=UNVERIFIED` とする。

## 実際の7職業内容（現時点のスコープ）

- 戦士：正面重撃（8秒CD）
- 魔法使い：3方向魔法（14秒CD）
- 忍者：2段影刃（10秒CD）
- 罠師：4方向衝撃罠（14秒CD）
- 建築士：非衝突仮設砲台と2回追撃（18秒CD）
- 魔獣使い：魔獣突進と後追い攻撃（15秒CD）
- ゾンビ使い：亡者3段攻撃（18秒CD）

元GameがロビーJOB_PICKを判定し、同職各チーム1名制・ACTIVEのみJOB_SKILL・Q/画面ボタン・能力CD・生存/同team/卵非所持/非拘束・既存seq再送拒否を守り、中立Hordeへしか新ジョブ攻撃しない。新ジョブの7種類すべてのPvP能力、職業HP/速度、召喚育成・本物の拘束や建築バトル、永続職業アンロックはまだ実装していない。**7つのPvE技能の実装ソース≠完成した7職業ゲーム**。

プライベート用 OFF flag `ServerStorage.P0D_RC_ENABLE_SEVEN_JOBS_PVE=false` は元Gameと元HUDの両側へ設置。公開サーバーではコードが動作しないStudio限定プレビュー。オフにしても元ゲームのPvP RAIDER/GUARDIAN、通常PvE攻撃、保存WEAPON強化は維持。

## 正式RC唯一の書き手 #220 の最短受入

1. 今の`rc/p0d-s1-kids-rc01`HEADと`SAVED_PVE_MASTERY`の状態を再確認。成功済み source55 基点よりさらにGameが変わっていたら**SOURCE SHA不一致でSTOP、作者から正しいrebaseだけ依頼**。RCの別Gameと古い丸ごとのPlaceをコピーしない。
2. 今回source `src/SevenJobsRules.luau`（GitBlob `a7253d36cb67df47d4ba65d35af212ed1eb7b5b2`）、Game/HUD 2つのデコード可能なSHAロックpatch、`tools/apply_seven_jobs.py`を正本RCビルドの「SAVED_PVE_MASTERY適用直後」に呼ぶ。単一ゲーム/Store権威、元保存済PvE強化を絶対に落とさない。
3. 現行正本の**同じ1本のCI**でnative all56/56、クラス負例・既存PvE保存・卵スコア安全、Rojo SourceExact全56検証、OFF切り戻しを済ませた後だけ`SEVEN_JOBS_PVE_V1`を正式RC機能台帳へ移す。CIが失敗したら現行55を維持。新たな公開・paid・main merge/PC操作禁止。
4. OWNERに実際のStudio56バイナリを渡す。Studio2client/Android/人間FUNや実DataStoreは**未試験**で、Ownerの方針どおり公開前の一括ゲートへ回す（機能RC採用の都度試遊を繰り返さない）。
5. 公開品質の過去評価は**75/100・FUN_NO_GO**のまま。26/26ローカル静的検査をゲーム完成%へ誤換算しない。

この手順は**別のプライベートRCを量産するためでなく、正式RCを上書きせず1機能ずつ早く積み上げるためのソース受渡し**。
