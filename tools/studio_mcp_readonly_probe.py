#!/usr/bin/env python3
"""Official Roblox Studio MCP *read-only* handshake; untrusted host advisory.

No editor, play, Luau, account mutation, upload, or publishing tools permitted.
Offline/mocked success never attests Studio ownership, identity or gameplay.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path, PureWindowsPath
import queue
import re
import subprocess
import sys
import threading
import time
from typing import Any

PROTOCOL_VERSION = "2025-06-18"
MAX_LINE = 131072
MAX_REPLY_COUNT = 16
MAX_TOOLS = 128
MAX_STUDIO_ITEMS = 16
MAX_CONTENT_CHARS = 4096
TIMEOUT = 12
ALLOWED_TOOLS = frozenset({"list_roblox_studios"})

class ProbeError(ValueError):
    pass

def _json_unique(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise ProbeError("duplicate MCP JSON key")
        out[k] = v
    return out

def _strict_json_constant(value):
    raise ProbeError("nonfinite MCP JSON value")

def validate_localappdata(value: str) -> str:
    """Lexically reject Windows cmd.exe metacharacters; no signature claim."""
    if (type(value) is not str or not 3 <= len(value) <= 240 or
            any(x in value for x in '\r\n\x00%!^&|<>()"') or
            re.fullmatch(r'[A-Za-z]:\\[^*?<>|"\x00-\x1f]+', value) is None or
            not PureWindowsPath(value).is_absolute() or
            '..' in PureWindowsPath(value).parts):
        raise ProbeError("unsafe local Studio launcher path")
    return value.rstrip('\\')

def _mcp_popen_spec(launcher: Path):
    """Construct a fixed, non-shell stdio command; *not* launcher trust proof.

    The host's separate lexical, symlink, file and path checks must precede
    execution. Roblox's official Windows setup starts mcp.bat from its own
    Roblox directory; subprocess cwd is equivalent to cmd.exe 'cd /d' here.
    """
    if (not isinstance(launcher, Path) or
            launcher.name.lower() != "mcp.bat" or
            launcher.parent.name.lower() != "roblox"):
        raise ProbeError("unreviewed Studio MCP launcher location")
    return (["cmd.exe", "/c", str(launcher)], {
        "cwd": str(launcher.parent),
        "shell": False,
        "stdin": subprocess.PIPE,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.DEVNULL,
        "text": True,
        "encoding": "utf-8",
        "bufsize": 1,
    })

class JsonLineTransport:
    """stdio-only local Windows launcher; does not trust server self-description."""
    def __init__(self, *, localappdata: str, runner=subprocess.Popen):
        if os.name != "nt":
            raise ProbeError("live Studio MCP requires a trusted Windows host")
        root = Path(validate_localappdata(localappdata))
        launcher = root / "Roblox" / "mcp.bat"
        if root.is_symlink() or launcher.is_symlink() or not launcher.is_file():
            raise ProbeError("local Studio MCP launcher unavailable")
        try:
            if launcher.resolve(strict=True) != (root.resolve(strict=True) / "Roblox" / "mcp.bat"):
                raise ProbeError("Studio MCP launcher escaped local root")
        except OSError as ex:
            raise ProbeError("Studio MCP launcher resolution failed") from ex
        command, options = _mcp_popen_spec(launcher)
        try:
            self.proc = runner(command, **options)
        except (OSError, subprocess.SubprocessError):
            raise ProbeError("Studio MCP launcher could not start") from None
        if self.proc.stdin is None or self.proc.stdout is None:
            raise ProbeError("MCP pipes unavailable")
        self.q = queue.Queue(maxsize=MAX_REPLY_COUNT + 1)
        self.sequence = 0
        def reader():
            try:
                for line in self.proc.stdout:
                    if len(line) > MAX_LINE:
                        try: self.q.put_nowait(ProbeError("oversize Studio MCP response"))
                        except queue.Full: pass
                        return
                    try: self.q.put_nowait(line)
                    except queue.Full: return
            except Exception:
                try: self.q.put_nowait(ProbeError("Studio MCP reader failure"))
                except queue.Full: pass
        self.thread = threading.Thread(target=reader, daemon=True)
        self.thread.start()

    def _send(self, data):
        payload = json.dumps(data, separators=(",", ":"), ensure_ascii=True)
        if len(payload) > 4096:
            raise ProbeError("oversize Studio MCP command")
        try:
            self.proc.stdin.write(payload + "\n")
            self.proc.stdin.flush()
        except (BrokenPipeError, OSError) as ex:
            raise ProbeError("Studio MCP process write failed") from ex

    def request(self, method: str, params: dict) -> dict:
        if method not in {"initialize", "tools/list", "tools/call"}:
            raise ProbeError("unsafe Studio MCP RPC method")
        if method == "tools/list" and params != {}:
            raise ProbeError("unreviewed Studio MCP tool pagination")
        if method == "initialize" and (
            type(params) is not dict or set(params) != {"protocolVersion", "capabilities", "clientInfo"} or
            params["protocolVersion"] != PROTOCOL_VERSION or
            params["capabilities"] != {} or
            params["clientInfo"] != {"name": "toy-wars-readonly-probe", "version": "0.1"}
        ):
            raise ProbeError("unreviewed Studio MCP initialization")
        if method == "tools/call" and (
            type(params) is not dict or set(params) != {"name", "arguments"} or
            params.get("name") not in ALLOWED_TOOLS or params.get("arguments") != {}
        ):
            raise ProbeError("unsafe Studio MCP tool call")
        self.sequence += 1
        ident = self.sequence
        self._send({"jsonrpc": "2.0", "id": ident, "method": method, "params": params})
        deadline = time.monotonic() + TIMEOUT
        for _ in range(MAX_REPLY_COUNT):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ProbeError("Studio MCP total response deadline exceeded")
            try:
                line = self.q.get(timeout=remaining)
            except queue.Empty as ex:
                raise ProbeError("Studio MCP response timeout") from ex
            if isinstance(line, BaseException):
                raise line
            if type(line) is not str or len(line) > MAX_LINE:
                raise ProbeError("invalid MCP line")
            try:
                msg = json.loads(line, object_pairs_hook=_json_unique,
                                 parse_constant=_strict_json_constant)
            except (ValueError, UnicodeError) as ex:
                raise ProbeError("invalid MCP JSON") from ex
            if type(msg) is not dict or msg.get("jsonrpc") != "2.0":
                raise ProbeError("invalid MCP envelope")
            if "id" not in msg:
                continue
            if type(msg["id"]) is not int or msg["id"] != ident:
                raise ProbeError("MCP response identity mismatch")
            if "error" in msg or type(msg.get("result")) is not dict:
                raise ProbeError("Studio MCP error or missing result")
            return msg["result"]
        raise ProbeError("MCP notification overflow")

    def notify(self, method, params):
        if method != "notifications/initialized" or params != {}:
            raise ProbeError("unsafe Studio MCP notification")
        self._send({"jsonrpc": "2.0", "method": method, "params": params})

    def close(self):
        try:
            if self.proc.stdin:
                self.proc.stdin.close()
            if self.proc.poll() is None:
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
        except (OSError, ValueError):
            pass

def probe(transport: Any) -> dict:
    """No session binding; only count untrusted content items, never parse IDs."""
    intro = transport.request("initialize", {
        "protocolVersion": PROTOCOL_VERSION, "capabilities": {},
        "clientInfo": {"name": "toy-wars-readonly-probe", "version": "0.1"}})
    if type(intro) is not dict or intro.get("protocolVersion") != PROTOCOL_VERSION:
        raise ProbeError("unsupported Studio MCP version")
    transport.notify("notifications/initialized", {})
    listing = transport.request("tools/list", {})
    if (type(listing) is not dict or type(listing.get("tools")) is not list or
            not 1 <= len(listing["tools"]) <= MAX_TOOLS or listing.get("nextCursor")):
        raise ProbeError("Studio MCP tool listing absent or paginated")
    names = [item.get("name") for item in listing["tools"] if type(item) is dict]
    if names.count("list_roblox_studios") != 1:
        raise ProbeError("Studio instance list tool missing or ambiguous")
    reply = transport.request("tools/call", {"name": "list_roblox_studios", "arguments": {}})
    if (type(reply) is not dict or ("isError" in reply and reply["isError"] is not False) or
            type(reply.get("content")) is not list or len(reply["content"]) > MAX_STUDIO_ITEMS or
            any(type(item) is not dict or item.get("type") != "text" or
                type(item.get("text")) is not str or len(item["text"]) > MAX_CONTENT_CHARS
                for item in reply["content"])):
        raise ProbeError("Studio MCP instance list untrusted/oversize")
    return {
        "status": "STUDIO_MCP_READ_ONLY_LIST_RESULT_UNTRUSTED",
        "stdio_handshake_observed": True,
        "studio_session_authenticated": False,
        "connected_studio_count_unverified": None,
        "studio_engine_verified": False,
        "play_started": False,
        "scripts_modified": False,
        "external_publish": False,
        "tool_calls": ["initialize", "tools/list", "list_roblox_studios"],
        "content_items": len(reply["content"])
    }

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true",
                        help="read-only probe against an already enabled trusted local Studio MCP")
    args = parser.parse_args(argv)
    if not args.live:
        print(json.dumps({"status": "NOT_RUN_DEFAULT", "studio_connected": False,
                          "game_tested": False, "scripts_modified": False,
                          "network": False}))
        return 0
    transport = None
    try:
        transport = JsonLineTransport(localappdata=os.environ.get("LOCALAPPDATA", ""))
        print(json.dumps(probe(transport), sort_keys=True))
        return 0
    except ProbeError:
        print(json.dumps({"status": "MCP_UNAVAILABLE_OR_FAILED",
                          "engine_verified": False, "scripts_modified": False,
                          "publish": False}), file=sys.stderr)
        return 2
    finally:
        if transport is not None:
            transport.close()

if __name__ == "__main__":
    raise SystemExit(main())
