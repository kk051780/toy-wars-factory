# GQ822｜Real44→46 無敵覚醒V2の実ダメージ入口候補

## 非重複の実装
既存 #823 V2純Policy（Git blob 1c38af7f0ed65a7a90b65bbc98b0ab35d54c971c）と、#827の実44ソース全13箇所の直接TakeDamage棚卸しを再利用する。新Damageオーナーを作らない。

元 #815 の真正Real44（run #44376856212）から、元SevenRoleCombat、BotActors、SwarmCombat、NeutralStoneGiant、LobbyCastleModesPreview Host、RealmBattleCore、CastleGuardianRuntime の既存7ソースのみを改変。他37ソース不変。全13箇所の元TakeDamage引数にだけ新InvulRuntime.filterDamageを差し込み、元の被ダメージ計算・HP実際のTakeDamage・スコア処理は変えない。未登録の14番目の直接TakeDamageがあればビルドRED。

新Moduleは二つだけ：一つは #823 原本Policyバイト完全再利用、一つはサーバの試合別Runtimeフィルタ。元HostのSevenRoleCombat.equip直後2箇所にRuntime.attachを最小追加し、Lv1無料の迎撃覚醒Toolを1個供給。サーバが3秒間のARM、最初の正規攻撃を0で受け6〜9秒の全攻撃遮断を管理する。本人/役職/アバター/現在の試合/城生存/卵/旧SHIELDはサーバ照合。死亡・再スポーン・旧試合の操作を拒否し、発動回数は試合stateで保持。

真正44+2=46のNative LuauコンパイルとRojo Source/Classを評価。元44 sourceとPlace byte exactのOFF44に戻せる。元Combat/Swarm/Hostの所有者を増やさず、main/正式RCへの直接書込、Roblox Publish/Robux変更なし。

## 必要な実ゲーム検証
- 今回の範囲は実44の直接TakeDamage13箇所のみ。直接Humanoid.Health代入、落下での非TakeDamage死亡、状態異常の新規CC/ノックバック、非ダメージ敗北、別Real48系統は未接続・未確認。完全無敵の合格と誤報しない。
- 元のHitFXはダメージが0でも表示され得る。専用無敵ラベル、職別立体演出、モバイル/タッチボタンは担当を分けて接続。
- 武神/忍者の単体撃破、魔法使い全方向結界の反撃波など、7役職固有カウンター自体の実Combat/Swarmへの効果接続は未完了。今回のコードで実際の一撃KOが出来るとは言わない。
- アイテムとジャストガード経路は元のItem/Weaponオーナー接続待ち。現時点のToolは無料職技のみ。
- Roblox Studio2client、Android15分、実際の攻撃0/通常被弾復帰、UI視界の妨げ、真のPvP敵に迎撃が成立するかは実機未検証。

## 正式RC受渡し
同じ現正式Core36 HEADでNative/Rojo/OFFと改変原本の固定blobを照合してから #220 唯一認証CAS writerが統合判断。別作者ACK待ちは不要。部分完成の候補を本体完成扱いしない。古いV1の0.9–2.2秒/試合5秒ルールに戻さない。
