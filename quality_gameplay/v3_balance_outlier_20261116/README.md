# GQ568｜EGGRUMBLE V3試合時間外れ値：品質判定の誤PASS防止

## 実際の31源構成で発見した重要な制約
固定RC31のNative/Rojo合成で検証したところ、原作者 #487 の `EGGRUMBLE_BalanceMetrics.luau` は **canonical 31 sourceに含まれない独立QA utility**。したがって **既存スロット置換やゲームへの修正組込みは不可能**。追加32番目のGame権威を作らず、既存31源の100%固定照合と独立native QAで実装する。初期の「既存31源のBalanceMetricsスロットを差替える」という古い記述は誤りであり破棄。

## 実修正と証拠の分離
- QAのみ: #487元の `EGGRUMBLE_BalanceMetrics.evaluate` はTEAM 720秒+BR 1500秒でmedian1110秒→`releaseReady=true`という誤合格が存在。改修選択ソースは`overlongCount`と`longestRoundSeconds`を計測し、1200秒超過が1試合でもあればFAIL。これはプレイヤーのラウンドを強制終了するものではない（実ゲームの時間管理#499とは非重複）。
- 生産系 SOURCE: 31スクリプトを一切変えない。実際の公式#555後31源を正規Source/Classのまま非公開Rojo Placeへ再合成し、全31のbytes/source/classを突合。差分0であることを検査。
- ORIGINAL HEAD `438a406ccfda5563053d783d7561797ccd364361`、元BalanceMetrics Git blob `1cb9316faa41f646bf2c18e15c6ddc46fc93bc78`。ドリフトはRED停止。
- OFFはoriginal #487のQAコード完全一致。既存Game/HP/Remote/DataStore/ボット/城卵/ロビー/Item/ART/SCOREの変更ゼロ。
- PC/Android実機・勝敗バランス・美観・FUN・OWNER受入は未実施。ゲームの時間制限バグそのものを修正済と誤記しない。

## CI / 正式RC引継ぎ
- 小CI `.github/workflows/p0d-gq-v3-balance-outlier.yml` はnative LuauとPython固定源回帰。
- 私的大型CI `.github/workflows/p0d-gq-v3-balance-outlier-private31.yml` は**固定正式RC `98a199a4ace7b350e4e909681ef0a7b904a7f942`**（#555含む）を読取専用取り込み、残りの既存作者headとRojoを固定し、31源無変更のnative/Place試験と外部QA単体を実施。
- #220唯一の認証済みCAS writerに正式RCへの**独立QA gateのみ**を採用するか検討依頼する。ゲームロジックへの採用効果はゼロ。#220以外がRCを直接更新しない。main/merge/Publish/支出/Windows操作なし。
- `P0D_PREP_READY` はprivate31の同HEAD成功＋再base最新RC照合を満たしてから宣言。作者個別ACK待ちは停止要因にしない。
