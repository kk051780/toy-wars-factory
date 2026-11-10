# OWNER → Windows Codex: 鍵なし旧成果物移行の次回一括指示

TRAP_RAIDERS / p0d-siege-v19。**既存PCとGitHubの最新CHECKPOINTが正本**。ゲーム進行中のD07/D08/D14統合を割り込んで破壊しない。最初はファイル受領・検証・台帳更新のみ、Studioゲーム本体は変更禁止。

1. GitHub #217 の鍵なし新ルール（新コメント）、#218 の最新他チャット担当、#213 の最新PC実測を参照する。新規 GitHub固定commitの `docs/P0D_KEYLESS_MIGRATION_REGISTRY.json` と `tools/p0d_keyless_migrate.py` を別の隔離作業フォルダーに取得してレビューする。mainへ勝手に統合しない。
2. PC内の **既に正規復元済み** `v39-h1-chatlead-ref-20261110`、`v43A-neutral-skirmish-chatlead-20261110`、`P0D-D07-GOROGAN-RIG-NAV-DAMAGE-20261110-03` の元ZIPを、最新台帳の `original_zip_sha256` と正確に照合する。元ZIPが本当に見つかった場合だけ、OWNER管理 inbox に正確な `<packet_id>.zip` という名前でコピーする。ネットワーク秘密鍵・Drive全検索・他プロジェクトのStudio/ZIPは探索しない。
3. `status` で元ZIPのSHAとZIP構造を検査、次に `pack` で **OWNER PC内だけ** の新しい鍵なしバッチZIPを生成。新しい出力をSHA照合。すべて未受領なら0件、作ったふりはしない。既存ゲームソースへ勝手に展開しない。
4. D07ゴロガン外観（5128e288...）・AI（80483ad...）は、元作者から**復号済みの正規元ZIP**をOWNER専用に再取得できた場合に限り同じ手順で追加する。鍵がないから暗号文を加工して読み出す・同じコードを捏造することは禁止。
5. `verify --stage` の対象フォルダーと各ファイルSHA、パケットごとの `MIGRATED_KEYLESS_SHA_PASS` / `SOURCE_NOT_RECEIVED` / `SOURCE_SHA_MISMATCH` を #218 へ公開安全に記録する。秘密データや平文コードをGitHubの公開repoに書かない。
6. これは **受領バッチの生成** であり D07実攻撃接続・D14車両統合・Roblox Studioを触る許可ではない。実ゲームの統合は従来のOWNER直接指示・隔離実装・二重監査・正常終了ゲートに従う。

失敗時は既存PC保存版を一切変更せず理由だけ報告。追加課金・main push・マージ・Roblox公開なし。