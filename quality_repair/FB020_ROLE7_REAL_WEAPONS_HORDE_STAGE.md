# [FB020 / Code Slice 2] RC82 7職の持ち武器・通常攻撃を同一実Placeに累積

更新元：2026-11-15 OWNER「実装意識して進めろ。開発のタイパ悪すぎる」→「つぎ」。
#364（OWNER試遊正本）・#219（職別のゲーム設計）・#470（品質ゲート）・#220（RC統合）に接続。**元作者#297のGame/HUD書込みは競合禁止。**

## 実装証拠（Studio用私的Place、GitHub public にbinary/完全ゲーム源はpushしない）
- 先にユーザーに渡した風走り修復Place SHA256: `89e67cc78cdc23ccb63284bd61cd038e3b2d7a7f70f8f084dc500d7f54a06e1f`。
- **累積FB020 Role7武器/中立実攻撃 Place SHA256** `9f4e32400dd6e098e526b59f9d4de38c069b938e1c8795a3b50483b69958278a`、**791171 bytes**。
- 専用ZIP `TRAP_RAIDERS_RC82_FB021_WEAPONS_COMBAT_PLAYTEST.zip`、**223106 bytes**、SHA256 `d7eb2bd028026629c0de4a63e98176890105c51aec0fa42ef4740a07ea6db150`。
- 82 script / **GameとTrapRaidersHUDの2源のみ変更**、他80源body byte-exact、元風走り修正保持。
- Game source Git blob `a7b047f5516b53174e7d23f66420aeef8a0c5325`→`58fa069a01be430579a83782e684e7c60e72d7eb`。
- HUD source Git blob `34e3b4548e0dba2ba6262059aa1c165f6405b0fb`→`65737fe0dcb51c7bf04371738b23bec1bfec625f`。

## 新しく実コードに追加した動作（予定仕様ではなくソース差分あり）
1. **職選択/リスポーンで3D武器を実キャラに装着**：戦士=大剣、魔法使い=杖、暗殺者=双短剣、トラッパー=罠銃、建築士=大槌、魔獣使い=槍、ゾンビ使い=大鎌。武器部品はServer Gameで生産+Weld（原キャラのRightHand/Right Arm、暗殺者のみLeftHand追加）、2-3非衝突parts/職。変更職の古武器除去、再スポーン再装備、チーム再編時除去。
2. **通常F攻撃を7種の本物の中立兵Hitに変更**：元Gameの唯一のATTACK / seq / cooldown内でSevenJob選択ACKを検査。戦士広角3斬、魔法使い2方向の魔法、暗殺者両手交差、罠師前/左右散弾、建築士大槌一撃+3段目追撃、魔獣使い前方槍二突き、ゾンビ使い前後左右の鎌範囲。すべて元MusouHorde:hitを通すためray LOS/本物HP減/KOs/被弾ポップアップ/個人成績の権威は一意。従来の保存レベル・道場・earned倍率を各職に継承し元上限40を守る。ゲームのPvP/卵/得点の攻撃権威は無変更。
3. **7種専用クライアントVFX**：各職別の色/サイズ/斬撃回数/軌道、同じF/スマホボタン、接触とKOは見た目だけで判定しない。選んだ職業武器名を攻撃ボタンに表示。

## 確認済 / 未完了
- XML 82/82 Script再読、inventory順と80 unchanged Git blob、一意Game Remote / source anchor / 改造後同一内容ZIP検証 / 元親SHA差異fail-closed / 7職定義の静的自動検査 **34/34 PASS**。
- ネイティブLuau compiler/Rojo/native game実行/Studio 1&2client/Android **NOT_RUN**。したがって**SOURCE_PATCH / STATIC_PASS / PRODUCT_NO_GO**。実装したと報告できるのは武器/通常PvEだけで、フル7職能力（回復/蘇生/ワープ/騎乗など）は**未実装**。技能体験の実機合格も未達。
- 職業別通常PvP攻撃/魔獣の真正Follow・城室内侵入・拾得物・ロビー物理導線は**別未完P0**。企画室の旧原案が消えたとは扱わない。

## 最短の公式受渡
既存元作者PR #297が真正最新Game/HUDに**変更関数だけ** rebaseしLuau native→Rojo source exact/rollbackを通す。私的ZIPに`SOURCE_PATCH.py`を同梱し元風走りPlaceに対する再現性を担保。B #220認証writerの最新同HEAD nonforce CAS以外で公式branchへ実Game書込禁止。#470品質writerはStudio/Android/対戦実測しOWNER不合格を同FBで再開。YELLOW修正待ちで開発RC停滞不可、RED（構文/権威/本体ソースドリフト/CI/CAS）だけ停止。