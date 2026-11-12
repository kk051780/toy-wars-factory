--!strict
-- ORIGINAL S2+ rare fantasy field catalogue; presentation contracts, not rewards.
-- 4 fantasy biomes inherit design intent WF-13..WF-24 from master Issue #222.
local Catalog = {}

Catalog.VERSION = "P0D_RARE_FOUR_REALMS_V1"
Catalog.MAX_SCENE_PARTS = 220
Catalog.WORLDS = {
    SPACE = {
        title = "星くず銀河城",
        label = "✨ ほしの おしろ",
        center = {x=240,y=0,z=0},
        color = {r=132,g=87,b=227},
        forward = "SPACE_STAR_BRIDGE",
        side = "SPACE_CRATER_PATH",
        scenic = "宇宙のリング・流星の橋・星くじらの立体像",
        mechanic = "上段と下段の無料侵攻を選べる。紫ドームは見た目のみ。WF13の局所重力とは未接続",
        child_action = "むらさきの みちを わたる",
        tactical = "乗り物役が上の輪を目印にし、戦士が下の橋を護衛して陽動",
        defender = "上段下段とも城から見渡せ、対戦側も同じ無料道を使用できる",
        promo_7s = "宇宙の城には道が2つ！星くじらを見つけられる？",
        rare_neutral_sculpture = "星くじら（像・NPCではない）",
        phase = "SCENE_ONLY",
    },
    CELESTIAL = {
        title = "光の天空神殿",
        label = "☁ そらの しんでん",
        center = {x=0,y=30,z=240},
        color = {r=255,g=219,b=122},
        forward = "SKY_GOLD_RAMP",
        side = "SKY_PEARL_ROAD",
        scenic = "白い雲の庭園・金の鐘・虹羽ペガサスの立体像",
        mechanic = "金色と白色の2本の無料道。鐘は警報の見た目だけで音や扉解除は未実装",
        child_action = "きんいろの さかを のぼる",
        tactical = "魔法職が金色の表道に注意を向け、罠職が真珠の裏道をカバー",
        defender = "双方見える色+雲の絵柄、無料で上り下りできる",
        promo_7s = "雲を登った先に金色の城！ペガサスを発見！",
        rare_neutral_sculpture = "虹羽ペガサス（像・NPCではない）",
        phase = "SCENE_ONLY",
    },
    EMBER = {
        title = "紅蓮の魔界城",
        label = "🔥 あかい おしろ",
        center = {x=-240,y=0,z=0},
        color = {r=241,g=106,b=63},
        forward = "EMBER_STONE_BRIDGE",
        side = "EMBER_SHADOW_PATH",
        scenic = "赤い歯車・安全な光る溶岩の見た目・マグマモグラの立体像",
        mechanic = "赤い岩道と灰色の防衛迂回路。溶岩は無害な見た目で即死しない",
        child_action = "あかい いわみちを わたる",
        tactical = "ゾンビ職の囮を赤い橋に置き、戦士の仲間が灰色の道を進む",
        defender = "橋の入り口と出口に予告看板があり、守備側も迂回できる",
        promo_7s = "溶岩の横を走れ！赤いお城の秘密の道！",
        rare_neutral_sculpture = "マグマモグラ（像・NPCではない）",
        phase = "SCENE_ONLY",
    },
    ECLIPSE = {
        title = "光と闇のはざま",
        label = "🌙 ひかりと やみ",
        center = {x=0,y=0,z=-240},
        color = {r=102,g=117,b=230},
        forward = "ECLIPSE_SUN_PATH",
        side = "ECLIPSE_MOON_PATH",
        scenic = "金の太陽と青紫の月・光闇の城・双面幻獣の立体像",
        mechanic = "太陽道・月道の両方を常に歩ける。光る装飾のみ時刻で変わり閉じ込めない",
        child_action = "たいようか つきを えらぶ",
        tactical = "魔獣職が月道を警戒し、忍者が太陽道で回り込みの候補にする",
        defender = "光と月のアイコンを常時表示。色覚だけに頼らず両方通行できる",
        promo_7s = "太陽と月の城！今はどっちの道が光る？",
        rare_neutral_sculpture = "双面の幻獣（像・NPCではない）",
        phase = "SCENE_ONLY",
    },
}

Catalog.ORDER = {"SPACE","CELESTIAL","EMBER","ECLIPSE"}
Catalog.ALL_ROUTES = {
    "SPACE_STAR_BRIDGE","SPACE_CRATER_PATH",
    "SKY_GOLD_RAMP","SKY_PEARL_ROAD",
    "EMBER_STONE_BRIDGE","EMBER_SHADOW_PATH",
    "ECLIPSE_SUN_PATH","ECLIPSE_MOON_PATH",
}
function Catalog.validate(): (boolean,string)
    if #Catalog.ORDER~=4 or #Catalog.ALL_ROUTES~=8 then return false,"counts" end
    local names={}
    local routes={}
    for _,id in ipairs(Catalog.ALL_ROUTES) do
        if routes[id] then return false,"duplicate route" end
        routes[id]=true
    end
    for _,id in ipairs(Catalog.ORDER) do
        local w=Catalog.WORLDS[id]
        if not w or names[id] or not routes[w.forward] or not routes[w.side] then
            return false,"bad world or missing route"
        end
        if w.forward==w.side then return false,"single attack route" end
        names[id]=true
        if #w.child_action<5 or #w.tactical<8 or #w.defender<8
            or #w.promo_7s<8 or w.phase~="SCENE_ONLY" then
            return false,"missing child tactic and truth"
        end
    end
    return true,"four worlds and eight free routes"
end
return Catalog
