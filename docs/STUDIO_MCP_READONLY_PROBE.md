# Official Studio MCP read-only intake, protected draft

This module is an **untrusted observation helper**, not a Studio connection from ChatGPT Android, not a Roblox Studio engine test, and not a GitHub authentication/approval authority.

It follows the public built-in Studio MCP stdio protocol and only invokes MCP initialization, tool discovery, and \`list_roblox_studios\` with **no arguments**. Other Lua execution, instance modification, Play, asset, upload and publish tools are rejected before sending. All returned instance content is treated as untrusted and is not converted to verified session counts.

**Default:** \`python3 tools/studio_mcp_readonly_probe.py\` prints NOT_RUN_DEFAULT without spawning anything. \`--live\` is Windows-only and requires an already installed, explicitly MCP-enabled, independently verified Roblox Studio and trusted \`%LOCALAPPDATA%\Roblox\mcp.bat\` launcher. This draft does NOT independently establish Authenticode or installer provenance; the Windows cmd.exe batch startup has not been tested on a real host. Do not enable unattended live mode before independent host security review. No credentials are read and there are no network calls in this module.

Official docs: https://create.roblox.com/docs/studio/mcp . Roblox official assistant integration: https://github.com/Roblox/roblox-studio-agent-plugin (ChatGPT desktop app/Codex supported; does not mean current ChatGPT Android has installed plugin or a Studio connection).

## Tests

\`python3 -m unittest discover -s tests -p 'test_*.py' -v\`

23 new synthetic tests \`tests/test_studio_mcp_readonly_guards.py\` cover RPC allowlist, malformed/adversarial data, nonfinite JSON, list bounds, total timeout, and unsafe Windows launcher metacharacter rejection. These tests are **offline**; \`stdio_handshake_observed\` can be true for a mock transport but does not authenticate an original Studio process. \`no engine\` and \`no publisher\` assertions are not substitute for actual engine evidence.

This is an isolated protected **CONTROLLER** draft, never to be auto-merged by the normal WORKER/META reviewer. Independent security review of launcher trust, exact source/head CI, other changed paths and cross-ref claim order required. No Roblox upload/Play/publish, billing, Task changes, source gameplay changes or public place publishing.
