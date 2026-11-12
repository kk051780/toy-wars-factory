-- P0D D18: six distinct manually-authored V5 sky-sea-fantasy archetype flagship source-only previews.
-- GENERATED, DO NOT EDIT. python tools/generate_catalog.py --check
-- No Roblox entitlement, combat, spawning, persistent inventory or reward logic.
local C = {}
local DEFINITIONS = {
    ["TRCA-BE-045"] = {
        ["archetype"] = "BE_THUNDER_CLOUD_GUARD",
        ["category"] = "BE",
        ["category_ja"] = "魔獣",
        ["id"] = "TRCA-BE-045",
        ["name"] = "天鼓の雷獣",
        ["palette"] = {
            ["cream"] = {
                245,
                245,
                213,
            },
            ["dark"] = {
                43,
                40,
                97,
            },
            ["gold"] = {
                247,
                200,
                54,
            },
            ["indigo"] = {
                84,
                67,
                155,
            },
            ["sky"] = {
                102,
                217,
                238,
            },
        },
        ["parts"] = {
            {
                ["color"] = "indigo",
                ["far"] = true,
                ["group"] = "body",
                ["name"] = "胴",
                ["position"] = {
                    0,
                    0.1,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Ball",
                ["signature_tag"] = "support",
                ["size"] = {
                    1.8,
                    1.1,
                    1.2,
                },
            },
            {
                ["color"] = "cream",
                ["far"] = true,
                ["group"] = "head",
                ["name"] = "大きい頭",
                ["position"] = {
                    0.8,
                    0.7,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Ball",
                ["signature_tag"] = "support",
                ["size"] = {
                    1,
                    0.94,
                    1,
                },
            },
            {
                ["color"] = "gold",
                ["far"] = true,
                ["group"] = "head",
                ["name"] = "左耳",
                ["position"] = {
                    0.8,
                    1.3,
                    -0.36,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Ball",
                ["signature_tag"] = "support",
                ["size"] = {
                    0.35,
                    0.44,
                    0.35,
                },
            },
            {
                ["color"] = "gold",
                ["far"] = true,
                ["group"] = "head",
                ["name"] = "右耳",
                ["position"] = {
                    0.8,
                    1.3,
                    0.36,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Ball",
                ["signature_tag"] = "support",
                ["size"] = {
                    0.35,
                    0.44,
                    0.35,
                },
            },
            {
                ["color"] = "gold",
                ["far"] = true,
                ["group"] = "mane",
                ["name"] = "たてがみ縦",
                ["position"] = {
                    -0.08,
                    1.45,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    35,
                },
                ["shape"] = "Block",
                ["signature_tag"] = "bolt_mane",
                ["size"] = {
                    0.35,
                    1.3,
                    0.28,
                },
            },
            {
                ["color"] = "sky",
                ["far"] = true,
                ["group"] = "mane",
                ["name"] = "稲妻枝",
                ["position"] = {
                    -0.45,
                    1,
                    -0.4,
                },
                ["rotation"] = {
                    0,
                    0,
                    -35,
                },
                ["shape"] = "Block",
                ["signature_tag"] = "bolt_mane",
                ["size"] = {
                    0.35,
                    0.95,
                    0.25,
                },
            },
            {
                ["color"] = "gold",
                ["far"] = true,
                ["group"] = "drum",
                ["name"] = "胸の太鼓",
                ["position"] = {
                    0.45,
                    0.2,
                    1.08,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Cylinder",
                ["signature_tag"] = "sky_drum",
                ["size"] = {
                    0.83,
                    0.76,
                    0.25,
                },
            },
            {
                ["color"] = "dark",
                ["far"] = true,
                ["group"] = "drum",
                ["name"] = "太鼓の目",
                ["position"] = {
                    0.45,
                    0.2,
                    1.22,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Ball",
                ["signature_tag"] = "sky_drum",
                ["size"] = {
                    0.28,
                    0.28,
                    0.18,
                },
            },
            {
                ["color"] = "sky",
                ["far"] = true,
                ["group"] = "tail",
                ["name"] = "雲しっぽ根",
                ["position"] = {
                    -1,
                    0.48,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    25,
                },
                ["shape"] = "Block",
                ["signature_tag"] = "cloud_tail",
                ["size"] = {
                    0.8,
                    0.36,
                    0.4,
                },
            },
            {
                ["color"] = "cream",
                ["far"] = true,
                ["group"] = "tail",
                ["name"] = "雲しっぽ先",
                ["position"] = {
                    -1.45,
                    0.85,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Ball",
                ["signature_tag"] = "cloud_tail",
                ["size"] = {
                    0.82,
                    0.72,
                    0.82,
                },
            },
            {
                ["color"] = "indigo",
                ["far"] = true,
                ["group"] = "body",
                ["name"] = "左足",
                ["position"] = {
                    0.6,
                    -0.53,
                    -0.4,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Ball",
                ["signature_tag"] = "support",
                ["size"] = {
                    0.45,
                    0.42,
                    0.35,
                },
            },
            {
                ["color"] = "indigo",
                ["far"] = false,
                ["group"] = "body",
                ["name"] = "右足",
                ["position"] = {
                    0.6,
                    -0.53,
                    0.4,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Ball",
                ["signature_tag"] = "support",
                ["size"] = {
                    0.45,
                    0.42,
                    0.35,
                },
            },
        },
        ["pose_offsets"] = {
            ["idle"] = {
            },
            ["loss"] = {
                ["head"] = {
                    ["dy"] = -0.2,
                },
                ["tail"] = {
                    ["dy"] = -0.18,
                },
            },
            ["tap"] = {
                ["drum"] = {
                    ["rz"] = 8,
                },
                ["head"] = {
                    ["dy"] = 0.15,
                },
            },
            ["win"] = {
                ["mane"] = {
                    ["dy"] = 0.2,
                },
                ["tail"] = {
                    ["dy"] = 0.18,
                },
            },
        },
        ["provenance"] = {
            ["atlas_sha256"] = "cf5ec26836842ce55a764c5ad66c711f00da0ed4cc30d80dad0df851e2656e01",
        },
        ["rarity"] = "レジェンド",
        ["signature_silhouette"] = "稲妻の三つ編みたてがみ、胸の太鼓、上向きの雲しっぽの雷獣",
        ["signature_tags"] = {
            "bolt_mane",
            "sky_drum",
            "cloud_tail",
        },
        ["story"] = "雷が苦手な小鳥を最後まで置いていかなかった。天鼓の雷獣は、その日の出来事を忘れないために、雲上の誓いの鐘に羽根形の導電紋と雲の房を一つ残した。持ち主が負けた日も同じ表情で迎える。",
        ["world"] = "雷鳥の空庭",
    },
    ["TRCA-SP-054"] = {
        ["archetype"] = "SP_TIDAL_LIGHTHOUSE",
        ["category"] = "SP",
        ["category_ja"] = "魔法",
        ["id"] = "TRCA-SP-054",
        ["name"] = "灯台の大潮",
        ["palette"] = {
            ["coral"] = {
                252,
                145,
                143,
            },
            ["deep"] = {
                23,
                91,
                134,
            },
            ["gold"] = {
                251,
                205,
                106,
            },
            ["teal"] = {
                65,
                177,
                183,
            },
            ["white"] = {
                241,
                251,
                253,
            },
        },
        ["parts"] = {
            {
                ["color"] = "deep",
                ["far"] = false,
                ["group"] = "wave",
                ["name"] = "波の土台",
                ["position"] = {
                    0,
                    -0.45,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Cylinder",
                ["signature_tag"] = "support",
                ["size"] = {
                    2.2,
                    0.3,
                    1.2,
                },
            },
            {
                ["color"] = "teal",
                ["far"] = true,
                ["group"] = "wave",
                ["name"] = "左波柱",
                ["position"] = {
                    -0.9,
                    0.4,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    -20,
                },
                ["shape"] = "Block",
                ["signature_tag"] = "wave_gate",
                ["size"] = {
                    0.36,
                    1.85,
                    0.4,
                },
            },
            {
                ["color"] = "teal",
                ["far"] = true,
                ["group"] = "wave",
                ["name"] = "波の上辺",
                ["position"] = {
                    -0.4,
                    1.35,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    23,
                },
                ["shape"] = "Block",
                ["signature_tag"] = "wave_gate",
                ["size"] = {
                    1.25,
                    0.28,
                    0.4,
                },
            },
            {
                ["color"] = "white",
                ["far"] = true,
                ["group"] = "wave",
                ["name"] = "波の泡冠",
                ["position"] = {
                    0.28,
                    1.3,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Ball",
                ["signature_tag"] = "wave_gate",
                ["size"] = {
                    0.68,
                    0.3,
                    0.45,
                },
            },
            {
                ["color"] = "white",
                ["far"] = true,
                ["group"] = "beacon",
                ["name"] = "灯台の塔",
                ["position"] = {
                    1,
                    -0.02,
                    -0.25,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Cylinder",
                ["signature_tag"] = "lighthouse_beacon",
                ["size"] = {
                    0.44,
                    1.3,
                    0.44,
                },
            },
            {
                ["color"] = "coral",
                ["far"] = true,
                ["group"] = "beacon",
                ["name"] = "灯台屋根",
                ["position"] = {
                    1,
                    0.75,
                    -0.25,
                },
                ["rotation"] = {
                    0,
                    0,
                    15,
                },
                ["shape"] = "Block",
                ["signature_tag"] = "lighthouse_beacon",
                ["size"] = {
                    0.7,
                    0.28,
                    0.66,
                },
            },
            {
                ["color"] = "gold",
                ["far"] = true,
                ["group"] = "beacon",
                ["name"] = "灯台の光",
                ["position"] = {
                    1,
                    1.08,
                    -0.25,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Ball",
                ["signature_tag"] = "lighthouse_beacon",
                ["size"] = {
                    0.42,
                    0.4,
                    0.4,
                },
            },
            {
                ["color"] = "white",
                ["far"] = true,
                ["group"] = "foam",
                ["name"] = "真珠泡大",
                ["position"] = {
                    -0.72,
                    0.68,
                    1,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Ball",
                ["signature_tag"] = "pearl_foam",
                ["size"] = {
                    0.46,
                    0.46,
                    0.46,
                },
            },
            {
                ["color"] = "coral",
                ["far"] = true,
                ["group"] = "foam",
                ["name"] = "真珠泡中",
                ["position"] = {
                    -0.12,
                    1.36,
                    0.83,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Ball",
                ["signature_tag"] = "pearl_foam",
                ["size"] = {
                    0.3,
                    0.3,
                    0.3,
                },
            },
            {
                ["color"] = "white",
                ["far"] = true,
                ["group"] = "foam",
                ["name"] = "真珠泡小",
                ["position"] = {
                    0.48,
                    0.94,
                    0.88,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Ball",
                ["signature_tag"] = "pearl_foam",
                ["size"] = {
                    0.22,
                    0.22,
                    0.22,
                },
            },
        },
        ["pose_offsets"] = {
            ["idle"] = {
            },
            ["loss"] = {
                ["foam"] = {
                    ["dy"] = -0.12,
                },
                ["wave"] = {
                    ["dy"] = -0.15,
                },
            },
            ["tap"] = {
                ["beacon"] = {
                    ["dy"] = 0.1,
                },
                ["wave"] = {
                    ["dy"] = 0.12,
                },
            },
            ["win"] = {
                ["beacon"] = {
                    ["dy"] = 0.16,
                },
                ["foam"] = {
                    ["dy"] = 0.25,
                },
            },
        },
        ["provenance"] = {
            ["atlas_sha256"] = "cf5ec26836842ce55a764c5ad66c711f00da0ed4cc30d80dad0df851e2656e01",
        },
        ["rarity"] = "レジェンド",
        ["signature_silhouette"] = "C字の波の門、小さな灯台、三つの真珠泡が漂う海の魔法",
        ["signature_tags"] = {
            "wave_gate",
            "lighthouse_beacon",
            "pearl_foam",
        },
        ["story"] = "沈んだ手紙を届けたお礼に海が道をひらいた。灯台の大潮は、その日の出来事を忘れないために、灯台の眠る窓に真珠の泡と波打つヒレを一つ残した。持ち主が負けた日も同じ表情で迎える。",
        ["world"] = "泡音の水都",
    },
    ["TRCA-TR-099"] = {
        ["archetype"] = "TR_CANDY_BOUNCE_ORB",
        ["category"] = "TR",
        ["category_ja"] = "罠",
        ["id"] = "TRCA-TR-099",
        ["name"] = "ぼよん跳ね玉",
        ["palette"] = {
            ["cream"] = {
                254,
                235,
                192,
            },
            ["dark"] = {
                105,
                65,
                145,
            },
            ["lilac"] = {
                183,
                154,
                237,
            },
            ["mint"] = {
                133,
                225,
                197,
            },
            ["pink"] = {
                253,
                136,
                184,
            },
        },
        ["parts"] = {
            {
                ["color"] = "pink",
                ["far"] = true,
                ["group"] = "orb",
                ["name"] = "大きな跳ね玉",
                ["position"] = {
                    0,
                    0.78,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Ball",
                ["signature_tag"] = "striped_candy_orb",
                ["size"] = {
                    1.8,
                    1.75,
                    1.8,
                },
            },
            {
                ["color"] = "mint",
                ["far"] = true,
                ["group"] = "orb",
                ["name"] = "右上の縞",
                ["position"] = {
                    0.28,
                    1.2,
                    0.74,
                },
                ["rotation"] = {
                    0,
                    0,
                    29,
                },
                ["shape"] = "Block",
                ["signature_tag"] = "striped_candy_orb",
                ["size"] = {
                    0.28,
                    0.94,
                    0.18,
                },
            },
            {
                ["color"] = "cream",
                ["far"] = true,
                ["group"] = "orb",
                ["name"] = "左下の縞",
                ["position"] = {
                    -0.4,
                    0.43,
                    0.72,
                },
                ["rotation"] = {
                    0,
                    0,
                    -24,
                },
                ["shape"] = "Block",
                ["signature_tag"] = "striped_candy_orb",
                ["size"] = {
                    0.26,
                    0.86,
                    0.16,
                },
            },
            {
                ["color"] = "lilac",
                ["far"] = true,
                ["group"] = "orb",
                ["name"] = "玉の星",
                ["position"] = {
                    0,
                    1.72,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Ball",
                ["signature_tag"] = "striped_candy_orb",
                ["size"] = {
                    0.42,
                    0.28,
                    0.45,
                },
            },
            {
                ["color"] = "dark",
                ["far"] = false,
                ["group"] = "base",
                ["name"] = "跳ね台の土台",
                ["position"] = {
                    0,
                    -0.54,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Block",
                ["signature_tag"] = "support",
                ["size"] = {
                    2.2,
                    0.27,
                    2.1,
                },
            },
            {
                ["color"] = "mint",
                ["far"] = true,
                ["group"] = "spring",
                ["name"] = "左ばね",
                ["position"] = {
                    -0.55,
                    -0.2,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Cylinder",
                ["signature_tag"] = "visible_double_spring",
                ["size"] = {
                    0.27,
                    0.6,
                    0.27,
                },
            },
            {
                ["color"] = "mint",
                ["far"] = true,
                ["group"] = "spring",
                ["name"] = "右ばね",
                ["position"] = {
                    0.55,
                    -0.2,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Cylinder",
                ["signature_tag"] = "visible_double_spring",
                ["size"] = {
                    0.27,
                    0.6,
                    0.27,
                },
            },
            {
                ["color"] = "cream",
                ["far"] = true,
                ["group"] = "spring",
                ["name"] = "ばねの縞左",
                ["position"] = {
                    -0.55,
                    0.05,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Cylinder",
                ["signature_tag"] = "visible_double_spring",
                ["size"] = {
                    0.43,
                    0.1,
                    0.43,
                },
            },
            {
                ["color"] = "cream",
                ["far"] = true,
                ["group"] = "spring",
                ["name"] = "ばねの縞右",
                ["position"] = {
                    0.55,
                    0.05,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Cylinder",
                ["signature_tag"] = "visible_double_spring",
                ["size"] = {
                    0.43,
                    0.1,
                    0.43,
                },
            },
            {
                ["color"] = "cream",
                ["far"] = true,
                ["group"] = "arrow",
                ["name"] = "大上矢印の棒",
                ["position"] = {
                    1.5,
                    0.64,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Block",
                ["signature_tag"] = "large_up_arrow",
                ["size"] = {
                    0.23,
                    1.3,
                    0.3,
                },
            },
            {
                ["color"] = "cream",
                ["far"] = true,
                ["group"] = "arrow",
                ["name"] = "矢印の左肩",
                ["position"] = {
                    1.32,
                    1.24,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    40,
                },
                ["shape"] = "Block",
                ["signature_tag"] = "large_up_arrow",
                ["size"] = {
                    0.23,
                    0.68,
                    0.3,
                },
            },
            {
                ["color"] = "cream",
                ["far"] = true,
                ["group"] = "arrow",
                ["name"] = "矢印の右肩",
                ["position"] = {
                    1.68,
                    1.24,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    -40,
                },
                ["shape"] = "Block",
                ["signature_tag"] = "large_up_arrow",
                ["size"] = {
                    0.23,
                    0.68,
                    0.3,
                },
            },
        },
        ["pose_offsets"] = {
            ["idle"] = {
            },
            ["loss"] = {
                ["arrow"] = {
                    ["dy"] = -0.1,
                },
                ["orb"] = {
                    ["dy"] = -0.2,
                },
            },
            ["tap"] = {
                ["orb"] = {
                    ["dy"] = -0.18,
                },
                ["spring"] = {
                    ["dy"] = -0.1,
                },
            },
            ["win"] = {
                ["arrow"] = {
                    ["dy"] = 0.2,
                },
                ["orb"] = {
                    ["dy"] = 0.26,
                },
            },
        },
        ["provenance"] = {
            ["atlas_sha256"] = "cf5ec26836842ce55a764c5ad66c711f00da0ed4cc30d80dad0df851e2656e01",
        },
        ["rarity"] = "レジェンド",
        ["signature_silhouette"] = "ピンクのしましま跳ね玉、見える二本ばね、大きな上矢印の罠",
        ["signature_tags"] = {
            "striped_candy_orb",
            "visible_double_spring",
            "large_up_arrow",
        },
        ["story"] = "泣いている子のために最後の観覧車を回した。ぼよん跳ね玉は、その日の出来事を忘れないために、閉園しない小さな舞台にお菓子色の柔らかい幾何学を一つ残した。持ち主が負けた日も同じ表情で迎える。",
        ["world"] = "夢菓子の遊園",
    },
    ["TRCA-VE-018"] = {
        ["archetype"] = "VE_FOREST_WALKING_GARDEN",
        ["category"] = "VE",
        ["category_ja"] = "乗り物",
        ["id"] = "TRCA-VE-018",
        ["name"] = "祖樹の散歩台",
        ["palette"] = {
            ["amber"] = {
                250,
                190,
                86,
            },
            ["bark"] = {
                116,
                78,
                65,
            },
            ["cream"] = {
                247,
                230,
                170,
            },
            ["leaf"] = {
                78,
                161,
                102,
            },
            ["moss"] = {
                128,
                183,
                81,
            },
        },
        ["parts"] = {
            {
                ["color"] = "bark",
                ["far"] = true,
                ["group"] = "base",
                ["name"] = "木の台車",
                ["position"] = {
                    0,
                    0,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Block",
                ["signature_tag"] = "support",
                ["size"] = {
                    2.8,
                    0.33,
                    1.7,
                },
            },
            {
                ["color"] = "moss",
                ["far"] = true,
                ["group"] = "wheel",
                ["name"] = "前車輪左",
                ["position"] = {
                    0.93,
                    -0.35,
                    -0.8,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Cylinder",
                ["signature_tag"] = "support",
                ["size"] = {
                    0.65,
                    0.65,
                    0.32,
                },
            },
            {
                ["color"] = "moss",
                ["far"] = true,
                ["group"] = "wheel",
                ["name"] = "前車輪右",
                ["position"] = {
                    0.93,
                    -0.35,
                    0.8,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Cylinder",
                ["signature_tag"] = "support",
                ["size"] = {
                    0.65,
                    0.65,
                    0.32,
                },
            },
            {
                ["color"] = "moss",
                ["far"] = true,
                ["group"] = "wheel",
                ["name"] = "後車輪左",
                ["position"] = {
                    -0.93,
                    -0.35,
                    -0.8,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Cylinder",
                ["signature_tag"] = "support",
                ["size"] = {
                    0.65,
                    0.65,
                    0.32,
                },
            },
            {
                ["color"] = "moss",
                ["far"] = false,
                ["group"] = "wheel",
                ["name"] = "後車輪右",
                ["position"] = {
                    -0.93,
                    -0.35,
                    0.8,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Cylinder",
                ["signature_tag"] = "support",
                ["size"] = {
                    0.65,
                    0.65,
                    0.32,
                },
            },
            {
                ["color"] = "bark",
                ["far"] = true,
                ["group"] = "roof",
                ["name"] = "木の柱",
                ["position"] = {
                    -0.56,
                    1.07,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Cylinder",
                ["signature_tag"] = "moss_canopy",
                ["size"] = {
                    0.36,
                    1.9,
                    0.42,
                },
            },
            {
                ["color"] = "leaf",
                ["far"] = true,
                ["group"] = "roof",
                ["name"] = "大きな苔屋根",
                ["position"] = {
                    -0.56,
                    2.13,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Ball",
                ["signature_tag"] = "moss_canopy",
                ["size"] = {
                    2.25,
                    0.55,
                    1.8,
                },
            },
            {
                ["color"] = "moss",
                ["far"] = true,
                ["group"] = "roof",
                ["name"] = "屋根の縁",
                ["position"] = {
                    -0.56,
                    1.94,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Ball",
                ["signature_tag"] = "moss_canopy",
                ["size"] = {
                    2.65,
                    0.26,
                    2,
                },
            },
            {
                ["color"] = "cream",
                ["far"] = true,
                ["group"] = "seat",
                ["name"] = "ベンチ座面",
                ["position"] = {
                    0.55,
                    0.5,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Block",
                ["signature_tag"] = "open_bench",
                ["size"] = {
                    1.15,
                    0.18,
                    0.8,
                },
            },
            {
                ["color"] = "bark",
                ["far"] = true,
                ["group"] = "seat",
                ["name"] = "ベンチ背もたれ",
                ["position"] = {
                    0.06,
                    0.88,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Block",
                ["signature_tag"] = "open_bench",
                ["size"] = {
                    0.18,
                    0.65,
                    0.8,
                },
            },
            {
                ["color"] = "bark",
                ["far"] = true,
                ["group"] = "lantern",
                ["name"] = "ランタンひも",
                ["position"] = {
                    -1.2,
                    1.54,
                    0.65,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Cylinder",
                ["signature_tag"] = "glow_lantern",
                ["size"] = {
                    0.13,
                    0.53,
                    0.13,
                },
            },
            {
                ["color"] = "amber",
                ["far"] = true,
                ["group"] = "lantern",
                ["name"] = "森の灯",
                ["position"] = {
                    -1.2,
                    1.2,
                    0.65,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Ball",
                ["signature_tag"] = "glow_lantern",
                ["size"] = {
                    0.36,
                    0.48,
                    0.36,
                },
            },
        },
        ["pose_offsets"] = {
            ["idle"] = {
            },
            ["loss"] = {
                ["lantern"] = {
                    ["dy"] = -0.14,
                },
                ["roof"] = {
                    ["dy"] = -0.1,
                },
            },
            ["tap"] = {
                ["lantern"] = {
                    ["dy"] = 0.06,
                },
                ["roof"] = {
                    ["dy"] = 0.12,
                },
            },
            ["win"] = {
                ["lantern"] = {
                    ["dy"] = 0.2,
                },
                ["roof"] = {
                    ["dy"] = 0.22,
                },
            },
        },
        ["provenance"] = {
            ["atlas_sha256"] = "cf5ec26836842ce55a764c5ad66c711f00da0ed4cc30d80dad0df851e2656e01",
        },
        ["rarity"] = "ミシック",
        ["signature_silhouette"] = "きのこの苔屋根、座れることが分かるベンチ、揺れるランタンの散歩台",
        ["signature_tags"] = {
            "moss_canopy",
            "open_bench",
            "glow_lantern",
        },
        ["story"] = "帰れなかった子のために森の出口をあけた。祖樹の散歩台は、その日の出来事を忘れないために、森番の大切な切り株に葉ときのこで包んだランタンを一つ残した。持ち主が負けた日も同じ表情で迎える。",
        ["world"] = "苔灯の深森",
    },
    ["TRCA-WE-072"] = {
        ["archetype"] = "WE_GHOST_MOON_HORN",
        ["category"] = "WE",
        ["category_ja"] = "武器",
        ["id"] = "TRCA-WE-072",
        ["name"] = "おばけホルン",
        ["palette"] = {
            ["blue"] = {
                102,
                179,
                214,
            },
            ["deep"] = {
                64,
                55,
                106,
            },
            ["purple"] = {
                163,
                142,
                211,
            },
            ["silver"] = {
                197,
                204,
                225,
            },
            ["white"] = {
                234,
                235,
                250,
            },
        },
        ["parts"] = {
            {
                ["color"] = "white",
                ["far"] = true,
                ["group"] = "hood",
                ["name"] = "おばけの胴",
                ["position"] = {
                    0,
                    0.35,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Ball",
                ["signature_tag"] = "ghost_sheet",
                ["size"] = {
                    1.15,
                    1.42,
                    1,
                },
            },
            {
                ["color"] = "white",
                ["far"] = true,
                ["group"] = "hood",
                ["name"] = "布の左裾",
                ["position"] = {
                    -0.48,
                    -0.32,
                    -0.33,
                },
                ["rotation"] = {
                    0,
                    0,
                    -15,
                },
                ["shape"] = "Block",
                ["signature_tag"] = "ghost_sheet",
                ["size"] = {
                    0.35,
                    0.77,
                    0.45,
                },
            },
            {
                ["color"] = "purple",
                ["far"] = true,
                ["group"] = "hood",
                ["name"] = "布の右裾",
                ["position"] = {
                    -0.48,
                    -0.32,
                    0.33,
                },
                ["rotation"] = {
                    0,
                    0,
                    17,
                },
                ["shape"] = "Block",
                ["signature_tag"] = "ghost_sheet",
                ["size"] = {
                    0.35,
                    0.59,
                    0.45,
                },
            },
            {
                ["color"] = "deep",
                ["far"] = true,
                ["group"] = "hood",
                ["name"] = "左目",
                ["position"] = {
                    0.53,
                    0.63,
                    -0.25,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Ball",
                ["signature_tag"] = "support",
                ["size"] = {
                    0.15,
                    0.2,
                    0.16,
                },
            },
            {
                ["color"] = "deep",
                ["far"] = false,
                ["group"] = "hood",
                ["name"] = "右目",
                ["position"] = {
                    0.53,
                    0.63,
                    0.25,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Ball",
                ["signature_tag"] = "support",
                ["size"] = {
                    0.15,
                    0.2,
                    0.16,
                },
            },
            {
                ["color"] = "silver",
                ["far"] = true,
                ["group"] = "horn",
                ["name"] = "ホルンの管",
                ["position"] = {
                    -0.72,
                    0.48,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    20,
                },
                ["shape"] = "Cylinder",
                ["signature_tag"] = "moon_horn",
                ["size"] = {
                    1.52,
                    0.22,
                    0.23,
                },
            },
            {
                ["color"] = "purple",
                ["far"] = true,
                ["group"] = "horn",
                ["name"] = "月角の上",
                ["position"] = {
                    -1.55,
                    1.02,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    35,
                },
                ["shape"] = "Block",
                ["signature_tag"] = "moon_horn",
                ["size"] = {
                    0.28,
                    0.95,
                    0.32,
                },
            },
            {
                ["color"] = "purple",
                ["far"] = true,
                ["group"] = "horn",
                ["name"] = "月角の下",
                ["position"] = {
                    -1.55,
                    0.06,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    -28,
                },
                ["shape"] = "Block",
                ["signature_tag"] = "moon_horn",
                ["size"] = {
                    0.28,
                    0.83,
                    0.32,
                },
            },
            {
                ["color"] = "blue",
                ["far"] = true,
                ["group"] = "horn",
                ["name"] = "ホルンの口",
                ["position"] = {
                    -1.78,
                    0.56,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Cylinder",
                ["signature_tag"] = "moon_horn",
                ["size"] = {
                    0.58,
                    0.7,
                    0.25,
                },
            },
            {
                ["color"] = "blue",
                ["far"] = true,
                ["group"] = "note",
                ["name"] = "音符の丸",
                ["position"] = {
                    -1.55,
                    1.7,
                    0.4,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Ball",
                ["signature_tag"] = "floating_note",
                ["size"] = {
                    0.31,
                    0.31,
                    0.31,
                },
            },
            {
                ["color"] = "deep",
                ["far"] = true,
                ["group"] = "note",
                ["name"] = "音符の棒",
                ["position"] = {
                    -1.37,
                    1.98,
                    0.4,
                },
                ["rotation"] = {
                    0,
                    0,
                    15,
                },
                ["shape"] = "Block",
                ["signature_tag"] = "floating_note",
                ["size"] = {
                    0.14,
                    0.6,
                    0.14,
                },
            },
            {
                ["color"] = "purple",
                ["far"] = true,
                ["group"] = "note",
                ["name"] = "音符の旗",
                ["position"] = {
                    -1.16,
                    2.17,
                    0.4,
                },
                ["rotation"] = {
                    0,
                    0,
                    24,
                },
                ["shape"] = "Block",
                ["signature_tag"] = "floating_note",
                ["size"] = {
                    0.42,
                    0.14,
                    0.12,
                },
            },
        },
        ["pose_offsets"] = {
            ["idle"] = {
            },
            ["loss"] = {
                ["hood"] = {
                    ["dy"] = -0.14,
                },
                ["note"] = {
                    ["dy"] = -0.1,
                },
            },
            ["tap"] = {
                ["hood"] = {
                    ["dy"] = 0.11,
                },
                ["note"] = {
                    ["dy"] = 0.17,
                },
            },
            ["win"] = {
                ["hood"] = {
                    ["dy"] = 0.23,
                },
                ["note"] = {
                    ["dy"] = 0.25,
                },
            },
        },
        ["provenance"] = {
            ["atlas_sha256"] = "cf5ec26836842ce55a764c5ad66c711f00da0ed4cc30d80dad0df851e2656e01",
        },
        ["rarity"] = "レジェンド",
        ["signature_silhouette"] = "白いおばけ布、片側に寄る三日月型ホルン、空中の音符の楽器",
        ["signature_tags"] = {
            "ghost_sheet",
            "moon_horn",
            "floating_note",
        },
        ["story"] = "一人ぼっちのおばけに仲間がいると教えた。おばけホルンは、その日の出来事を忘れないために、おやすみの円舞台に縫い目のある布と小さな三日月を一つ残した。持ち主が負けた日も同じ表情で迎える。",
        ["world"] = "月縫いの墓園",
    },
    ["TRCA-ZO-090"] = {
        ["archetype"] = "ZO_TIME_MAZE_GUIDE",
        ["category"] = "ZO",
        ["category_ja"] = "ゾンビ",
        ["id"] = "TRCA-ZO-090",
        ["name"] = "迷宮の道案内兵",
        ["palette"] = {
            ["blue"] = {
                80,
                98,
                152,
            },
            ["dark"] = {
                62,
                61,
                88,
            },
            ["linen"] = {
                234,
                225,
                201,
            },
            ["mint"] = {
                134,
                193,
                176,
            },
            ["sand"] = {
                235,
                196,
                112,
            },
        },
        ["parts"] = {
            {
                ["color"] = "linen",
                ["far"] = false,
                ["group"] = "body",
                ["name"] = "案内兵の胴",
                ["position"] = {
                    0,
                    0.15,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Ball",
                ["signature_tag"] = "support",
                ["size"] = {
                    1.05,
                    1.15,
                    0.8,
                },
            },
            {
                ["color"] = "sand",
                ["far"] = true,
                ["group"] = "head",
                ["name"] = "布の頭",
                ["position"] = {
                    0,
                    1.02,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Ball",
                ["signature_tag"] = "support",
                ["size"] = {
                    0.87,
                    0.84,
                    0.78,
                },
            },
            {
                ["color"] = "blue",
                ["far"] = true,
                ["group"] = "hat",
                ["name"] = "帽子上",
                ["position"] = {
                    0,
                    1.83,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Block",
                ["signature_tag"] = "hourglass_helmet",
                ["size"] = {
                    0.84,
                    0.19,
                    0.58,
                },
            },
            {
                ["color"] = "sand",
                ["far"] = true,
                ["group"] = "hat",
                ["name"] = "帽子くびれ",
                ["position"] = {
                    0,
                    1.57,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Cylinder",
                ["signature_tag"] = "hourglass_helmet",
                ["size"] = {
                    0.24,
                    0.34,
                    0.33,
                },
            },
            {
                ["color"] = "blue",
                ["far"] = true,
                ["group"] = "hat",
                ["name"] = "帽子下",
                ["position"] = {
                    0,
                    1.33,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Block",
                ["signature_tag"] = "hourglass_helmet",
                ["size"] = {
                    0.72,
                    0.19,
                    0.58,
                },
            },
            {
                ["color"] = "dark",
                ["far"] = true,
                ["group"] = "sign",
                ["name"] = "看板の柱",
                ["position"] = {
                    0.84,
                    0.4,
                    0.8,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Block",
                ["signature_tag"] = "direction_sign",
                ["size"] = {
                    0.16,
                    1.48,
                    0.17,
                },
            },
            {
                ["color"] = "mint",
                ["far"] = true,
                ["group"] = "sign",
                ["name"] = "右向き看板",
                ["position"] = {
                    0.92,
                    1.18,
                    0.8,
                },
                ["rotation"] = {
                    0,
                    0,
                    16,
                },
                ["shape"] = "Block",
                ["signature_tag"] = "direction_sign",
                ["size"] = {
                    1.2,
                    0.25,
                    0.24,
                },
            },
            {
                ["color"] = "sand",
                ["far"] = true,
                ["group"] = "sign",
                ["name"] = "左向き看板",
                ["position"] = {
                    0.68,
                    0.83,
                    0.8,
                },
                ["rotation"] = {
                    0,
                    0,
                    -18,
                },
                ["shape"] = "Block",
                ["signature_tag"] = "direction_sign",
                ["size"] = {
                    0.82,
                    0.2,
                    0.21,
                },
            },
            {
                ["color"] = "blue",
                ["far"] = true,
                ["group"] = "feet",
                ["name"] = "左の小靴",
                ["position"] = {
                    0.13,
                    -0.57,
                    -0.3,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Block",
                ["signature_tag"] = "uneven_boots",
                ["size"] = {
                    0.43,
                    0.49,
                    0.4,
                },
            },
            {
                ["color"] = "sand",
                ["far"] = true,
                ["group"] = "feet",
                ["name"] = "右の大靴",
                ["position"] = {
                    0.18,
                    -0.58,
                    0.3,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Block",
                ["signature_tag"] = "uneven_boots",
                ["size"] = {
                    0.7,
                    0.55,
                    0.59,
                },
            },
            {
                ["color"] = "mint",
                ["far"] = true,
                ["group"] = "body",
                ["name"] = "胸の時計",
                ["position"] = {
                    0.45,
                    0.16,
                    0,
                },
                ["rotation"] = {
                    0,
                    0,
                    0,
                },
                ["shape"] = "Ball",
                ["signature_tag"] = "support",
                ["size"] = {
                    0.23,
                    0.33,
                    0.23,
                },
            },
        },
        ["pose_offsets"] = {
            ["idle"] = {
            },
            ["loss"] = {
                ["head"] = {
                    ["dy"] = -0.13,
                },
                ["sign"] = {
                    ["rz"] = -14,
                },
            },
            ["tap"] = {
                ["head"] = {
                    ["dy"] = 0.13,
                },
                ["sign"] = {
                    ["rz"] = 14,
                },
            },
            ["win"] = {
                ["hat"] = {
                    ["dy"] = 0.16,
                },
                ["sign"] = {
                    ["dy"] = 0.2,
                },
            },
        },
        ["provenance"] = {
            ["atlas_sha256"] = "cf5ec26836842ce55a764c5ad66c711f00da0ed4cc30d80dad0df851e2656e01",
        },
        ["rarity"] = "レジェンド",
        ["signature_silhouette"] = "砂時計の帽子、左右逆向き看板、左右違う大きさの靴を持つ迷宮の案内兵",
        ["signature_tags"] = {
            "hourglass_helmet",
            "direction_sign",
            "uneven_boots",
        },
        ["story"] = "道に迷った旅人のために自分の時間を分けた。迷宮の道案内兵は、その日の出来事を忘れないために、二度と閉じない時の扉に砂粒の粒子と回転する目盛を一つ残した。持ち主が負けた日も同じ表情で迎える。",
        ["world"] = "砂時計の迷宮",
    },
}
function C.get(id)
    if type(id) ~= "string" then return nil end
    return DEFINITIONS[id]
end
function C.ids()
    return {
    "TRCA-BE-045",
    "TRCA-SP-054",
    "TRCA-TR-099",
    "TRCA-VE-018",
    "TRCA-WE-072",
    "TRCA-ZO-090",
}
end
return C
