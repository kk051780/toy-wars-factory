# GQ8 CROSSLANE｜陸海空＋自然回復＋魔法使い蘇生（真正37スクリプト）

## 新規の仕事は差分統合検査のみ
既存の重複除外：
- PR #764：Realm34（飛行機・艦砲・飛行獣・海中モンスター）
- PR #775：自然回復33（先行PR #773の純Policyを再利用）
- PR #777：Mage32（非致死のHP20%以下ダウン・味方の魔法使いが3秒で蘇生）
- PR #780：Realm34＋Regen33 を36へ同時合成した既存品質ゲート。**作り直さない**。

今回新しいゲームルール・HP権限・Hostを複製しない。唯一の新しい工程は「#780の真正36に、#777の元魔法使いModule1と元HostのMageインポート/2箇所の装備Hookだけを追加して37を検査」。

構成：31元ゲームScripts + 3 Realm + 2 Regen + 1 Mage = **37**。元ゲーム既存30ソース完全一致・元Host1本の2機能接続だけの変更・Combat/Swarm/Store/スコア/ラウンド所有者を追加しない。
真正31/36/32はそれぞれ固定SHAの先行PRコンポーザを使う。原作者ファイルは直接改変せず、差分Hostの文字列整合で二重hookや見知らぬ変更をRED拒否。

## 重要な検査
- Native Luau compile37/36/31
- Rojo37/36/31 Source+Class exact
- ソース由来構成と名前に対する負例：旧Combat改変、Host重複Hook、Mage Module重複、元ソース破損
- 正式RC最新SHA＝同一正式31バイナリ成功Run HEAD＝採用候補評価後RC HEAD
- original31へのOFF完全巻戻しと、Mageだけ外して先行36へ戻す可逆性
- ランタイムの初期機能試験は先行PR #775/#777 のVM証拠を再利用し、今回は3レイヤーの**共存ビルド証拠**を作る。

## 残すべきYELLOW/RED
YELLOW：Studio2client、Android15分、画面での属性、実際の魔法使いのダウン→蘇生/自然再生の同時挙動、1-hit lethal-downed未接続、現行rich51への完全適用。**QA成功はゲーム完了ではない**。
RED：同じHostへの2重hook、原本Game/Combat/Swarm/Score/Store変更、同一HEAD未照合、32/36/37ルート不整合、元31に戻せない、別端末の危険なHP操作。見つかれば正式採用不可。

## 正式RCの受渡し
#220 の唯一認証済みRC writerだけが、現正式HEADへsource selection→同HEAD Native/Rojo/rollback→nonforce expected-SHA CAS/readbackを実行する。原作者の個別ACK待ちは不要。main/公開/追加課金禁止。今回のPRは**正式RCの書込みを行わない独立QA**。
