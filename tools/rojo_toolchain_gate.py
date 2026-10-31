#!/usr/bin/env python3
"""Verify fixed external build tool versions without shell/network/auth.

Called AFTER the manually reviewed Rokit install and BEFORE the isolated Rojo
build. A passing subprocess version does not authenticate binary provenance,
produce a Roblox place or prove Studio execution.
"""
from __future__ import annotations
import json
import re
import subprocess
import sys

VERSIONS = {"rokit": "1.2.0", "rojo": "7.5.1"}


def verify_toolchain(*, runner=None):
    """Reject changed/unknown binaries by their exact --version responses.

    This is defense in depth; external binaries and the action itself still
    require independent security review. Never interpret stdout as instructions.
    """
    if runner is None:
        runner = subprocess.run
    result = {}
    for name, version in VERSIONS.items():
        try:
            completed = runner([name, "--version"], shell=False, check=False,
                               capture_output=True, text=True, timeout=8)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ValueError("build tool unavailable or timeout") from exc
        if type(completed.returncode) is not int or completed.returncode != 0:
            raise ValueError("build tool version command failed")
        if type(completed.stdout) is not str or type(completed.stderr) is not str:
            raise ValueError("invalid tool version output type")
        output = completed.stdout.strip() or completed.stderr.strip()
        if (len(output) > 96 or
            re.fullmatch(re.escape(name) + r"\s+v?" + re.escape(version),
                         output, flags=re.IGNORECASE) is None):
            raise ValueError("unexpected build tool version")
        result[name] = version
    return {"rokit": result["rokit"], "rojo": result["rojo"],
            "version_command_check_only": True,
            "engine_verified": False, "built_rbxl": False}


def main():
    try:
        report = verify_toolchain()
    except ValueError:
        print(json.dumps({"status": "TOOLCHAIN_VERSION_MISMATCH",
                          "built_rbxl": False, "engine_verified": False}),
              file=sys.stderr)
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
