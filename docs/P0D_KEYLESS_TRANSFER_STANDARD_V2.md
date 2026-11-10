# P0-D・P0-A横断｜鍵なし納品標準（OWNER指示 2026-11-10）

## 決定
新規の商用ゲーム成果は、**鍵探しを必要としない OWNER 管理の原本ZIP** とする。現行 `kk051780/toy-wars-factory` は **PUBLIC** なので、平文 ZIP・ゲームソース・未公開のキャラクター設定・秘密鍵をこのリポジトリのブランチ、Draft PR、Issue、CI成果物へ置かない。GitHub に保管するのは公開安全な受領プログラム、仕様、原本・変換後の SHA-256、パケットID、依存関係、ステータスのみ。SHAは完全性照合であり、秘匿や署名の代わりにはならない。

## 新規成果物の必須「鍵なし受入」契約
1. `packet_id`・`game_id=TRAP_RAIDERS`・`work_id=p0d-siege-v19`・担当範囲・依存・実装状態を登録する。
2. 元 Luau/Python/QA/README/manifest など正規原本を単一の ZIP にまとめ、`sha256` と明細 SHA を取得する。鍵・パスワード・別のZIPの探索は要求しない。
3. **OWNER専用の安全な経路**（会話ファイルのPCダウンロード、OWNER限定Library→PC、OWNERが明示承認したアクセス制御付き非公開共有先）へ原本を渡す。公開 GitHub に原本の平文を置かない。
4. Windows Codex は固定受信フォルダー `%USERPROFILE%\TRAP_RAIDERS\handoff\inbox` または `Downloads` の指定ファイルだけを確認し、GitHub台帳の SHA・packet_id・ZIP内部ファイル・安全なパスを検査する。必要な原本がなければ `BLOCKED_SOURCE_NOT_PRESENT`。別パケットのファイルを流用・代替しない。
5. Codexは隔離した `handoff/staged/<packet_id or bundle_sha>` へ**データとして**展開する。現PCの本体 `CHECKPOINT`/Place/Source を保全。依存/認証/独立監査・合格したパケットだけ、OWNERが直接指示して一件ずつPC/Studioで試す。
6. `PUBLIC_METADATA_VERIFIED`、`OWNER_BYTES_RECEIVED`、`ZIP_SHA_PASS`、`PC_STAGE_PASS`、`LUAU_PARSE`、`STUDIO_SCOPED_PASS`、`STUDIO_CLOSED_VERIFIED`、`GITHUB_SOURCE_CONFIRMED` を混同しない。
7. main直書込み・未審査merge・本番公開・実課金・追加支出・P0-A/CAS回避は従来どおり禁止。

## 旧暗号化パックの移行
- **元のZIPがチャットまたはOWNERのPCにある**：既存GitHubに記録された元ZIP SHAと照合し、`p0d_keyless_migrate.py` で鍵なしオーナー専用バッチZIPへ組み替える。元ZIPのバイト列・正本SHAを変更して「古い復元PASS」を取り消してはならない。新形式は別revision。
- **Windowsで正規に復号済み**：Windows PCにある元ZIPが正しい元ZIP SHAを満たせば同じ方式で移行できる。元の暗号鍵を再度使う必要はない。
- **元ZIP不明・鍵だけ失われた**：公開暗号文から元コードを復元することはできない。元制作者に原本ZIPをOWNER専用で再提供してもらう。提供不可の場合は `BLOCKED_SOURCE_NOT_PRESENT` とし、ソースを勝手に捏造・差替えない。もし再実装するなら既存パケットとは別の新規企画・コード・QAとして扱う。
- **旧AES方式が必要な共同作業**：既存暗号文を無理に解除しない。各元作者が鍵と原本を正規に保持し、OWNERへ私的に渡すことは可能。しかしこれ以後、新しい納品の要件に「鍵の所在を元作者以外が探す」を入れない。

## 既存成果物の現在の事実（このチャットからの実測）
- GitHubの以前の16封筒台帳と、その後の個別パックを合わせ**候補26件**のSHA付き暫定台帳を作成。候補数であり完成ゲーム機能数ではない。今後の最新コメントで追記する。
- この作業環境から元ZIPを直接照合できたのはD18図鑑 **1/26** 件。正規SHA検査・鍵なしZIP変換・隔離再展開を実施。残り25件はここには元ZIPがないため**未変換**。ただしPCで復元済と報告された v39、v43-A、D07 Rig の3件は、Windowsの元ZIPが正規SHAに一致すれば次に転換できる。現チャットではそのPC実ファイルは受け取っていない。
- ゴロガン外観・AIについてGitHub #213 Windows実測は**専用鍵不足**。このルールは両パックの復号済を意味しない。

## 自動化用の安全なコマンド（PC側・OWNERから直接指示）
公開安全ツールの置き場： `tools/p0d_keyless_migrate.py` ／ `docs/P0D_KEYLESS_MIGRATION_REGISTRY.json`

```powershell
# OWNERが正規元ZIPを inbox に <packet_id>.zip として提供した後のみ。
py -3 tools/p0d_keyless_migrate.py status --registry docs/P0D_KEYLESS_MIGRATION_REGISTRY.json --inbox "$env:USERPROFILE\TRAP_RAIDERS\handoff\inbox"
py -3 tools/p0d_keyless_migrate.py pack --registry docs/P0D_KEYLESS_MIGRATION_REGISTRY.json --inbox "$env:USERPROFILE\TRAP_RAIDERS\handoff\inbox" --output "$env:USERPROFILE\TRAP_RAIDERS\handoff\keyless\TRAP_RAIDERS_OWNER_KEYLESS_BATCH.zip"
# packが出力した sha256 を正本台帳へ記録してから検証（推測・コピペ誤り不可）
py -3 tools/p0d_keyless_migrate.py verify --registry docs/P0D_KEYLESS_MIGRATION_REGISTRY.json --bundle "$env:USERPROFILE\TRAP_RAIDERS\handoff\keyless\TRAP_RAIDERS_OWNER_KEYLESS_BATCH.zip" --sha256 <実測SHA256> --stage "$env:USERPROFILE\TRAP_RAIDERS\handoff\staged"
```

`pack` は元ZIPが無いパケットを出力に混ぜず、`pending` として明示する。全件揃っていなければ `is_partial=true`。すべて必須にする際は `--strict-all` で欠落した場合は失敗する。既存ファイル上書きは許さない。コマンドはCodexへの遠隔命令ではなく、OWNERの実行操作が必要。

## 公開安全Githubメタ
- Issue #217：新規・旧式移行の共通方針
- Issue #218：実パケットごとの担当と正本固定SHA・状態
- Issue #213：Windows実機・Studioの受入QA
- Issue #219：D18企画図鑑（旧パックと新規構想）

以上はOWNERからの新方針を受けてこのチャットで作成した標準。各既存チャット／Windowsの実作業はこのコメントから自動実行されない。