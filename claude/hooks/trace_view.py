#!/usr/bin/env python3
# trace_view.py - reconstruct a session trace written by trace_span.py.
# Usage: python3 ~/.claude/hooks/trace_view.py [session_id|latest]
# Prints: event/tool counts, subagent activity, errors, and a compact timeline.
# For diamond-graph runs this reconstructs the node/tool activity that CLAUDE.md
# 1.5.7 requires in the delivery declaration.

import glob
import json
import os
import sys
from collections import Counter

TRACE_DIR = os.path.expanduser("~/.claude/traces")


def pick_session(arg):
    if arg and arg != "latest":
        p = os.path.join(TRACE_DIR, f"{arg}.jsonl")
        return p if os.path.isfile(p) else None
    files = glob.glob(os.path.join(TRACE_DIR, "*.jsonl"))
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "latest"
    path = pick_session(arg)
    if not path:
        print(f"no trace found (dir: {TRACE_DIR})")
        sys.exit(1)
    spans = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    spans.append(json.loads(line))
                except Exception:
                    pass
    if not spans:
        print(f"{path}: empty")
        sys.exit(0)

    events = Counter(s.get("event") for s in spans)
    tools = Counter(s.get("tool_name") for s in spans if s.get("tool_name"))
    errors = [s for s in spans if s.get("status") == "error"]
    subagents = [s for s in spans if s.get("event") == "SubagentStop"]
    t0 = spans[0].get("ts", 0)
    t1 = spans[-1].get("ts", 0)

    print(f"trace: {os.path.basename(path)}")
    print(f"spans: {len(spans)}   wall: {round(t1 - t0, 1)}s")
    print(f"events: {dict(events)}")
    print(f"tools:  {dict(tools.most_common())}")
    if subagents:
        st = Counter(s.get("agent_type", "?") for s in subagents)
        print(f"subagents finished: {dict(st)}")
    print(f"errors: {len(errors)}")
    for e in errors[:20]:
        print(f"  ! {e.get('tool_name')}  {e.get('target', '')[:80]}")
    print("timeline:")
    for s in spans:
        rel = round(s.get("ts", 0) - t0, 2)
        tag = s.get("tool_name") or s.get("event")
        extra = s.get("target", "") or s.get("agent_type", "")
        stat = f" [{s['status']}]" if s.get("status") == "error" else ""
        print(f"  +{rel:>7}s  {tag}{stat}  {str(extra)[:70]}")


if __name__ == "__main__":
    main()
