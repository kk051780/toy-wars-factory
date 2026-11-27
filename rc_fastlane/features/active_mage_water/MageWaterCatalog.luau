--!strict
-- Exact MAGE-041 row from the approved ability data. Mount only the selected row.
local data={
["MAGE-041"]={["id"]="MAGE-041",["name"]="水弾",["rarity"]="C",["description"]="単体水弾",["roles"]={"MAGE"},["catalogSource"]="7203799683",["cd"]=12,["energy"]=30,["metrics"]={{["label"]="射程stud",["values"]={10,12,14,16,18},["note"]=""},{["label"]="中立水印秒",["values"]={1,1.2,1.4,1.6,2},["note"]=""}},["forms"]={"杖先に雫形結晶","水晶の二層殻から水弾","結晶の花弁と着弾水紋","杖の尾部から水の帯","潮紋に変形した結晶と地表の水波"},["designSource"]="7204247109",["specification"]="- MAGE-041 **水弾** [C]｜射程stud: 10/12/14/16/18｜中立水印秒: 1/1.2/1.4/1.6/2｜CD12s/E30\n- 造形/リグ：樫製杖、彫金、青い曇り水晶核、弾殻の輪郭\n- モーション：手を開き杖を回す→照準→水弾→実着弾に水印→杖を戻す\n- 音響：水滴、木杖、結晶の共鳴\n- S0 杖先に雫形結晶 → S1 水晶の二層殻から水弾 → S2 結晶の花弁と着弾水紋 → S3 杖の尾部から水の帯 → S4 潮紋に変形した結晶と地表の水波\n- 対抗/回帰：水印の期限と実対象を明示、壁越し不可"},
}
return table.freeze(data["MAGE-041"])
