# EGGRUMBLE GQ822 | 最新正式Private Real55→56 7職迎撃カウンター

**2026-11-19 OWNER最新**。旧短時間無敵0.9–2.2秒/V1は廃止。無敵覚醒V2は「迎撃構え3秒→敵の実ヒットを被害0→6〜9秒完全無敵→役職固有の逆転技」。

## 正本と重複回避
- 最新正式RC private V3 Companion：`rc/p0d-s1-kids-rc01` の Real55 HEAD `a6020867fac80fa3b2ca47478625873fc6f3678e`（#834）。S1 rich51は変えない。
- 同HEAD成功した正式 Real55 source + Place artifact：GitHub Actions #44393525211。台帳は `B_REAL55_RECEIPT.json`。
- #823 は7職の無敵覚醒純Luau Policyの正本。#830は旧Real44→46に最初の13箇所の被弾前ゼロ判定を載せた元差分。**今回のReal55にはこの成果がすでに含まれるため、旧44→46を再採用しない。**
- #825は無双/確変・自然チャージの本体。Real55の `session.swarm.musouActive(p)` と覚醒待機/覚醒の相互排他を完全保持。
- #800/#815/#821の既存単一Swarm/実呪印・中立8種、#808のショップ、#831のロビーを上書きしない。

## Real56追加する「実反撃」の範囲
**元55ソース中53本を全バイト無変更。元の2本だけを限定改変＋新Module1本（合計56本）。**

| 職業 | 新しい本物のソース連動 |
|---|---|
| 武神 WARRIOR | 最初の攻撃者が実Playerのときのみ、元SevenRoleCombatのPvP所有者が指名反撃。サーバが実人物・敵Team/BR・距離18stud・射線を2回照合。0.65秒の一つのPartless Highlightで予兆を示し、攻撃者が距離16stud以上へ逃げる/壁へ逃げれば不成立。満HPでは非致死、HP25%以下は判定が揃った場合のみ決着、最大40% MaxHP |
| 忍者 NINJA | 同じ元Combatの一対一反撃だがHP20%以下の閾値／35% MaxHP上限。他のPlayerや無関係な近くの中立を殺さない |
| 魔法使い MAGE | 実3撃を防いだあと、真正の近くの中立敵に対して既存Swarmの `damageFromPlayer` を呼び、半径14studの20ダメージ反波。元Swarmの射線/距離/Hit budget/KO/Scoreは変更せずに実HPを減らす |
| 超能力者 TRAPPER | 実3撃で同一Swarmの半径10stud/18ダメージ中立反撃を1回。対人への鏡面反射追加ダメージはまだ未接続 |
| マッドサイエンティスト BUILDER | 実2撃で同TEAM・本人半径10studにいる味方へ3秒間50%軽減。元の被ダメージ入口で `allyMultiplier=.5` を掛ける（城HP・本人・敵・既存SHIELDには適用しない） |
| 魔獣使い BEAST | 実2撃で同一Swarm半径11stud/28ダメージ。陸海空で実移動/ノックバック追加は未接続 |
| 呪術師 ZOMBIE | 実3撃で元Swarmの8ダメージ呪印攻撃1回。既存CurseConversionPolicyの実封印/転向条件（体力・印数等）を勝手に上書きせず、条件が揃うまで一撃で味方化しない |

**固有反撃は一回の覚醒中一度だけ**、Role Policy #823 `claimCounter`でサーバ認証。中立の本物HP減少を確認した場合のみ、上限24秒内の1.5秒連鎖延長を認める。ダメージ発生させるのは元SingleCombat/Swarmであり、新Moduleは一切Humanoid:TakeDamage/HP直書き・Remote/Store/Scoreなし。

## 反撃の見た目/攻撃側の対処
PvP指名反撃にはサーバーのHighlight一つを0.65秒だけ出し、逃げ・射線遮断で回避可能。今後7職それぞれに専用視覚/audioを実装する段階までは「演出完成」扱い禁止。全画面フラッシュ・常時HUD・過剰Partは追加しない。新しい味方シールドは**味方完全無敵ではなく半減**、他の無敵・卵・無双と併用しない。ラウンド/城生存/アバター/職の失効と異常なPlayer識別子をサーバで再検証。

## 重要な限界 / RED残件
- Roblox Studio 2人試遊とAndroid15分、実際の7職演出・面白さは未検証。
- 旧Real55の直接TakeDamage13箇所以外のHealth直接書込/落下/CC/ノックバックを含む「全ダメージ/全状態異常ゼロ」はまだ未保証。
- 中立兵の指名1体確殺(WARRIOR/NINJA)は本当の加害Neutral instance IDの取得が必要。現段階ではデタラメな近隣NPCを処刑する代用は**実装しない**。
- 魔法使いはまず中立兵へ正規反波。複数Playerへの対人反撃波は既存Combatの照合/可視演出/妥当なPVP被ダメ上限を整備してから追加。
- 無双が現在発動している場合、元Real55の `musouActive` ガードを保持して無敵迎撃構えを拒否。攻守同時無敵で無限稼ぎを作らない。
- Real55の55ファイル/Source/Classの原本を再取得した際、差分不一致が一つでもあれば **RED fail-close**。
- 正式RC更新は#220の唯一認証済みwriterのみ。新候補は私人用56 source Placeを検証するまで正式受入と見なさない。原作者個別ACK待ちは不要、main/Publish/Robux/取引処理変更は禁止。

## 証拠と戻し
`compose_real56.py` は本物の最新Real55 Source SHA256台帳・今の正式HEAD・初期#830 Runtime Git blob・#823 Policy Blobを照合し、現Real55 Runtimeが旧Runtime+元Musouガードのみであることを証明した後に限定Overlayする。元55の53ソース完全一致、原Combatの追加PvPダメージ1箇所が同じHP owner内、元Swarm一つのみ、OFF55 Rojo Place元本のバイト比較。GitHub Native VMは5職のリアルCounter +旧Runtime事実上7職動作、Barriers/Damage変異RED。これは実機の証拠ではなく、実ソース採用候補の証拠。
