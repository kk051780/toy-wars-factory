import unittest
import verify_compact as qa

class CompactRealmHUDTests(unittest.TestCase):
    def test_original_source_is_immutable_and_single_delta(self):
        old,new=qa.exact_source()
        self.assertGreater(len(new),len(old))
        self.assertEqual(new.replace(qa.INSERT.encode(),qa.ANCHOR.encode()),old)

    def test_small_panel_for_nonfighter_and_restore_fighter(self):
        code=qa.CANDIDATE.read_text()
        self.assertIn("panelHeight=isFlight and 260 or 90",code)
        self.assertIn("gun.Position=UDim2.fromOffset(5,isFlight and 122 or 34)",code)
        for weapon in ("cannon","breath","hydro"):
            self.assertIn(f"{weapon}.Position=UDim2.fromOffset(5,34)",code)
        self.assertIn("if currentKind~=previous then",code)

    def test_controls_follow_authoritative_kind_flags(self):
        text=qa.CANDIDATE.read_text()
        for expected in ("frame.Visible=active","gun.Visible=isFlight or isAir",
                         "bomb.Visible=isFlight","cannon.Visible=isShip",
                         "breath.Visible=isBeast","hydro.Visible=isDiver",
                         'heading.Text=currentKind=="FIGHTER"', "pilotKind()"):
            self.assertIn(expected,text)

    def test_new_client_does_not_add_attack_or_server_authority(self):
        old,new=qa.exact_source()
        for token in (b'remote:FireServer(',b'UIS.InputBegan:',b'UIS.InputEnded:',
                      b'RenderStepped:Connect(',b'EGGRUMBLE_RealmBattleIntent_V1'):
            self.assertEqual(old.count(token),new.count(token))

    def test_negative_source_mutant_rejected(self):
        original=qa.ORIGINAL.read_text()
        candidate=qa.CANDIDATE.read_text()
        mutant=candidate.replace("panelHeight=isFlight and 260 or 90",
                                 "panelHeight=isFlight and 260 or 290",1)
        self.assertNotEqual(mutant,original.replace(qa.ANCHOR,qa.INSERT,1))
        self.assertEqual(original.count(qa.ANCHOR),1)

if __name__=="__main__":
    unittest.main()
