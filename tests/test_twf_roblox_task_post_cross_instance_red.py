"""RED negative control: two independently built one-shot objects can POST twice."""
import hashlib
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import twf_roblox_task_post_once as m
from test_twf_roblox_task_post_once import FakeOpener, SCRIPT, KEY, T

class CrossInstanceRed(unittest.TestCase):
    def test_same_intent_must_only_submit_one_http_post(self):
        with patch.object(m,'SMOKE_SHA256',hashlib.sha256(SCRIPT).hexdigest()):
            opener=FakeOpener()
            request=m.prepare(T,SCRIPT)
            fence=m.LocalIntentFence()
            first=m.OneShotPoster(request,T,SCRIPT,api_key=KEY,opener=opener,intent_fence=fence)
            second=m.OneShotPoster(request,T,SCRIPT,api_key=KEY,opener=opener,intent_fence=fence)
            first.submit_once()
            try:
                second.submit_once()
            except m.TaskHold:
                pass
            self.assertEqual(len(opener.requests),1,'duplicate POST by second object is unsafe')

if __name__=='__main__':unittest.main()
