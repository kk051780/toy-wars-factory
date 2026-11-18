# EGGRUMBLE｜全7職の短時間完全無敵 P0（Issue #822）

## 今回実装したもの
`InvulnerabilityPolicy.luau` はゲームの無料スキル・拾得アイテム・武器ジャストガードから共通利用できる**サーバー用純Luau状態管理モジュール**。職業ごとの1回時間/回数/CD、全ソース合算最大5秒、全ソース発動間隔18秒、1試合1アイテム・1ジャストガード、重複効果拒否、同じ試合の転職・再スポーンやクライアント不正による無敵再付与拒否を担う。

7職の技は初期Lv1で無課金利用を前提。卵運搬中・既存SHIELD中・ダウン中は無敵技を始められず、無敵中は卵の取得/納入・攻城・フィニッシュを無効、通常攻撃のみ威力60%。属性/通常/落雷/水中/炎上等を問わずダメージ倍率を0にする**判定API**（`damageMultiplier`）とCC付与阻止（`allowNewStatus`）を提供。直接HPや属性Damageに書き込まず、既存単一サーバDamageOwnerの被害適用**直前**に接続する契約。

`newRound`は試合ごとに新規state。`activate`時点で回数と合計秒数を原子的に予約。`isInvulnerable`/ `damageMultiplier`/ `allowNewStatus`/ `attackMultiplier`/ `allowObjectiveAction`/ `cancelOnObjectivePickup`/ `cancelAvatar`/ `snapshot` APIはすべて現在の試合・現在のアバター・生存・チーム/BR・Server Verifiedを要求する。クライアントからの直接呼出しや時間の受信を認めない。

## シールドとは別
旧ITEM `SHIELD` は別の防御要素。本モジュールを使用するには旧SHIELDが有効でないことを既存ITEM責任者が確認する。無敵は**正規ゲームダメージを受けない**状態。ただし非ダメージの試合敗北・場外リセット・退室・不正対処・デスポーンを無効化しない。

無敵中のプレイヤーは有利になり過ぎないよう攻撃威力低下と攻城/卵目的制限を受ける。味方の魔法使いの蘇生や職業HP・自然回復を置き換えない。なかでも卵を持ったまま逃げるための無敵は許可しない。

## 重要：まだライブの完全無敵ではない
このPRのSource実装/Native VM成功だけでは本物の Roblox で全てのダメージが遮断できた証拠にならない。旧Combat/Host、Swarm、LSS/RealmCore、天候、DOT、落下、ステージ/ボス、PVPステータスなど全ダメージの**単一のサーバー適用入口**への接続が必要。ForceFieldを追加して演出だけ完了扱いしない。攻撃者別の属性ダメージ規則や得点権限を二重で実装しない。

## CIとRC統合の受入
固定実ソース由来のNative Luau試験で7職回数/継続、無敵中攻撃係数、全ダメージ係数0、CC保護、卵Pickupによる取消、別試合・別アバター・旧時刻拒否、二つの故障変異（無敵5秒上限改ざん、ダメージ漏れ）を確認。過去正式RC36 sourceを一切変更せず、新Luau1本のみの提案。OFFは本Policy源を合成しない、元Core36が完全そのまま。

**実ゲームコード接続（未完）**：#220唯一認証RC writer/Combat ownerが最新正式RC HEADを取得し、旧#489 SHIELD/卵、#766属性、#765 HP回復、#777 Mage、#806 PvP CC、#802天候との一元damage/CC/Objective APIに接続したビルドをNative+Rojo Source/Class、OFF元Core36、Studio二人15分、低性能Android15分で受入。未接続を「無敵遊べる」と報告しない。

**進捗の区別**：要件共有◯／Policy源◯／Native VM検証はworkflow結果による／既存Combat接続×／正式RC採用×／Studio×／Android×。main/Roblox公開/Robux課金/追加費用禁止。原作者個別ACKを待たず既存実装者が引継ぎ、重複PRを排除。
