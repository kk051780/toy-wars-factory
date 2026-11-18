#!/usr/bin/env python3
"""Fail-closed source-delta tests; actual source selection and VM run in Actions."""
import unittest

from patch_weather41 import (
    HELPER_ANCHOR,REALM_OLD,REALM_NEW,REALM_HELPER,
    STAGE_OLD,STAGE_INSERT,STORM_FENCE,patch,
)

class StageRealmWeatherContract(unittest.TestCase):
    def setUp(self):
        self.renderer=(
            '--!nonstrict\nlocal root={}\n'+STAGE_OLD+
            ' root.Parent=world\n')
        self.realm=(HELPER_ANCHOR+' return nil\nend\n'+REALM_OLD+
            '  if state.weather~=weather then\n'+STORM_FENCE+
            '  end\n'
            '  if weather=="THUNDER" and state.pendingLightning and now>=state.pendingLightning then\n'
            '  end\n')

    def test_patch_is_exactly_two_reversible_source_changes(self):
        render,realm=patch(self.renderer,self.realm)
        self.assertIn(STAGE_INSERT,render)
        self.assertIn(REALM_HELPER,realm)
        self.assertIn(REALM_NEW,realm)
        self.assertEqual(render.replace(STAGE_INSERT,"",1),self.renderer)
        self.assertEqual(realm.replace(REALM_HELPER,"",1).replace(REALM_NEW,REALM_OLD,1),self.realm)
        self.assertIn(STORM_FENCE,realm)

    def test_client_seed_not_used_and_realm_single_damage(self):
        self.assertIn('root:SetAttribute("GQ802_WeatherStart",os.clock())',STAGE_INSERT)
        self.assertIn('local stage=world:FindFirstChild("GQ802_VISUAL_TILE_STAGE_V1")',REALM_HELPER)
        self.assertIn('and approved[second] and approved[third]',REALM_HELPER)
        self.assertIn('or theme=="METEOR" then "THUNDER"',REALM_HELPER)
        self.assertIn('elseif theme=="SNOW" then "WIND"',REALM_HELPER)
        self.assertIn('elseif theme=="RAIN" then "RAIN"',REALM_HELPER)
        self.assertIn('return fallback,"LEGACY"',REALM_HELPER)
        self.assertNotIn('RemoteEvent',REALM_HELPER)
        self.assertNotIn('TakeDamage',REALM_HELPER)
        self.assertNotIn('workspace.Gravity=',REALM_HELPER)

    def test_malicious_stage_missing_weather_publish_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"RED_811_STAGE_INSERTION_ANCHOR"):
            patch(self.renderer.replace(STAGE_OLD,'  -- missing seed marker\n'),self.realm)
        with self.assertRaisesRegex(ValueError,"RED_811_STAGE_INSERTION_ANCHOR"):
            patch(self.renderer+STAGE_OLD,self.realm)

    def test_malicious_realm_storm_fence_change_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"RED_797_STORM_FENCE_MISSING"):
            patch(self.renderer,self.realm.replace(STORM_FENCE,''))
        with self.assertRaisesRegex(ValueError,"RED_REALM_WEATHER_LOOP_DRIFT"):
            patch(self.renderer,self.realm.replace(REALM_OLD,' local weather="CLEAR"\n'))

    def test_valid_author_churn_no_hidden_second_writer(self):
        self.assertIn('root:Destroy()\n     return nil,"RED_UNVERIFIED_WEATHER_PHASES"',STAGE_INSERT)
        self.assertIn('root:SetAttribute("GQ802_WeatherPolicy","DW_STAGE_V1")',STAGE_INSERT)
        self.assertIn('core:SetAttribute("RealmWeatherTheme",weatherTheme)',REALM_NEW)
        self.assertIn('if state.weatherTheme~=weatherTheme then',REALM_NEW)
        self.assertIn('now-started<3600',REALM_HELPER)

if __name__=="__main__":
    unittest.main()
