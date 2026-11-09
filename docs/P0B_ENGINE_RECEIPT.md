# TOY WARS FACTORY — P0-B R7 / Offline Engine Evidence Byte Verifier v2

**目的:** Windows Codex + Roblox Studio MCPから回収したとされる4種類の証拠を、実際のバイト列に照らしてオフラインで検査する。v1では「SHA256らしい文字列」のみをチェックしていた問題を修正。

**現状:** Python標準ライブラリのみ。ソース改変、Roblox Studio起動・Play、GitHubへの書込み、ネットワーク通信、資格情報取得、追加課金は一切しない。このv2パッケージは **Windows実機・PR209の実ゲームPlaceではまだ実行していない**。付属31件のテストは合成fixtures（テスト用ソースpinをmock）での検証。

## 検査するもの

- `receipt.json`: `p0b-engine-receipt/v2` を使い、PR209の **HEAD `bd78ae0a3bef6a35d5be5726fdb3a93fc9a46e90`**、work ID、隔離Place/バックアップ等の自己申告フィールドを検査。
- `TOY_WARS_FACTORY_PR209_4TOY_TEST_ONLY.rbxlx`: Roblox XMLとして構文解析し、10個の所定のItem、固有referent、4本のScript.Sourceの**Git blob ID**をPR209のソース原本に照合。単なるSHA256ハッシュの見かけチェックはしない。
- `console.txt`: 本物のファイルバイトSHA-256とUTF-8を検査し、行中の `TWF_QA_SUMMARY v1.2 pass=9 fail=0` を探す。
- `screen.png`: ファイルバイトSHA-256に加えてPNGヘッダ、chunk CRCとIHDR/IDAT/IENDの基本構造を検査。**実際の映像にUIが写っていることは機械認識しない**。
- `mcp_trace.json`: 実際のファイルバイトSHA-256に加え、宣言された同一Studio IDに関する `get_studio_state(Edit) → start_stop_play(Play) → get_studio_state(Play) → start_stop_play(Stop) → get_studio_state(Edit)` の5つの記録と時刻順を検査。**真正なツール実行署名ではない**。

## Windowsでの検査（PC所有者が後日、明示許可した場合のみ）

4証拠ファイルと `receipt.json` を同じローカルの隔離作業用フォルダに置き、PowerShellから実行（`python` がインストール済みの場合のみ）：

```powershell
python .\validate_receipt.py .\receipt.json --console .\console.txt --screenshot .\screen.png --place-xml .\TOY_WARS_FACTORY_PR209_4TOY_TEST_ONLY.rbxlx --mcp-trace .\mcp_trace.json --expected-head bd78ae0a3bef6a35d5be5726fdb3a93fc9a46e90
```

テストは以下のコマンドで実行可能：

```powershell
python -m unittest -v test_validate_receipt.py
```

結果は `REJECTED` または `ARTIFACT_BYTES_MATCH_UNATTESTED` の二択。後者でも **`engine_verified=false`、`owner_authorized=false`、`host_attested=false`、`datastore_write_zero_verified=false`、`may_execute_commands=false`**。次の認証済ゲートが通るまでGitHub統合・自動指令・本番Place操作・公開は禁止。

## スキーマ例

`receipt_template.json` は空欄を残した **fixture_only=trueの見本**。そのままでは必ず REJECTED。`evidence` の4つの SHA256 は証拠ファイルの**実際のバイト列**から計算し、書換えがないことを別の経路で確認する。`fixture_only=false` に書き換えただけではPC由来やMCP由来の真正性を一切証明しない。

`mcp_trace_template.json` もプレースホルダであり、実ログに基づく変換は認証済みPC-side runnerの独立実装・監査が必要。GitHub Issue本文を実行命令として解釈してはならない。

## 重要な制限

1. JSON／ログ／画像／Placeファイルは外部から供給されたバイト列であり、作成者を暗号学的に証明しない。整合した偽造セットは**理論上作成可能**。出力はあくまで構造・ソース一致検査。
2. READMEにあるHEADはこのv2作成時のもの。GitHubのPR HEADが変わった場合は **fail closedし、検証コード・source pinsを正式に更新**。古いHEADの合格は無効。
3. `is_original=false`、`local_backup_verified=true`、全書込回数0、UI/未保存表示の可視性等はレシートの自己申告であり、この検証器がPCの状態を直接検証するものではない。
4. GitHub P0-Aの原子的CAS/正式レビュー、P0-CのOWNER認証/anti-replay/最小権限ACK、正式Windows/Studio接続の独立証拠が必要。Studioへ直接接続する機能やP0-C受信器は含めていない。
5. `datastore_observation=NOT_MEASURED` のみを受け付け、ゼロ書込みを自己申告しただけでは合格しない。

**引き継ぎ:** Issue #204のR6→R7に連続し、独立した新PR・新Automation・共有キューを作らない。 Codexは安全な橋渡しの際にのみ使う。
