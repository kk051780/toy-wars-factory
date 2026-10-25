# 取り込み承認待ち

観測時点: 2026-10-25T00:15:57.147900+00:00

| PR | 内容 | 区分 | 現在headの検査 |
| --- | --- | --- | --- |
| [#35](https://github.com/kk051780/toy-wars-factory/pull/35) | 生産3件・ウェーブ2件・敗北リセット1件の回帰検査。ゲーム本体の変更なし。 | 回帰検査追加 | [合格](https://github.com/kk051780/toy-wars-factory/actions/runs/40114787373) / `1fdc549d` |
| [#38](https://github.com/kk051780/toy-wars-factory/pull/38) | 戦場・工場・ロビーの床だけ衝突を有効化。追加5検査が合格。 | ゲーム本体修正 | [合格](https://github.com/kk051780/toy-wars-factory/actions/runs/40137069031) / `b8e543ad` |
| [#40](https://github.com/kk051780/toy-wars-factory/pull/40) | 工場アップグレードの不足金額・ぴったり購入・上限・収入の4検査。ゲーム本体の変更なし。 | 回帰検査追加 | [合格](https://github.com/kk051780/toy-wars-factory/actions/runs/40138956623) / `f172f711` |

承認する場合の返信: **#35・#38・#40のmain取り込みを承認**

対象は上記コミットのmain取り込み。Roblox公開・課金・外部モデル再実行の承認は含まない。
承認後にhead・CI・競合を再確認し、変更があれば承認を流用しない。
