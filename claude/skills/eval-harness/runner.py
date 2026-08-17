#!/usr/bin/env python3
# runner.py - zero-dependency eval/regression harness for Claude Code.
# Replays frozen task cases through `claude -p --output-format json`, grades each
# with assertions.py (deterministic first, llm_judge only where declared), writes
# a versioned results file, and diffs against a baseline to surface regressions.
#
# Usage:
#   python3 runner.py                      # run every cases/*.jsonl, invoke the model
#   python3 runner.py --cases cases/x.jsonl
#   python3 runner.py --model claude-opus-4-8
#   python3 runner.py --update-baseline    # write results/baseline.json from this run
#   python3 runner.py --self-test          # assertion-library unit test, NO model calls
#   python3 runner.py --dry                # grade each case's "mock" field, NO model calls
#
# Exit code is non-zero if any case fails or a regression vs baseline is detected,
# so it gates a git pre-push hook or CI (CLAUDE.md testing gate).
#
# Case file: JSONL, one object per line:
#   {"id": "...", "prompt": "...", "asserts": [ {..assertion..}, ... ],
#    "extract": {"lang": "rust", "to": "gen.rs"},   # optional: pull first code fence to a file
#    "cwd": ".", "mock": "canned output for --dry", "critical_default": true}

import argparse
import glob
import json
import os
import re
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import assertions  # noqa: E402


def load_cases(paths):
    cases = []
    for p in paths:
        with open(p) as f:
            for ln, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    c = json.loads(line)
                    c.setdefault("_src", f"{os.path.basename(p)}:{ln}")
                    cases.append(c)
                except json.JSONDecodeError as e:
                    print(f"skip {p}:{ln} (bad JSON: {e})", file=sys.stderr)
    return cases


def invoke_model(prompt, model, cwd, timeout):
    cmd = ["claude", "-p", prompt, "--output-format", "json"]
    if model:
        cmd += ["--model", model]
    r = subprocess.run(cmd, cwd=cwd or None, capture_output=True, text=True, timeout=timeout)
    try:
        obj = json.loads(r.stdout)
    except Exception:
        return r.stdout, {}
    text = obj.get("result", r.stdout)
    meta = {k: obj.get(k) for k in ("total_cost_usd", "duration_ms", "num_turns",
                                    "session_id", "is_error", "usage") if k in obj}
    u = obj.get("usage") or {}
    if isinstance(u, dict):
        meta["output_tokens"] = u.get("output_tokens")
    return text, meta


def extract_block(text, lang):
    m = re.search(r"```" + re.escape(lang) + r"\s*(.+?)```", text, re.S)
    if not m:
        m = re.search(r"```\w*\s*(.+?)```", text, re.S)
    return m.group(1).strip() if m else None


def grade_case(case, text, meta):
    ctx = {"text": text, "meta": meta, "skill_dir": HERE, "workdir": case.get("cwd", ".")}
    tmp = None
    if case.get("extract") and text:
        ex = case["extract"]
        block = extract_block(text, ex.get("lang", ""))
        if block is not None:
            tmp = tempfile.mkdtemp(prefix="evalcase-")
            cf = os.path.join(tmp, ex.get("to", "gen.txt"))
            with open(cf, "w") as f:
                f.write(block)
            ctx["workdir"] = tmp
            ctx["code_file"] = cf
    crit_default = case.get("critical_default", True)
    results = []
    passed = True
    for a in case.get("asserts", []):
        ok, detail = assertions.run_assertion(a, ctx)
        critical = a.get("critical", crit_default)
        results.append({"type": a.get("type"), "desc": a.get("desc", ""),
                        "ok": ok, "critical": critical, "detail": detail})
        if critical and not ok:
            passed = False
    return passed, results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", nargs="*")
    ap.add_argument("--model", default=None)
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--update-baseline", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        sys.exit(0 if assertions.self_test() else 1)

    case_paths = args.cases or sorted(glob.glob(os.path.join(HERE, "cases", "*.jsonl")))
    if not case_paths:
        print("no case files found under cases/", file=sys.stderr)
        sys.exit(2)
    cases = load_cases(case_paths)
    if not cases:
        print("no cases loaded", file=sys.stderr)
        sys.exit(2)

    run = {"model": args.model or "session-default", "mode": "dry" if args.dry else "live",
           "cases": {}}
    n_pass = 0
    for c in cases:
        cid = c.get("id", c.get("_src", "?"))
        try:
            if args.dry:
                text, meta = c.get("mock", ""), {}
            else:
                text, meta = invoke_model(c["prompt"], args.model, c.get("cwd"), args.timeout)
            ok, results = grade_case(c, text, meta)
        except FileNotFoundError:
            print("ERROR: `claude` CLI not found on PATH. Use --dry to test offline.", file=sys.stderr)
            sys.exit(2)
        except Exception as e:
            ok, results = False, [{"type": "runner", "ok": False, "critical": True,
                                   "detail": f"{type(e).__name__}: {e}"}]
        n_pass += ok
        run["cases"][cid] = {"pass": ok, "asserts": results}
        mark = "PASS" if ok else "FAIL"
        print(f"[{mark}] {cid}")
        if not ok:
            for r in results:
                if not r["ok"] and r.get("critical"):
                    print(f"        - {r.get('type')} {r.get('desc','')}: {r['detail']}")

    total = len(cases)
    print(f"\n{n_pass}/{total} cases passed  (model={run['model']}, mode={run['mode']})")

    # regression diff vs baseline
    base_path = os.path.join(HERE, "results", "baseline.json")
    regressed = []
    if os.path.isfile(base_path) and not args.dry:
        base = json.load(open(base_path))
        for cid, cur in run["cases"].items():
            was = base.get("cases", {}).get(cid, {}).get("pass")
            if was is True and cur["pass"] is False:
                regressed.append(cid)
        if regressed:
            print(f"\nREGRESSION vs baseline: {regressed}")

    # write versioned results (epoch stamp; harness has no wall-clock constraint)
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    stamp = str(int(time.time()))
    outp = os.path.join(HERE, "results", f"run-{stamp}.json")
    json.dump(run, open(outp, "w"), indent=1)
    print(f"results: {outp}")
    if args.update_baseline and not args.dry:
        json.dump(run, open(base_path, "w"), indent=1)
        print(f"baseline updated: {base_path}")

    sys.exit(1 if (n_pass < total or regressed) else 0)


if __name__ == "__main__":
    main()
