-- Fixed #219 COMBO-001..021; design inputs from comments 7210878151 and 7211006478.
-- Isolated source candidate. No Remote, damage, energy, CD, unlock or match authority.
-- All numeric stage values are design limits, not grants. Absent values must be
-- resolved against the original authoritative abilities, never treated as unlimited.
local rows = {
    {id = "COMBO-001", role = "WARRIOR", parts = {"WARRIOR-060", "WARRIOR-020"}, name = "天翼剣雨", flow = "LAND_THEN_ATTACK", telegraphMinSec = 1, receipts = {"FLIGHT_VALID", "LAND_VALID", "ATTACK_VALID"}, note = "COMBO-001 対人は元技上限かつ一回、飛翔中攻撃なし", stage = {neutralMax = {2, 3, 4, 6, 8}}},
    {id = "COMBO-002", role = "WARRIOR", parts = {"WARRIOR-071", "WARRIOR-016"}, name = "炎輪剣舞", flow = "ATTACK_UNIFIED", telegraphMinSec = 0.8, receipts = {"ATTACK_VALID", "STATUS_VALID"}, note = "燃焼登録一度", stage = {radius = {3, 4, 5, 6, 7}, neutralMax = {1, 2, 3, 4, 5}, burnSec = {1, 1.2, 1.4, 1.6, 2}}},
    {id = "COMBO-003", role = "WARRIOR", parts = {"WARRIOR-018", "COMMON-025"}, name = "光盾踏陣", flow = "PLACE_THEN_GUARD", receipts = {"PLACEMENT_VALID", "OWNER_ON_PLATFORM", "GUARD_VALID"}, note = "防御窓は足場の残寿命以下", stage = {width = {2, 2.5, 3, 3.5, 4}, life = {1, 1.5, 2, 2.5, 3}, mitigatePct = {8, 10, 12, 14, 16}, guardMaxSec = {1, 1.3, 1.6, 1.9, 2.2}}},
    {id = "COMBO-004", role = "MAGE", parts = {"MAGE-025", "MAGE-041"}, name = "雷潮連環", flow = "ATTRIBUTE_CHAIN", receipts = {"WATER_MARK_VALID", "REACTION_VALID"}, note = "発動順は水弾→連鎖雷。構成順とは独立", stage = {neutralMax = {1, 2, 3, 4, 5}}},
    {id = "COMBO-005", role = "MAGE", parts = {"MAGE-012", "MAGE-040"}, name = "白銀嵐翼", flow = "LAND_THEN_ATTACK", receipts = {"FLIGHT_VALID", "LAND_VALID", "ATTACK_VALID"}, note = "風翼→氷槍", stage = {flightSec = {0.8, 1.3, 1.8, 2.6, 3.6}, height = {4, 6, 9, 13, 18}, range = {9, 11, 13, 15, 17}, neutralMax = {1, 1, 2, 2, 3}}},
    {id = "COMBO-006", role = "MAGE", parts = {"MAGE-005", "MAGE-035"}, name = "炎風回廊", flow = "GUARD_THEN_ATTACK", receipts = {"GUARD_ACTIVE", "ATTACK_VALID"}, note = "正面風壁→追火球", stage = {mitigatePct = {6, 8, 10, 12, 14}, guardSec = {1, 1.3, 1.6, 1.9, 2.2}, range = {9, 11, 13, 15, 17}, trackingDeg = {5, 8, 11, 14, 17}}},
    {id = "COMBO-007", role = "NINJA", parts = {"NINJA-020", "NINJA-028"}, name = "月蝕影舞", flow = "REVEAL_THEN_ATTACK", telegraphMinSec = 0.45, receipts = {"STEALTH_ENDED", "ATTACK_VALID"}, note = "再出現予兆0.45秒以上、攻撃は透明中不可", stage = {neutralMax = {1, 2, 3, 4, 5}}},
    {id = "COMBO-008", role = "NINJA", parts = {"NINJA-031", "NINJA-061"}, name = "霞瞬歩", flow = "MOVE_THEN_PLACE", telegraphMinSec = 0.18, receipts = {"MOVE_VALID", "PLACEMENT_VALID"}, note = "煙で危険予兆を隠さない", stage = {distance = {5, 7, 9, 11, 13}, radius = {3, 4, 5, 6, 7}, life = {1, 1.5, 2, 2.5, 3}}},
    {id = "COMBO-009", role = "NINJA", parts = {"NINJA-060", "NINJA-025"}, name = "宵翼囮行", flow = "FLIGHT_VISUAL_DECOY", receipts = {"FLIGHT_VALID", "DECOY_VALID"}, note = "非実体囮一体", stage = {flightSec = {0.8, 1.2, 1.8, 2.5, 3.4}, height = {4, 6, 9, 13, 17}, decoyDist = {4, 6, 8, 10, 12}, decoyLife = {1, 1.2, 1.4, 1.6, 1.8}}},
    {id = "COMBO-010", role = "TRAPPER", parts = {"TRAPPER-015", "TRAPPER-036"}, name = "刻重星", flow = "CONTROL_THEN_RETURN", receipts = {"CONTROL_VALID", "RETURN_VALID"}, note = "安全な自己位置、他の値を巻き戻さない", stage = {neutralMax = {2, 3, 4, 5, 6}}},
    {id = "COMBO-011", role = "TRAPPER", parts = {"TRAPPER-025", "TRAPPER-054"}, name = "念動交換浮遊", flow = "SWAP_THEN_HOVER", telegraphMinSec = 0.6, receipts = {"SWAP_VALID", "HOVER_VALID", "LAND_VALID"}, note = "両端安全/対象適格", stage = {distance = {4, 5, 6, 7, 8}, hoverSec = {0.5, 0.7, 0.9, 1.1, 1.3}, height = {1, 2, 3, 4, 5}}},
    {id = "COMBO-012", role = "TRAPPER", parts = {"TRAPPER-060", "TRAPPER-040"}, name = "無重力刻環", flow = "CONTROL_THEN_FLIGHT", telegraphMinSec = 1, receipts = {"CONTROL_VALID", "FLIGHT_VALID", "LAND_VALID"}, note = "中立軌道のみ、成長時間は変更なし", stage = {radius = {3, 4, 5, 6, 7}, controlSec = {0.4, 0.5, 0.6, 0.7, 0.8}, neutralMax = {3, 3, 3, 3, 3}, flightSec = {0.8, 1.3, 1.8, 2.6, 3.6}, height = {4, 6, 9, 13, 18}}},
    {id = "COMBO-013", role = "BUILDER", parts = {"BUILDER-040", "BUILDER-018"}, name = "星環空砲", flow = "LAND_THEN_ATTACK", receipts = {"FLIGHT_VALID", "LAND_VALID", "ATTACK_VALID"}, note = "飛行→着地→連装砲", stage = {neutralMax = {2, 2, 3, 4, 5}}},
    {id = "COMBO-014", role = "BUILDER", parts = {"BUILDER-060", "BUILDER-048"}, name = "超機磁甲", flow = "FORM_THEN_PLACE", telegraphMinSec = 0.8, receipts = {"FORM_VALID", "PLACEMENT_VALID"}, note = "変形は一形態のみ", stage = {formChoices = {1, 2, 2, 3, 3}, formSec = {2, 2.5, 3, 3.5, 4}, width = {3, 4, 5, 6, 7}, life = {2, 2.5, 3, 3.5, 4}}},
    {id = "COMBO-015", role = "BUILDER", parts = {"BUILDER-025", "BUILDER-075"}, name = "護衛跳台", flow = "GUARDIAN_THEN_PLATFORM", receipts = {"OWNED_GUARDIAN_VALID", "PLACEMENT_VALID", "JUMP_VALID"}, note = "正規装置枠、一人一跳躍", stage = {guardSec = {3, 4, 5, 6, 7}, mitigatePct = {5, 7, 9, 11, 13}, jumpHeight = {2, 3, 4, 5, 6}, life = {3, 4, 5, 6, 7}}},
    {id = "COMBO-016", role = "BEAST", parts = {"BEAST-008", "BEAST-005"}, name = "雷翼竜", flow = "LAND_THEN_ATTACK", receipts = {"OWNED_MOUNT_VALID", "FLIGHT_VALID", "LAND_VALID", "ATTACK_VALID"}, note = "既存獣一体", stage = {neutralMax = {1, 2, 3, 4, 5}}},
    {id = "COMBO-017", role = "BEAST", parts = {"BEAST-020", "BEAST-095"}, name = "月狼円陣", flow = "CHARGE_THEN_GUARD", receipts = {"OWNED_BEAST_VALID", "CHARGE_VALID", "STOP_VALID", "FORMATION_VALID"}, note = "同じ既存獣", stage = {distance = {6, 8, 10, 12, 14}, neutralMax = {1, 2, 3, 4, 6}, guardRadius = {4, 5, 6, 7, 8}, guardSec = {2, 3, 4, 5, 6}}},
    {id = "COMBO-018", role = "BEAST", parts = {"BEAST-029", "BEAST-065"}, name = "天翼癒光", flow = "LAND_THEN_HEAL", receipts = {"OWNED_MOUNT_VALID", "FLIGHT_VALID", "LAND_VALID", "HEAL_CHANNEL_VALID"}, note = "既存合法形態切替が必要、チャネル1秒", stage = {flightSec = {0.8, 1.3, 1.8, 2.5, 3.5}, height = {4, 6, 9, 13, 18}, healPct = {2, 3, 4, 5, 6}, range = {5, 7, 9, 11, 13}}},
    {id = "COMBO-019", role = "ZOMBIE", parts = {"ZOMBIE-035", "ZOMBIE-040"}, name = "冥軍転向令", flow = "CONVERT_THEN_COMMAND", receipts = {"CONVERSION_ELIGIBLE", "OWNED_CONVERTED_VALID", "COMMAND_VALID"}, note = "転向条件・既存枠を保持", stage = {neutralMax = {1, 1, 2, 2, 3}}},
    {id = "COMBO-020", role = "ZOMBIE", parts = {"ZOMBIE-087", "ZOMBIE-020"}, name = "冥門百影", flow = "MOVE_THEN_COMMAND", telegraphMinSec = 0.5, receipts = {"MOVE_VALID", "OWNED_SPIRIT_VALID", "COMMAND_VALID"}, note = "隊列予告1秒以上、視覚影は非実体", stage = {distance = {4, 6, 8, 10, 12}, range = {6, 8, 10, 12, 14}, neutralMax = {1, 2, 3, 4, 5}}},
    {id = "COMBO-021", role = "ZOMBIE", parts = {"ZOMBIE-005", "ZOMBIE-060"}, name = "魂鎖天環", flow = "CONTROL_THEN_WAVE", telegraphMinSec = 1, receipts = {"CONTROL_VALID", "RELEASE_VALID", "ATTACK_VALID"}, note = "鎖印→解放→霊波。引寄せは既存正規権威確認・承認まで保留", stage = {range = {5, 6, 7, 8, 9}, controlSec = {0.6, 0.8, 1, 1.2, 1.4}, radius = {5, 7, 9, 11, 13}, neutralMax = {2, 3, 4, 5, 6}}},
}
local M = {}
local byPair = {}
local function key(role, a, b)
    if type(role) ~= "string" or type(a) ~= "string" or type(b) ~= "string" or a == b then return nil end
    if a:find("|", 1, true) or b:find("|", 1, true) or role:find("|", 1, true) then return nil end
    if a > b then a, b = b, a end
    return role .. "|" .. a .. "|" .. b
