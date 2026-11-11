# P0D S1 V6 — Guardian罠の復活・リプレイ・退出時クリーンアップ検証

game_id: TRAP_RAIDERS
work_id: p0d-siege-v19
release_id: P0D-S1-KIDS-RC01
packet_id: P0D-S1-V6-TRAP-RESPAWN-REPLAY-20261112-01
owner_lane: CHAT-QA-S1-TRAP-RESPAWN-REPLAY-20261112-01
exact_original_RC_commit: 1263a03701211a652b99b91d2339575dc8104eff

## 目的

元ゲームの固定Game.serverほか計5本の実Luauと元公式native test runnerをバイト単位で検証して読み出す。「罠を踏んだ直後の復活」「設置者が抜けても試合が続く条件」「クールダウンが終わった後に古いseqを再送」の3つを増強する。変更するのは一時生成するテスト用APIダブルとアサーションだけ。公式RC・Studio・mainを一切書き換えない。

## 追加テスト

1. 最初の罠は踏まれたらDestroy済みで再利用されない。20秒のクールダウン後に正当な2枚目は置ける。
2. 敵への減速が発生する。復活でHumanoidが替わっても旧・新両方の歩行速度状態が安全に復元される。
3. 20秒のクールダウンが終わっても、同じseq8の再送は新しい罠を作れない（第三罠の25秒の有効期間中）。
4. 実テスト用プレイヤーをRED/BLUEに1人ずつ追加し、BLUEがまだ生存している試合途中に罠の設置者が退出したら、罠のみ確実に削除され試合は続行できる。
5. サーバーのseq拒否・旧Humanoidの減速解除・設置者退出時の罠除去をそれぞれ意図的に壊した3変異がnative Luau検査で失敗する。

## 実行例

Python構造テスト:
python3 handoffs/P0D-S1-V6-TRAP-RESPAWN-REPLAY-20261112-01/tools/trap_respawn_native.py --selftest

Python unittest:
python3 -m unittest discover -s handoffs/P0D-S1-V6-TRAP-RESPAWN-REPLAY-20261112-01/tests -v

native Luau 実ソース試験:
python3 handoffs/P0D-S1-V6-TRAP-RESPAWN-REPLAY-20261112-01/tools/trap_respawn_native.py --repo . --luau /path/to/luau

隔離branch専用GitHub Actionsは固定公式Luauソース f46d879e28302a430029304f7f6a162aed66f103 を取得しnative CLIをソースビルドして実行する。履歴全量をgit fetchして固定オリジナルcommitが存在する必要がある。オリジナルGit blob SHA 6件のうちひとつでも違えば失敗。

## 証拠の境界

Python SELFTEST、実source native Luauと3つの危険変異検知、完全manifest SHA256、GitHub CIを区別。Luau内のRobloxサービスは外部テストダブルであり、実Roblox Studio・2client・スマホ・音/FPS・人間試遊・リリース許可は一切証明しない。全体進捗率は唯一のIssue #220統合班の判定を転載するだけ。Win CodexはOWNER直接指示があるまで起動しない。

Issue #226: https://github.com/kk051780/toy-wars-factory/issues/226
共通台帳 #218: https://github.com/kk051780/toy-wars-factory/issues/218
公式S1進捗 #220: https://github.com/kk051780/toy-wars-factory/issues/220
禁止: main/公式RCへのwrite、無断merge、Roblox publish、課金/支出、P0-A/B/C保護改変、既存5 automation改変。
