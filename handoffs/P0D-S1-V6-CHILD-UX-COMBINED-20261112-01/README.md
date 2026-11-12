# TRAP RAIDERS S1｜V6「子ども向け日本語案内」2件を合わせた実機前レビュー版

**パケット:** `P0D-S1-V6-CHILD-UX-COMBINED-20261112-01`

**重要:** これは正式ゲームRCでも公開ゲームでもありません。正式RCを変更せず、OWNERと唯一の統合担当が採用判断するための**レビュー専用・未公開候補ゲームファイル**です。Roblox Studioでの2人対戦・スマホ実機・子どもの試遊は未検証です。

## 出発点

正式RC V6の固定SHAは `1263a03701211a652b99b91d2339575dc8104eff`。罠機能のあるゲーム本体・HUD・ロール・バトル・MapBuilder・FirstMinuteModelなど、**21本の元Luauファイル**と既存Rojo設定を正本にします。

ただし、子どもが実際に遊び方を理解できるよう、すでに個別にCI成功した次の2件のみを加えます。

| 差し替える1ファイル | 正本ソース／ユーザーへの効果 |
| --- | --- |
| `src/server/MapBuilder.luau` | 以前の日本語看板パック [ソース](https://github.com/kk051780/toy-wars-factory/tree/78f849af28e15d7e990dd2690f2cafff0854d001/handoffs/P0D-S1-JP-MAP-SIGNS-20261112-01) を完全そのまま使用。「卵を取る」「卵を届ける」「卵はここへ！」、赤青の城・スタート地点の表示だけ日本語化 |
| `src/shared/FirstMinuteModel.luau` | 以前の守護役案内パック [ソース](https://github.com/kk051780/toy-wars-factory/tree/e29d37737890671d458072bebe729127878700f6/handoffs/P0D-S1-GUARDIAN-TRAP-FTUE-COPY-20261112-01) を完全そのまま使用。最初の0～12秒は罠ボタン、12～32秒は設置方法、32～60秒は20秒待ちと守護の遊び方を教える |

残る**19本は正式RC V6とGit blobが完全一致**します。Rojo `default.project.json` も一致し、Game.server、S1TrapRules、HUD、Config、RemoteEvent、罠の20秒ルールやHP・勝敗は一切変更しません。別チャットで作成されたファイルをコピー・新規改変したものではなく、Gitの元Blobを固定参照しています。

## 検証・品質境界

- `SELECTION_LOCK.json` が全22ファイル（Luau21 + project1）の元Git blobと候補Git blob、バイト数、2件の採用元コミットを記録します。全文比較で、**第三の差分を1件でも検出したら失敗**させます。
- `tools/check_paired_ux_rojo.py` は正式RCのGit blob（19本）、完成済みの2つの独立日本語UXパックのGit blob（2本）を再取得し、コピー元とビット単位に一致するか検査します。
- 正規Rojo v7.7.1（ZIP SHA-256 `00feb4fa0829a1dd72b49df2639da519a352bfe13cadcd83969e2ba2bb5693c4`）で**実際に`.rbxlx`を生成**します。生成後のXMLから21本のソース全文と位置・Script種別を照合し、Game.serverが1本、LocalScript3本、ModuleScript17本であることを確認します。
- 意図的に汚した8種類のXML（見当違いの看板コード、偽の罠クールダウン、権限重複、案内欠落、罠ルール欠落、HUD種別異常、Gameの公開領域移動、不正XML）を拒否させます。
- 既存の各パックの実Luau QAは、日本語看板版が地形168件＋文言20件・改変8件、守護役案内版が文言状態124件・改変9件、それぞれ別途GitHub Actionsで成功済み。今回の新しいCIは**2件を同じ完全V6ゲームファイルに組み込んだ場合のRojo互換性・実ソース同一性**を検証します。

## OWNER と唯一の統合担当向けの採用方針

1. #220の唯一の正式RC担当が、このレビュー版と最新RCを比較して採否を判断します。
2. 採用するなら、MapBuilderの8表示変更とFirstMinuteModelの4局所変更だけを、最新RCの該当2ファイルへ統合してください。すでにソースが変化していた場合は中止して手動再レビューします。
3. RCのマニフェスト・選択履歴を更新し、**採用後の本物の正式RC全体を再度Rojoで生成し、全ゲーム・罠・サーバー権限・2人Studio・スマホ実機・正常終了のQA**を行います。
4. 罠の動作・イベント/ボス解禁を暗黙で変更しないこと。D07/D08の未承認機能はOFFのままにしてください。
5. 事業指標（楽しさ・継続率・収益）や実際の子どもの理解度を証明したとは扱いません。

**保護:** main変更、正式RC直接変更、マージ、Roblox公開、課金支出、Windows PC上のCodexやStudio操作、P0A/B/C、既存自動化の変更はしていません。公開GitHubソースであり鍵や暗号化は不要です。
