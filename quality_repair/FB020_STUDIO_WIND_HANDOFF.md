# FB-020 / 実ゲームRC82 風走り修正（隔離・SOURCE-WIP）

**最新ユーザー試遊** #364 コメント 6891935350。実験対象は品質ゲート私的ビルド82本の `Game` と `TrapRaidersHUD`。城、飛行、職別7武器、ロビー、魔獣はこのパッチでは未修復。実装したものだけ数える。

## 実装差分
1. 旧RAIDERに加えて「明示選択ACK済の暗殺者（内部NINJA）」のR/タッチ風走りを許可。サーバ職選択の真値からのみ判定し、HUDとサーバGameの2箇所に反映。
2. Studioでは物理地面をサーバーでRaycastし、現行復帰座標の内側 (X±178,Z±140) に限って広域風走りを許可。public serverは旧ServerStorage明示フラグOFF状態のまま。
3. 18秒クールダウン、卵所持/拘束/死亡/試合外禁止、従来Remote/Seq一意、ダメージ/保存/卵/得点/AIは不変更。

## 実ファイルと再現
- GitHub Actions元候補: [#43694651550](https://github.com/kk051780/toy-wars-factory/actions/runs/43694651550) / artifact 14154231400
- 元Place SHA256: `11c9afe248915989531ff4945cb7267e70f7bf0e7ebfeb8782ac22d8dcdfe6d6`（ユーザーが試した直前の配布候補を実測）
- 変更後Place SHA256: `89e67cc78cdc23ccb63284bd61cd038e3b2d7a7f70f8f084dc500d7f54a06e1f` / 781967 bytes
- 82本のScriptを読み取り、2本変更、80本元GitBlob一致 / 元Game+HUD以外は不変更
- 手元でXML再読・同じパッチ二重適用拒否・Remote唯一を静的検証。native Luau compile / Studio 1client / 2client / Android **NOT_RUN**。

再現用コマンド：`python -m pip install lxml`; `python quality_repair/fb020_wind_assassin_studio_patch.py original_82.rbxlx patched_82.rbxlx`。

**統合**: #297既存Game/HUD原作者が変化行だけを現在の最新版に取り込み、#220認証済みwriterが同HEAD native/Rojo/ソースロックを確認して非force CASで反映。固定古いGameの丸ごと上書きは不可。YELLOWは記録して私的SOURCE採用を進め、REDは停止。main、無断merge、publish、課金なし。
