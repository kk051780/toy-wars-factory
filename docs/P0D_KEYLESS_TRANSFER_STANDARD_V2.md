# P0-D 鍵なし成果物移行補助標準（OWNER 2026-11-10）

> **上位正本**：GitHub [#217](https://github.com/kk051780/toy-wars-factory/issues/217) と [#218](https://github.com/kk051780/toy-wars-factory/issues/218) の冒頭にある **TRAP_RAIDERS の `PUBLIC_SOURCE_V1` 特別許可**。この文書はそれを上書きしない。全P0配送の標準策定は #217 #6766538817 の別担当レーンと調整する。本件は D18 企画および旧パックの**元ZIP検証・鍵不要OWNERローカル移行補助ツール**の実装記録である。

## 第一方式：TRAP RAIDERS オリジナルゲームソースの鍵なし直接納品

ユーザーは最初のゲーム `TRAP_RAIDERS / p0d-siege-v19` **の自作ゲームソースの公開を明示許可**している。ゲームコードの新規・再納品は [P0D_PUBLIC_SOURCE_HANDOFF_V1](https://github.com/kk051780/toy-wars-factory/blob/b519a17a3152613666822b7d9660742f93a739b7/handoffs/P0D_PUBLIC_SOURCE_HANDOFF/docs/P0D_PUBLIC_SOURCE_HANDOFF_V1.md) に従う。

- 正規の元Luau、Pythonテスト、README、BUILD_MANIFESTを、他チャットと重複しない**一意の隔離branch**へ、平文で**直接コミット**する。
- 固定40桁commitから**ソース実体の全件**を再取得し、SHAとバイトを検査する。AESの封筒だけ・概要READMEだけでは新方式の納品完了ではない。
- APIキー、認証情報、本人情報、実プレイヤー情報、無許可第三者IP、他ゲームの非公開ソースなどは公開禁止。公開を許された範囲を超えて、非公開の企画原本を自動公開しない。
- Codexの真のPC保存Place/CHECKPOINTと依存を照合し、OWNERが直接指示して一つずつ統合する。main直変更・無断merge・Roblox本番公開・実課金・CAS回避禁止。

## 第二方式：OWNER専用鍵不要ZIP（旧ZIP移行／非公開の資料）

GitHub公開の対象外にある企画資料や既存のオリジナルZIPで、OWNER本人が安全に私的転送する場合は、**パケットごとのAES復号鍵を探さない**。

- 原本ZIPをOWNERのPC `Downloads` か `%USERPROFILE%\TRAP_RAIDERS\handoff\inbox\<packet_id>.zip` の決まった場所へ渡す。
- `p0d_keyless_migrate.py` は `P0D_KEYLESS_MIGRATION_REGISTRY.json` に登録済みの**元ZIP SHA256**を確認し、安全なZIPエントリだけを解凍・まとめ直す。検査不成立なら一切混ぜない。
- 鍵不要のバッチZIPは**OWNER管理の非公開ローカルファイル**として生成し、全ファイルSHAを持つ `KEYLESS_RECEIPT.json` を同梱する。`verify --stage` は隔離フォルダーだけを作り、ゲーム本体に書き込まない。
- 元ZIPがなければ `BLOCKED_SOURCE_NOT_PRESENT`、暗号文だけなら復元できない。旧暗号の復元実績と別々に記録し、**鍵を使わず元の暗号文から復元できた**という虚偽表示をしない。
- 既存アーカイブの作者が元ソースを持っている場合は、第一方式の公開を許されたゲームコードなら**別revisionのPUBLIC_SOURCE_V1**として再納品するのが優先。元原本がない場合の独立再実装は新しいコード・検証を必要とし、旧バイト一致とは言わない。
- **鍵なしZIPを公開GitHubへ置くことと、鍵なしでOWNERへ渡すことは別**。非公開であるべき資料はOWNERの私的保存に留める。SHAは秘匿の手段ではない。

## 今回の実際の検証結果

- 2026-11-10 時点の旧・追加受渡し候補26件を、公開安全メタの暫定台帳に整理（**全成果の確定総数ではない**）。他チャットの19件台帳やPC実測と集計基準が違うため単純比較しない。
- **このチャットのローカル環境**に元ZIPがあったのはD18コレクション1件。SHA照合後、元10ファイルを保持した**鍵不要OWNER専用バッチ**を実制作し、再検証・隔離展開もPASS。残25件はこのチャットに元ZIPが届いていないだけであり、**他チャットやWindowsに原本が存在しないという意味ではない**。
- Windowsで復元済のv39-H1、v43-A、D07実リグが各々正しい元ZIP SHAを満たせば、PC上で追加移行できる。一方D07外観とAIは最新PC報告でAES鍵不足。元作者の公開ソース再納品または別途認可された再実装が必要。
- `p0d_keyless_migrate.py` 単体17件PASS、D18鍵不要ZIP構造検査＋外側SHA＋隔離展開PASS。**Studioでのゲーム動作を確認したものではない**。

## 実行例：所有者のPCに正規の元ZIPが存在するときだけ

```powershell
# 改変禁止の隔離ワークスペースで行う。元ZIP名は正確なpacket_id.zip。
py -3 tools/p0d_keyless_migrate.py status --registry docs/P0D_KEYLESS_MIGRATION_REGISTRY.json --inbox "$env:USERPROFILE\TRAP_RAIDERS\handoff\inbox"
py -3 tools/p0d_keyless_migrate.py pack --registry docs/P0D_KEYLESS_MIGRATION_REGISTRY.json --inbox "$env:USERPROFILE\TRAP_RAIDERS\handoff\inbox" --output "$env:USERPROFILE\TRAP_RAIDERS\handoff\keyless\TRAP_RAIDERS_OWNER_KEYLESS_BATCH.zip"
# 出力時に報告された実際のSHAを、同じ実ファイルで照合する
py -3 tools/p0d_keyless_migrate.py verify --registry docs/P0D_KEYLESS_MIGRATION_REGISTRY.json --bundle "$env:USERPROFILE\TRAP_RAIDERS\handoff\keyless\TRAP_RAIDERS_OWNER_KEYLESS_BATCH.zip" --sha256 <実測64桁SHA256> --stage "$env:USERPROFILE\TRAP_RAIDERS\handoff\staged"
```

#217が全P0方針の正本、#218が実パケット所有/納品台帳、#213がWindows実機QA。GitHubコメントはWindows PCへの自動実行命令ではない。