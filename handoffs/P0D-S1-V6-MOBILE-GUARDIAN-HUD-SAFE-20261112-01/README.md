# P0D S1 V6 — Guardian罠のスマホ下部ボタン干渉を避ける独立候補

対象：`TRAP_RAIDERS` / `p0d-siege-v19` / `P0D-S1-KIDS-RC01`

担当：`CHAT-S1-V6-GUARDIAN-MOBILE-HUD-SAFE-20261112-01`

ソース固定：公式RC `1263a03701211a652b99b91d2339575dc8104eff` の `src/client/HUD.client.luau` Git blob `ee594fbc34e6bf938518fae32c0642c852f11f9e`。

## 課題と設計

現行GuardianTrapは画面**左下2%**、下から16pxに固定。スマホのRoblox標準移動スティック領域と重なる可能性がある。これは実機で確認したバグではなく、**事前UI安全性リスク**である。

今回の候補は**罠ボタンの位置だけ**を変え、右下の「攻撃」ボタンの**上**に置く。

- 攻撃（変更なし）：幅126・高さ88、右端余白14px、下余白16px
- Guardian罠：幅110・高さ74、右端余白30px、下余白110px
- 同じ左端で縦積み。両ボタン間の空白6px。移動スティックを想定した左32%から離れる
- 最小対象は**640×360の横画面**。上部の案内パネル（左から中央・y108〜175）や下部説明テキストと重ならない
- 667×375、812×375、1024×576、1280×720、1920×1080についても矩形検査。これより小さい画面・画面回転や端末の表示領域差は実機で追加評価
- 攻撃、役職選択、T/Fキー入力、RemoteEvent、SEQ、アンチチート、ゲーム中の罠可視性、ボス表示コードはバイト単位で元のまま。サーバー変更なし

## 正本取り込み条件

候補ファイルは `candidate/src/client/HUD.client.luau`。**公式RCの上書きではない**。#220統合担当だけが、同一SHAの最新版RCに対して候補を採用するか判断する。UIが数値上重ならないことと「実機タッチで操作できること」は別。実機では**移動しながら罠をタップできるか／端末の安全領域とジャンプボタンに重ならないか**を確認する。問題があれば候補を修正する。

テスト：本物のGit原本を固定blob照合→原本と候補の差分が**位置の1行のみ**であることを検証→横画面6種類の矩形配置・危険な配置5種類の負例→元と候補のネイティブLuauパーサ確認。ネイティブ文法検査もRoblox Studio実機の保証ではない。

```sh
python3 handoffs/P0D-S1-V6-MOBILE-GUARDIAN-HUD-SAFE-20261112-01/tools/verify_guardian_mobile_layout.py --repo .
python3 handoffs/P0D-S1-V6-MOBILE-GUARDIAN-HUD-SAFE-20261112-01/tools/verify_guardian_mobile_layout.py --selftest
python3 -m unittest discover -s handoffs/P0D-S1-V6-MOBILE-GUARDIAN-HUD-SAFE-20261112-01/tests -v
```

報告正本：[Issue #229](https://github.com/kk051780/toy-wars-factory/issues/229)、[共通 #218](https://github.com/kk051780/toy-wars-factory/issues/218)、[S1 #220](https://github.com/kk051780/toy-wars-factory/issues/220)

禁止：main、公式RC、merge、本番Roblox公開、課金・支出、Codexの小片検証、P0-A/B/C、既存5自動化の無断変更。
