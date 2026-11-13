# P0D 正式RC53 → 6分野永続保存54本：現行RC差分の衝突解消パック

**2026-11-14 JST | QA支援 / #220 sole RC integrator 専用。** 正式RC、main、公開、課金、PC/Codex、既存自動化には一切書き込んでいない。

## 見つかった衝突と今回の実物検証

1. **今回の本物の最新公式RC** `rc/p0d-s1-kids-rc01`、HEAD `4b753cd34dd6629e599b0c256d2f8ab73c448cf0`、<https://github.com/kk051780/toy-wars-factory/actions/runs/43489213284> **SUCCESS**。実物 artifact `14068926474`、ZIP SHA256 `a058a3e7d55fd4157cb5a51d654cddebddf9ba5ee3653d6903123b4a04302e1f`、実物 `.rbxlx` 479054 bytes SHA256 `8e5fd93fedc799247eb9fbb0c61f8f4c59cb256a715631b779da818299c676fb`。正本のGame/Store/Realm2/V4をXMLで抽出し、53 scriptを確認。
2. **元作者の進行済み54パッチは再実装しない。** 元作者 commit `68625792b1882bd69db0342e46efd342d842bbcc` の source-locked 3件（Game, Store, HUD）は実物native 54/54およびFake UpdateAsync43/43検証済み。ただしそのHUD patchは、後から正式RCに入った `Player.Idled` 警告やフレンド安全修正がない **古いV4TrialOverlay** を基準にしている。現在のHUDへ無検査適用して無操作警告を消してはいけない。
3. **本RCのGame本体は作者パッチ基準のまま**：SHA256 `3e18329c413517e520536540a7a5ce5efa9d827337ccb2999254582a8e75518f`。既存元作者 `Game.patch` のGitBlob `5c80b0e3d265fccfc8914b1a0d16cc6418f24d09` を1バイトも変更せずこのrootへ固定した。今ターンでGame.patchの `patch --fuzz=0` 実行は**未実施**。元作者の前回native成果を継承するが、現在のHEADへ正本統合時に#220が再実行すること。
4. **本RC Storeは実バイトで20KBの正本**：SHA256 `2485b6e5c0f14383c03d2ee7f3a6a38eebbd05793630497cf54a34254c57fa8a`。元作者の新しい失われる旧 `dojo` / `dojoV4` の別保存値をfail-closedするStore patchを完全一致 `5b06b6009f223c6054d9973bedc3f1ac24f2864d` として固定。現行RCの実ソースへGNU patch **--fuzz=0、hunks完全成功**。生成Store SHA256 `c9e1c4d7a527939568127cdc7e3cee0ae2312580239b7b5bbe6bac4c657c39bf`。
5. **今ターンの固有修正：HUDを現行RC53に再ベース**。`LATEST53_V4_SAVED_STATUS_IDLE_SAFE.patch` GitBlob `1bc940f1fee0cdbe4ea294be562a797f1d990942`。旧HUD source SHA `7a278a18886f47585e39710e084b623a4391c68e61e274e5f78153f50ea52d48` に GNU patch --fuzz=0で一致、新source SHA256 `0094052e013c33212545b6535acacfb8eb6ed8559776567e0bb9a13041db035f`。
   - **`SAVED` は元Game+Storeからサーバー属性 `P0D_V4_SaveStatus` が明示的に来た場合のみ**表示。未承認は LOCAL_ONLY/WRITING/UNCONFIRMED等でセッションXPのみ。
   - 既存の `player.Idled`、実ユーザー操作の `UserInputService.InputBegan`、約20分無操作に関する警告を保持。警告解除後はハードコード「保存なし」へ戻すのではなく、現在の認証済みSAVE状態を再描画。
   - `VirtualUser` / `VirtualInputManager` / 新規Remote / DataStoreクライアント操作は含まず、StoreやGameの権限を増やさない。

## このチャットで実際に行った検査

1. 公式Actions ZIPダウンロード・CRC、Place原本SHA一致と **53の本物のXML Source抽出**：PASS。
2. 本物のGame/Store/HUD SHA固定とRealmHunt2 script保持：PASS。
3. 先行作者Store patch `5b06...` を現行Storeへfuzz0実適用して SHA `c9e1...`：PASS。
4. 新HUD patch `1bc940...` を現行HUDへfuzz0実適用して SHA `009405...`：PASS。
5. **ローカルPython独立検査17/17 PASS**。Game1本/Remote1 handler、悪質な上書き防止、旧dojo/dojoV4 failclosed、保存確認後のみ表示、Idled維持、人手入力で表示回復、Store same-key UpdateAsync、元ソースの改変2件拒否など。

これは「最新RCに対する**互換パッチ検証**」であり、全部を結合した54本の新RojoビルドやLuau再コンパイルは**このターンでは未実施**。先行作者の54/54 PASSをこの新HUD改訂版のPASSと混同しない。実Studio1/2/Android/実DataStore再入場/FUNはNOT_TESTED。

## 唯一のRC書き手 #220 への最短引渡し

1. **今のRC HEADを再取得し、上記Game/Store/HUD source SHAと照合**（変わっていたらSTOP/再ベース）。
2. 元作者 `LATEST53_EXACT_AUTHOR_GAME.patch`、`LATEST53_EXACT_AUTHOR_STORE_ALIAS_SAFE.patch`、今回`LATEST53_V4_SAVED_STATUS_IDLE_SAFE.patch` を正本のソースlock付きビルドに反映。
3. 原作者 immutable `SixSkillAtomicProfile.luau` GitBlob `aeadd5a8e0d367ddfa639df161843f9a74637c87` をServerScriptServiceの同じフォルダに1 module追加。既存Scheduler/XPモデルと唯一Game/Storeを再利用。**既存RealmHunt2本とV4 idle/friend fixを失わない**。
4. 正式RC内 feature `SIX_SKILL_DURABLE` を独立OFF可能に。少なくともStore+Game+HUDの一括rollback IDを確保し、中途半端な片方だけの切替は禁止。
5. 既存の単一RC CIで 54/54 source exact、原本Game1・Remote1・Store同key、Luau Native、Fake UpdateAsyncの重複receipt/同時装備/不正追加を一括検査。合格したら正式RC PROFILEとFeatureRegistryを更新し、OWNERへ実際のStudio Placeを渡す。異常時は現在成功済みの53に切戻し。
6. 人間Studio2client/Android/FUNはOWNER方針で公開前の一括試遊へ。RC取り込みの毎回の必須条件には戻さない。公開・課金禁止は変更しない。

現時点の公式品質評価は **75/100 FUN_NO_GO**。検査PASSは公開品質採点の自動加点ではない。守るべき主要成果は卵の所持/装備/進化、SkyV5、無双V7、RealmHunt、既存道場、6技能日次Quotaを1つのGame/Storeで安全に並存させること。
