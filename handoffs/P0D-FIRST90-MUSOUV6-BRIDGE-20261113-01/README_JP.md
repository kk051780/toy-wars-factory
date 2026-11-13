# P0D H1：B42「卵案内・進化」× 無双V6「動く雑魚敵」実ソース統合候補

2026-11-13 JST / isolated PRELAUNCH only / **公式S1 RCではない**。

## 何を統合したか
- **ベース B42** \`837853e66278e38bb79f6399c3e8bfc9a2403be6\`：一つの本物の Game.server、1卵/5卵、XP・無課金覚醒、保存・魔獣進化、90秒の卵ガイドとWaypoint、旧Mob V5。
- **変更は1モジュールだけ**：\`server/MusouHorde.luau\` を #288 無双V6固定Git blob \`e67b186f08a0e9ca20d5f09a7c5b22205e2b7240\`（commit \`4b09de3eb70abb2e79268ce41bdecc4b614d39df\`）に置換。9体の中立敵の3D腕・足・目・角・命中後の怯みと精鋭の予兆等を持つ。**残り41モジュールはB42にバイト同一**。
- 既存の Game/Remote/HP/XP/Score/Store は一切増やさない。従ってこれは２つの別Gameを丸ごと重ねたものではなく、**既存B42ランタイムへV6 Hordeを1つ接続した統合**。
- \`tools/assemble.py\` はB42正本の再現可能な42スクリプト生成を呼び出し、固定Git SHAを照合したV6 Hordeだけを差し替え、source-lockを付けて隔離 \`dist/\` を生成。既存 author roots/RC/mainを編集しない。
- \`tests/test_integration.py\` と隔離GitHub Actionsが、全42本の実Luau native compile / 実Horde nativeモック / Rojo非公開Place生成とsource一致を確認する。PASSは実Roblox Studio/Android/2clientのPASSと混同しない。

## 検証中の注意
- **新しい世界/海/空はこのビルドに追加していない。** #248で報告された4箇所の壁交差は別途解決が必要。
- V6では既存B42のHorde V5と異なる追加3D Partが増えるため、実StudioでFPS・モバイル視認性・エリート予兆・卵運搬を必ず確認する。
- \`B42\` の獲得魔獣ASSAULT「5秒に1回の成功命中」制約をゲーム側で維持し、V6単体40-Luau別ゲームの2チャンス設定を混入しない。元の収集/進化/データ/HP/XPは改変しない。
- 見た目の改善が楽しいことは未実証。\`STUDIO_2CLIENT=NOT_TESTED\` \`ANDROID=NOT_TESTED\` \`OWNER_FUN=NOT_TESTED\`。
- 実Studio試遊はOWNERが隔離Placeを本人のPCで開く。GitHubへのコード納品はCodex自動実行ではない。

**統合採否**：#250が製品採用を決定し、#220唯一の正式RC統合担当だけが公式S1へ実差分・SOURCE_LOCKを搬入する。この候補はあくまでS1のための非公開比較材料であり、公開・実課金・main変更・正式RC書込み・mergeなし。
