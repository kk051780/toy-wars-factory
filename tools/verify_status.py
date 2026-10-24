"""Verify state reports; local claims alone are never runtime evidence."""
from urllib.parse import urlparse

STOPPED = {"NOT_ACTIVE", "NOT_ACTIVE_AI_INFERENCE_UNVERIFIED", "BLOCKED_AUTH_AND_LOCK_NOT_ACTIVE"}

def status_ok(agent, repo):
    if not isinstance(agent, dict): return False
    name = agent.get("status")
    verified = agent.get("workflow_run_verified")
    if name in STOPPED:
        return verified is False
    if name != "ACTIVE_VERIFIED" or verified is not True: return False
    if agent.get("agentic_workflow_compiled") is not True: return False
    url = agent.get("verified_agent_run_url")
    if not isinstance(url,str): return False
    u = urlparse(url)
    base = "/" + repo + "/actions/runs/"
    return u.scheme == "https" and u.netloc == "github.com" and u.path.startswith(base) and u.path[len(base):].isdigit()
