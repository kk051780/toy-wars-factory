# P0D FAST-RC — 1本のRCを成長させる（OWNER 2026-11-14）
**正本はこの branch の `rc_fastlane/ACTIVE.json` と `rc_fastlane` 用GitHub Actions。** 前の21本S1は immutable commit `1263a03701211a652b99b91d2339575dc8104eff` に保存し、`releases/P0D_S1_KIDS_RC01/`の原本は上書きしない。

## 方針
- 「企画 → 企画室プレビュー → 人間の試遊 → 再採用会議 → RC組み直し」を**廃止**。採用済・依存を満たすソースは#220唯一のRC writerがこの本線のビルドprofileへ即時採用。GitHub Actionsが同じ源からStudio用`.rbxlx`を出す。OWNERの試遊は**後でまとめて**よい。
- 人間の楽しい/面白いゲート、Studio 2client・Androidは**RCの積み増しの必要条件にしない**。公開前のゲートとしてだけ残す。ゲームのバグは報告後OFF/切戻し→改善。
- 停止条件は本物の危険だけ：Game/Remote/HP/score/XP/Storeの二重権威、アンチ複製違反、保存データ消失、他人のコード変更、ビルド不一致、main/公開/課金の無断実行。
- #250は個々の機能の**追跡台帳**であり、同じ機能を再実装する第二工場ではない。#219企画室が各機能のownerと修復を追い、#220だけがRCを更新。重複レビューチケットで開発を停滞させない。

## 2026-11-14 最初の直結
`rich51` を現行RC主開発profileに選択（最新の51本ソース・自動ビルドの対象）。厳密固定SHA `79123d35cd7afdd5f4f9941675bc2d2cf382ac4e`。
- 51本は既存47本のGame/Storeを**バイト同一**に保ち、セッション限定6技能修行台4ファイルを追加。前回元branch CI成功の証拠： https://github.com/kk051780/toy-wars-factory/actions/runs/43479603989
- **本RCで初回ビルドが実際にPASS済み**：RC SHA `5a0864fe9d3980dd6e0fdd9aa44f4d0169009166`、Actions [43483022604](https://github.com/kk051780/toy-wars-factory/actions/runs/43483022604)、51/51 RojoバイナリSourceExact、Game 1本。以後のHEADは毎回独立ビルドで再判定。Studio実プレイ・Android・人間FUNは依然NOT_TESTED。元候補の未確認事項を持ち越す。
- **6技能の永続保存/日次30分枠/追加4技能の実戦能力は未完成**。元H1 2技能LvとV4セッションLvはまだ別体系。保存統合は元Store担当が互換性・移行を処理するまで禁止。

## 切り離し方法（現時点）
1. `ACTIVE.json`のprofileを`rich47`へ変更すると、**V4セッション修行追加4本を外す**（元47本をそのまま使う）。
2. `legacy21`なら**旧S1に戻す**。前の正式RC `1263a03701211a652b99b91d2339575dc8104eff` は永久に復元可能。
3. H1の無双/天空/卵1/5等の**単体機能ON/OFFはまだ未実装**。次のRC改修はGameを単一権威のまま、サーバー正本のfeature IDで切替できるようにする。現段階で「全部個別に切り離せる」とは言わない。

## ビルド
`.github/workflows/p0d-rc-fastlane.yml` をRC branchへpushすると active profile `rich51` が自動ビルドされ、`P0D-CANONICAL-RC-STUDIO` artifactに`.rbxlx`と検査receiptが出る。source SHA一致→元作者のassemble→Rojo 7.7.1 checksumピン→51/51 XMLソース一致/一意のGame確認という **1回だけの検査**。
`workflow_dispatch` で `rich47` / `legacy21` を個別ビルドもできる（RC本線profileは変えない）。本workflowはRead-only、main変更/merge/Publish/課金/PC操作を行わない。

新機能の実装／ロールバック粒度は [`FEATURE_REGISTRY.json`](FEATURE_REGISTRY.json) に記録し、個別スイッチ未実装を隠さない。

## 次の統合優先
1. ACTIVE `rich51`新RCのビルド成否確認と修正（同一source SHAの再生成だけ）。
2. 6技能の本物のレベル/保存統合・1つのゲーム権威の内部feature flags化（保存データ破損の検証必須）。
3. 卵リレー/進化実戦/7職/巨大ボスなど既存ソースの**小さな実機能**を、#220が同一RCへ追加。先に人間試遊は要求しない。
4. 一括Studio試遊→改善→公開可否はOWNER別承認。

**公式S1進捗75/100は最終監査値。新しいprofileの選択だけで数値を増やさない。**
