#!/usr/bin/env python3
# trace_span.py - observability hook. Appends one JSONL span per lifecycle event
# to ~/.claude/traces/<session_id>.jsonl. Wired on PostToolUse (all tools),
# SubagentStop, SessionStart, Stop. Fail-open: never breaks the session.
#
# No secrets are stored: tool_input is hashed (sha256), only a short human target
# (file path / command head / first key) is kept in clear. Token/cost fields are
# recorded only if the event payload happens to carry them (hooks are not given
# token usage today), so downstream cost accounting is best-effort.
#
# View a run:  python3 ~/.claude/hooks/trace_view.py [session_id|latest]

import hashlib
import json
import os
import sys
import time

TRACE_DIR = os.path.expanduser("~/.claude/traces")


def sha(obj) -> str:
    try:
        return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()[:16]
    except Exception:
        return ""


def target_of(tool_name: str, tool_input: dict) -> str:
    if not isinstance(tool_input, dict):
        return ""
    for k in ("file_path", "path", "command", "url", "pattern", "query", "prompt", "description"):
        if k in tool_input and tool_input[k]:
            return str(tool_input[k])[:200]
    keys = list(tool_input.keys())
    return ("keys:" + ",".join(keys[:5])) if keys else ""


def classify(tool_response) -> str:
    try:
        if isinstance(tool_response, dict):
            if tool_response.get("is_error") or tool_response.get("error"):
                return "error"
        if isinstance(tool_response, str) and tool_response.lower().startswith("error"):
            return "error"
    except Exception:
        pass
    return "ok"


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    try:
        session = data.get("session_id") or "unknown"
        event = data.get("hook_event_name") or "unknown"
        span = {
            "ts": round(time.time(), 3),
            "event": event,
            "session_id": session,
            "cwd": data.get("cwd"),
        }
        if "tool_name" in data:
            ti = data.get("tool_input") or {}
            span["tool_name"] = data.get("tool_name")
            span["target"] = target_of(data.get("tool_name"), ti)
            span["input_sha"] = sha(ti)
            if event == "PostToolUse":
                span["status"] = classify(data.get("tool_response"))
        if data.get("agent_id"):
            span["agent_id"] = data.get("agent_id")
        if data.get("agent_type"):
            span["agent_type"] = data.get("agent_type")
        # opportunistic usage capture if ever present
        for uk in ("usage", "total_tokens", "output_tokens", "input_tokens"):
            if uk in data:
                span[uk] = data[uk]

        os.makedirs(TRACE_DIR, exist_ok=True)
        # sanitize session for filename
        safe = "".join(c for c in str(session) if c.isalnum() or c in "-_")[:80] or "unknown"
        with open(os.path.join(TRACE_DIR, f"{safe}.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(span, default=str) + "\n")
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
