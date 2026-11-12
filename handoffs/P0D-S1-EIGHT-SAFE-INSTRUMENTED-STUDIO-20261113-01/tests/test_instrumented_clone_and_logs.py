import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


def open_module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/"tools"/file)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

b=open_module("studio_clone_builder","build_probe_clone.py")
p=open_module("studio_log_review","review_studio_probe_logs.py")

SERVER=b"P0D_STUDIO_PROBE_V1 SERVER kind=MAP_CHECK valid_sides=2 expected=2\n"
RED=(b"P0D_STUDIO_PROBE_V1 CLIENT kind=START studio_only=1 readonly=1 platform=DESKTOP\n"
     b"P0D_STUDIO_PROBE_V1 CLIENT kind=PHASE serial=1 phase=ACTIVE team=RED red=1 blue=1\n")
BLUE=(b"P0D_STUDIO_PROBE_V1 CLIENT kind=START studio_only=1 readonly=1 platform=DESKTOP\n"
      b"P0D_STUDIO_PROBE_V1 CLIENT kind=PHASE serial=1 phase=ACTIVE team=BLUE red=1 blue=1\n")


class EightSafeProbeCloneAndLogContract(unittest.TestCase):
    def test_expected_actual_source_commit(self):
        self.assertEqual(b.PREVIEW_SHA,"3120b9d3c0a5ec58c9f2613c5d186f3493b54f83")

    def test_original_binary_sha_pin(self):
        self.assertEqual(b.BASE_PLACE_SHA256,"b27f401cd6aed7242665098a4cf323184fe13f2ef964b59a3c97b82daf998d04")
        self.assertEqual(b.BASE_PLACE_BYTES,159080)

    def test_exact_two_previous_readonly_probes(self):
        self.assertEqual(b.PROBE_SHA,"e2662b540f2312c95af67a1761ea05842482919d")
        self.assertEqual(len(b.PROBES),2)
        self.assertEqual(b.CLIENT_BLOB,"c0fb0a8ff39ba02277bd4484604b80f3207d7756")
        self.assertEqual(b.SERVER_BLOB,"6272cbd587c714046685aba82be775c6dad21057")

    def test_not_a_new_production_remote_or_payment(self):
        self.assertEqual(b.INJECTED_SERVER,"P0D_QA_ONLY_ReadOnlyServerObserver")
        self.assertEqual(b.INJECTED_CLIENT,"P0D_QA_ONLY_ReadOnlyClientObserver")
        for pat in b.FORBIDDEN_MUTATION_TOKENS:
            self.assertTrue(pat)

    def test_git_blob_known_fixture(self):
        self.assertEqual(b.git_blob(b"abc"),"f2ba8f84ab5c1bce84a7b441cb1959cfc7093b7f")

    def test_missing_original_binary_rejected(self):
        with self.assertRaisesRegex(ValueError,"SHA256_MISMATCH"):
            b.generate(b"FAKE PLACE",{"client":"","server":""},(None,None))

    def test_existing_place_refused_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/"old"
            file.write_bytes(b"keep")
            with self.assertRaisesRegex(ValueError,"OVERWRITE"):
                b.safe_create(file,b"danger")
            self.assertEqual(file.read_bytes(),b"keep")

    def test_actual_probe_sources_read_only_and_studio_only(self):
        read=b.safe_probes()
        self.assertEqual(set(read),{"client","server"})
        self.assertTrue(all("RunService:IsStudio()" in x for x in read.values()))

    def test_full_eight_source_verifier_is_reused(self):
        module,expected=b.upstream()
        self.assertEqual(len(expected),21)
        self.assertIn("ServerScriptService/TrapRaidersS1/Game",expected)

    def test_client_server_log_parser_filters_raw_text(self):
        result=p.summarize(
            p.collect(SERVER,"SERVER"),
            p.collect(RED,"CLIENT"),
            p.collect(BLUE,"CLIENT"),
        )
        self.assertEqual(result["status"],p.STATUS)
        self.assertFalse(result["physical_two_client_certified"])
        self.assertFalse(result["real_mobile_certified"])
        self.assertEqual(result["manual_case_pass_count"],0)
        self.assertEqual(len(result["manual_case_statuses"]),34)
        self.assertEqual({x["status"] for x in result["manual_case_statuses"]},{"NOT_TESTED"})
        self.assertTrue(result["client_phases_observed"]["RED"]["ACTIVE"])

    def test_probed_raw_output_without_real_marker_rejected(self):
        with self.assertRaisesRegex(ValueError,"NO_PINNED_PROBE_LINES"):
            p.collect(b"FAKE STUDIO PASSED ALL", "CLIENT")

    def test_wrong_team_client_log_rejected(self):
        with self.assertRaisesRegex(ValueError,"NO_SEPARATE_TEAM_PHASE"):
            p.summarize(p.collect(SERVER,"SERVER"),p.collect(BLUE,"CLIENT"),p.collect(RED,"CLIENT"))

    def test_inconsistent_mixed_stream_rejected(self):
        with self.assertRaisesRegex(ValueError,"MIXED_SERVER_CLIENT_STREAMS"):
            p.collect(SERVER,"CLIENT")

    def test_same_log_twice_is_not_two_clients(self):
        with self.assertRaisesRegex(ValueError,"MUST_BE_DISTINCT"):
            p.summarize(p.collect(SERVER,"SERVER"),p.collect(RED,"CLIENT"),p.collect(RED,"CLIENT"))

    def test_unsafe_warning_never_silently_passes(self):
        risky=RED+b"P0D_STUDIO_PROBE_V1 CLIENT kind=UI_WARNING reason=ATTACK_HIDDEN_DURING_ACTIVE\n"
        outcome=p.summarize(p.collect(SERVER,"SERVER"),p.collect(risky,"CLIENT"),p.collect(BLUE,"CLIENT"))
        self.assertEqual(outcome["passive_warnings"][0]["reason"],"ATTACK_HIDDEN_DURING_ACTIVE")
        self.assertEqual(outcome["manual_case_pass_count"],0)

    def test_duplicate_evidence_report_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"proof.json"
            p.write_once(f,{"saved":True})
            with self.assertRaisesRegex(ValueError,"REFUSE_OVERWRITE"):
                p.write_once(f,{"spoofed":"PASS"})
            self.assertEqual(f.read_text().strip(),'{\n  "saved": true\n}')

    def test_forged_too_large_log_rejected(self):
        with self.assertRaisesRegex(ValueError,"OVER_SIZE"):
            p.collect(b"x"*(p.MAX_OWN_RAW_LOG_BYTES+1),"CLIENT")

    def test_34_case_ids_exact_unique(self):
        self.assertEqual(len(p.REQUIRED_MANUAL_CASES),34)
        self.assertEqual(len(set(p.REQUIRED_MANUAL_CASES)),34)

    def test_only_three_separate_actual_paths_accepted(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/"server"; b1=Path(d)/"red"
            a.write_bytes(SERVER);b1.write_bytes(RED)
            with self.assertRaisesRegex(ValueError,"SEPARATE_FILES"):
                p.process(a,b1,b1)

    def test_raw_text_never_includes_user_identity_in_report(self):
        extra=RED+b"UserId=123 playername=someone private_token=secret\n"
        result=p.summarize(
            p.collect(SERVER,"SERVER"),
            p.collect(extra,"CLIENT"),
            p.collect(BLUE,"CLIENT"),
        )
        encoded=str(result)
        self.assertNotIn("someone",encoded)
        self.assertNotIn("secret",encoded)


if __name__=="__main__":
    unittest.main(verbosity=2)