end
for _, r in ipairs(rows) do
    local k = assert(key(r.role, r.parts[1], r.parts[2]))
    assert(not byPair[k], "duplicate pair")
    byPair[k] = r
end
local function copyList(list)
    local out = {}
    for i, v in ipairs(list) do out[i] = v end
    return out
end
function M.resolve(role, first, second, stage)
    if type(stage) ~= "number" or stage < 0 or stage > 4 or stage % 1 ~= 0 then return nil, "STAGE" end
    local r = byPair[key(role, first, second) or ""]
    if not r then return nil, "PAIR" end
    local stageLimits = {}
    for metric, levels in pairs(r.stage) do stageLimits[metric] = levels[stage + 1] end
    local hold = nil
    if r.id == "COMBO-018" then hold = "OWNED_BEAST_FORM_COMPATIBILITY" end
    if r.id == "COMBO-021" then hold = "CONTROL_RELEASE_AUTHORITY" end
    return {
        id = r.id, role = r.role, name = r.name, flow = r.flow,
        parts = copyList(r.parts), receipts = copyList(r.receipts), stage = stage,
        limits = stageLimits, telegraphMinSec = r.telegraphMinSec, note = r.note,
        proposedEnergy = 80, proposedCooldownSec = 40, hold = hold,
    }
end
function M.list()
    local result = {}
    for i, r in ipairs(rows) do
        result[i] = {id = r.id, role = r.role, parts = copyList(r.parts)}
    end
    return result
end
return M
