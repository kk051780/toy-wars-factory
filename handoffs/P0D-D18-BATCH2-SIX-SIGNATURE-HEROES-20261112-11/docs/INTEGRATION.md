# 6体のSource-only受け渡し手順

1. 元帳 `#219` の `TRCA-BE-009`, `SP-018`, `VE-027`, `WE-036`, `ZO-045`, `TR-054` に単独soft claim（https://github.com/kk051780/toy-wars-factory/issues/219#issuecomment-6813408820）。
2. 固定`commit`で`data/`、`src/`、`BUILD_MANIFEST.json`のハッシュ確認。
3. 本ファイルは前回の共通インタフェースと同じLuauファクトリー。**元の18体のFactoryやCatalogは一切上書きしない**。名前の衝突を避けるには既存ギャラリーの `D18DetailModels/Batch2/` に新しい2モジュールを別名で置き、構造の確認後にID→factoryへ配線する。
4. Roblox Studioの隔離した**非公開のクローン**でLuau構文・Rojo/3D・near/far・スワイプ・FPSをテストする。現段階では未実施。
5. S1公式RCは#220統合担当だけがinclude-or-skipを選ぶ。初回リリースの必須にしない。公開/課金/報酬/バトル権限なし。

## 次バッチ48体
`data/next54_source_queue.json`（旧名互換、値は48体）を参照。6分類ごと8件で全48を`NOT_STARTED_3D_SOURCE`と明示。新規バッチは別claim/branch/rootに限定し、最新S1と公式キャラ原本を再照合すること。既存IDの再請負は禁止。
