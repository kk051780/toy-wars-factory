import unittest
from quality_gameplay.gq8_fourlane39_20261118.compose_fourlane39 import combine_host,MREQ,MCALL,RREQ,RCALL,MAGE,VFX
BASE='local A=1\n SevenRoleCombat.equip(session,p,role)\n SevenRoleCombat.equip(session,p,role)\n'
def add(src,req,call):
 return req+"\n"+src.replace("SevenRoleCombat.equip(session,p,role)","SevenRoleCombat.equip(session,p,role)\n "+call)
class FourLaneQA(unittest.TestCase):
 def setUp(self):
  self.m=add(BASE,MREQ,MCALL);self.r=add(BASE,RREQ,RCALL)
 def test_combined(self):
  out=combine_host(BASE,self.r,self.m)
  self.assertEqual(out.count(MCALL),2)
  self.assertEqual(out.count(RCALL),2)
 def test_extra_mage_red(self):
  with self.assertRaisesRegex(ValueError,"RED_MAGE_AUTHOR_EXTRA"):
   combine_host(BASE,self.r,self.m+"print('hack')\n")
 def test_duplicate_hook_red(self):
  with self.assertRaisesRegex(ValueError,"RED_AUTHOR_HOOK_COUNT"):
   combine_host(BASE,self.r,self.m.replace(MCALL,MCALL+"\n "+MCALL))
 def test_wrong_regen_red(self):
  with self.assertRaisesRegex(ValueError,"RED_AUTHOR_HOOK_COUNT"):
   combine_host(BASE,self.r.replace(RCALL,"BAD_HP_WRITE"),self.m)
 def test_unique_source_routes(self):
  self.assertFalse(MAGE & VFX)
if __name__=="__main__":unittest.main()
