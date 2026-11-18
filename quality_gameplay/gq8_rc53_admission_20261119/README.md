# GQ8 Real53 正式RC受入・独立リハーサル

FEATURE_ID: GQ8_REAL53_FORMAL_ADMISSION_GUARD_20261119

独自レーンは **真正Real53の正式RC受入前の独立検証** のみ。キャラ/フィールド/Combat/Host/Swarm/Item/Shop/HUD/Balanceの元作者ソースに変更を加えない。

- 公式RC: rc/p0d-s1-kids-rc01 @ f77b4d4393d9e9b19b65566413432a7a9f13962b（Core36）
- 最有力候補: PR #826 @ 96ac3b4caa2f649f98c9e093c864c39555f3616a（Real53）
- 元の合格run: #44390806767 Native/Rojo/OFF49
- 親候補: #825 Real49 @ b49350c8b8aaba561c9e0839d27fc5fc275c3a32 / #815 Real44 @ d5c13082d4987a8c89588a12b81edc73adc945ce / 既存 #816/#808 4 original shop sources
- 真正PRIVATE Place（公式ではない）: 572030 bytes、SHA256 47b49a5d8ae758071af8eb5faf1ae8bd247d01f6dfe39557a502bd98dce15690
- main/公開/課金/経済権限/正式RCへの直接書込なし

## このPRの新規防護
1. 公式RC SHAの再確認。公式branchが前進していればfail closed。
2. 元#826真正同一HEAD Native/Rojo成功run証拠の再取得。
3. 実53ソース個別のSHA256/Route/Class/サイズと受入レシートを照合。原49本不変＋ショップ4本のみ、戦闘・Swarm単一権威、実ダメージ13経路を検証。
4. 9領域のソース存在を機械可読ledgerで記録する。ただしsource存在＝実際に楽しい、ではない。
5. 不正なreceipt変異4種類を拒否し、Luau53ソースを独立Native compile、Rojo再ビルドで候補Place 1byte一致を要求。
6. OFF49 Placeを退避し、最新RC入替え後は直前正式RCへの逆転採用を可能にする。

## RC統合の残責任
本PR自体はPREP判定であってRC採用ではない。#220認証済みwriterによる fresh expected-SHA / non-force CAS、正式RCの53ソースprofile設定、同HEAD Native/Rojo/source lock/OFF、安全なreadback、容量証拠、台帳ACKが必要。無認証のmergeやbranch直pushはしない。Studio2client・Android15分・人間FUN/ARTはNOT_TESTED/NO_GO。

後継者は同じFEATURE_IDと固定SHAを引き継ぐ。原作者の個別ACKは不要。最新候補が前進した場合はソース再確認・再CIを行い、旧候補へ戻さない。
