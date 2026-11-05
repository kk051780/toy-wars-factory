"""Versioned read-only triage; legacy CLI remains a known Issue72 limitation.

Use repair_control.py triage as the supported entry point. The accepted v1
validator still checks provider binding, freshness, lease and exact-head QA.
Collectors must obtain evidence independently; JSON source labels are not proof.
No scheduler, Git mutation, credential access, recovery or write authority.
"""
import argparse
import json
import sys
import system_host_write_triage as legacy


def classify(evidence, config, now):
    """Preserve v1 diagnoses; terminal failure cannot become healthy idle."""
    verdict = legacy.classify(evidence, config, now)
    # Run the complete accepted validator first. Do not mask an active owner,
    # orphan, host rejection or ref race with an unrelated service-health label.
    if (verdict["state"] == "SAFE_TO_NEXT_SCHEDULE" and
            evidence["service"]["data"]["last_run"]["recorded_status"] != "completed"):
        return legacy.result("INDETERMINATE", "SERVICE_NOT_SUCCESSFULLY_COMPLETED")
    return verdict


def main(argv=None):
    class SafeParser(argparse.ArgumentParser):
        def error(self, message):
            raise legacy.InvalidEvidence()

    try:
        parser = SafeParser(description=__doc__)
        parser.add_argument("--evidence", required=True, help="JSON file or - for stdin")
        parser.add_argument("--config", required=True, help="separately trusted collector config")
        parser.add_argument("--now", required=True, help="explicit timezone-aware clock")
        args = parser.parse_args(argv)
        legacy.require(args.config != "-")
        verdict = classify(legacy.load_json(args.evidence),
                           legacy.load_json(args.config), args.now)
    except (OSError, UnicodeError, ValueError, TypeError, RecursionError):
        verdict = legacy.result("INDETERMINATE", "INVALID_OR_MISSING_EVIDENCE")
    print(json.dumps(verdict, sort_keys=True))
    return 2 if verdict["state"] == "INDETERMINATE" else 0


if __name__ == "__main__":
    sys.exit(main())
