# OWNER → Windows Codex｜旧パケット鍵なし化・補助手順

TRAP_RAIDERS / p0d-siege-v19。**第一方式は既に承認されたPUBLIC_SOURCE_V1**。元ゲームコードの再納品は実LuauをPUBLIC GitHubの各隔離branchに直接置き、commit/SHAで受領する。元ソースが存在しない旧AESパックを復号できたと偽装しない。他案件の秘匿資料は絶対公開しない。

本手順は、OWNERのPCに**正規の原本ZIPが既に存在する**場合に限る鍵不要バッチ移行補助。main/現Place/Studio/実課金は操作禁止。

1. #217 の公開ソースV1上位規約、#218の最新担当、#213の最新Windows実測を確認。実PCのCHECKPOINT・Source・Placeを保全する。
2. 既に復元済みとPC報告された v39-H1、v43-A、D07実リグの原本ZIPが現在も保存されているか、**指定原本ハッシュだけ**で確認する。見つかった正しい原本だけ `<packet_id>.zip` として `%USERPROFILE%\TRAP_RAIDERS\handoff\inbox` にコピーする。全ディスク探索や無関係な鍵探しをせず、既存のStudioファイルを変更しない。
3. 本固定commitの公開安全な `tools/p0d_keyless_migrate.py`、`docs/P0D_KEYLESS_MIGRATION_REGISTRY.json` を隔離取得。`status` → `pack` → `verify --stage` の順に実行。SHA不一致・元ファイル不足・ZIP安全検査失敗はそのパケットのみHOLD。変換後のZIPはOWNER管理PC内だけで保存する。
4. D07ゴロガン外観/AIは **鍵不足の旧暗号パック**。元作者が自作ソースを保持するなら #217指定のPUBLIC_SOURCE_V1で別revisionとして再納品するか、実ソースがなければCodexが別途認可された独立実装を行う。旧AES暗号文を推測して解除したことにはしない。
5. `PUBLIC_SOURCE_READBACK_PASS`, `LOCAL_ORIGINAL_SHA_PASS`, `KEYLESS_BATCH_VERIFY_PASS`, `STUDIO_QA_PASS` は別判定。#218/#213へ秘密を含まない照合結果のみ報告する。

OWNERの明示指示なしにmain変更、未審査merge、Roblox公開、追加支出、本番課金を行わない。