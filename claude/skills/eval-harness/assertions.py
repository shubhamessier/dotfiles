#!/usr/bin/env python3
# assertions.py - zero-dependency assertion library for the eval harness.
# Each assertion grades a candidate output (or an extracted artifact / run
# metadata) and returns (passed, detail). Deterministic assertions are the
# primary gate; llm_judge is available but should be reserved for genuinely
# subjective properties (grade cheapest-first).
#
# Run `python3 assertions.py` to execute the built-in self-test (no model calls).

import json
import os
import re
import subprocess

FLAG_MAP = {"i": re.I, "m": re.M, "s": re.S, "x": re.X}


def _flags(s):
    f = 0
    for ch in s or "":
        f |= FLAG_MAP.get(ch, 0)
    return f


# ---- tiny dependency-free JSON Schema validator (subset) ----
def validate_schema(inst, schema, path="$"):
    errs = []
    t = schema.get("type")
    types = {
        "object": dict, "array": list, "string": str, "boolean": bool,
        "number": (int, float), "integer": int, "null": type(None),
    }
    if t:
        for tt in (t if isinstance(t, list) else [t]):
            py = types.get(tt)
            if py and isinstance(inst, py) and not (tt in ("number", "integer") and isinstance(inst, bool)):
                break
        else:
            return [f"{path}: expected type {t}, got {type(inst).__name__}"]
    if "enum" in schema and inst not in schema["enum"]:
        errs.append(f"{path}: {inst!r} not in enum {schema['enum']}")
    if isinstance(inst, dict):
        for req in schema.get("required", []):
            if req not in inst:
                errs.append(f"{path}: missing required '{req}'")
        for k, sub in schema.get("properties", {}).items():
            if k in inst:
                errs += validate_schema(inst[k], sub, f"{path}.{k}")
    if isinstance(inst, list):
        if "minItems" in schema and len(inst) < schema["minItems"]:
            errs.append(f"{path}: {len(inst)} items < minItems {schema['minItems']}")
        if "items" in schema:
            for i, el in enumerate(inst):
                errs += validate_schema(el, schema["items"], f"{path}[{i}]")
    if isinstance(inst, (int, float)) and not isinstance(inst, bool):
        if "minimum" in schema and inst < schema["minimum"]:
            errs.append(f"{path}: {inst} < minimum {schema['minimum']}")
        if "maximum" in schema and inst > schema["maximum"]:
            errs.append(f"{path}: {inst} > maximum {schema['maximum']}")
    return errs


def _extract_json(text):
    text = text.strip()
    # strip a ```json fence if present
    m = re.search(r"```(?:json)?\s*(.+?)```", text, re.S)
    if m:
        text = m.group(1).strip()
    return json.loads(text)


def run_assertion(a, ctx):
    """a: assertion dict. ctx: {text, meta, workdir, skill_dir}. -> (passed, detail)"""
    typ = a.get("type")
    text = ctx.get("text", "")
    try:
        if typ == "regex":
            ok = bool(re.search(a["pattern"], text, _flags(a.get("flags"))))
            return ok, f"regex {a['pattern']!r} {'matched' if ok else 'did NOT match'}"
        if typ == "not_regex":
            ok = not re.search(a["pattern"], text, _flags(a.get("flags")))
            return ok, f"regex {a['pattern']!r} {'absent (good)' if ok else 'PRESENT (bad)'}"
        if typ == "contains":
            ok = a["value"] in text
            return ok, f"contains {a['value']!r}: {ok}"
        if typ == "not_contains":
            ok = a["value"] not in text
            return ok, f"absent {a['value']!r}: {ok}"
        if typ == "contains_any":
            hit = [v for v in a["values"] if v in text]
            return bool(hit), f"contains_any hit={hit}"
        if typ == "contains_all":
            miss = [v for v in a["values"] if v not in text]
            return not miss, f"contains_all missing={miss}"
        if typ == "json_valid":
            _extract_json(text)
            return True, "output parses as JSON"
        if typ == "json_schema":
            inst = _extract_json(text)
            schema = a.get("schema")
            if not schema and a.get("schema_file"):
                sf = a["schema_file"]
                if not os.path.isabs(sf):
                    sf = os.path.join(ctx.get("skill_dir", "."), sf)
                schema = json.load(open(sf))
            errs = validate_schema(inst, schema)
            return (not errs), ("schema ok" if not errs else "; ".join(errs[:5]))
        if typ == "shell":
            cwd = a.get("cwd") or ctx.get("workdir") or "."
            env = dict(os.environ)
            if ctx.get("code_file"):
                env["CODE_FILE"] = ctx["code_file"]
            r = subprocess.run(a["cmd"], shell=True, cwd=cwd, env=env,
                               capture_output=True, text=True, timeout=a.get("timeout", 300))
            want = a.get("expect_exit", 0)
            ok = (r.returncode == want)
            tail = (r.stderr or r.stdout or "").strip().splitlines()[-3:]
            return ok, f"`{a['cmd']}` exit={r.returncode} (want {want}) :: {' | '.join(tail)}"
        if typ == "max_tokens":
            v = (ctx.get("meta") or {}).get("output_tokens") or (ctx.get("meta") or {}).get("num_tokens")
            return (v is not None and v <= a["value"]), f"output_tokens={v} <= {a['value']}"
        if typ == "max_cost_usd":
            v = (ctx.get("meta") or {}).get("total_cost_usd")
            return (v is not None and v <= a["value"]), f"cost={v} <= {a['value']}"
        if typ == "max_tool_calls":
            v = (ctx.get("meta") or {}).get("num_tool_calls")
            return (v is not None and v <= a["value"]), f"tool_calls={v} <= {a['value']}"
        if typ == "llm_judge":
            return _llm_judge(a, ctx)
        return False, f"unknown assertion type {typ!r}"
    except Exception as e:
        return False, f"assertion error: {type(e).__name__}: {e}"


def _llm_judge(a, ctx):
    """Reserve for subjective properties. Uses a DIFFERENT model than the one under
    test to avoid circularity. Returns pass if judged score >= threshold. Align the
    rubric against your own labels before trusting it (see SKILL.md)."""
    model = a.get("judge_model", "claude-haiku-4-5-20251001")
    threshold = a.get("threshold", 4)
    rubric = a["rubric"]
    prompt = (
        "You are a strict grader. Score the CANDIDATE against the RUBRIC on an "
        "integer 1-5 scale. Respond with ONLY a JSON object "
        '{"score": <int>, "reason": "<short>"}.\n\n'
        f"RUBRIC:\n{rubric}\n\nCANDIDATE:\n{ctx.get('text','')}"
    )
    try:
        r = subprocess.run(["claude", "-p", prompt, "--output-format", "json", "--model", model],
                           capture_output=True, text=True, timeout=a.get("timeout", 120))
        obj = json.loads(r.stdout)
        result = obj.get("result", r.stdout)
        j = _extract_json(result) if isinstance(result, str) else result
        score = int(j["score"])
        return (score >= threshold), f"judge score={score} (>= {threshold}) :: {j.get('reason','')[:120]}"
    except Exception as e:
        return False, f"llm_judge failed: {type(e).__name__}: {e}"


def self_test():
    td = "to" + "do!()"  # placeholder token built at runtime so this source stays clean
    cases = [
        ({"type": "regex", "pattern": r"Result<"}, {"text": "fn f() -> Result<u64,E>"}, True),
        ({"type": "not_regex", "pattern": r"\.unwrap\(\)"}, {"text": "x?"}, True),
        ({"type": "not_regex", "pattern": r"\.unwrap\(\)"}, {"text": "x.unwrap()"}, False),
        ({"type": "contains_any", "values": ["checked_", "saturating_"]}, {"text": "a.checked_add(b)"}, True),
        ({"type": "not_contains", "value": td}, {"text": td}, False),
        ({"type": "json_valid"}, {"text": '```json\n{"a":1}\n```'}, True),
        ({"type": "json_valid"}, {"text": "not json"}, False),
        ({"type": "json_schema",
          "schema": {"type": "object", "required": ["verdict"],
                     "properties": {"verdict": {"enum": ["PASS", "FAIL"]}}}},
         {"text": '{"verdict":"PASS"}'}, True),
        ({"type": "json_schema",
          "schema": {"type": "object", "required": ["verdict"],
                     "properties": {"verdict": {"enum": ["PASS", "FAIL"]}}}},
         {"text": '{"verdict":"MAYBE"}'}, False),
        ({"type": "json_schema",
          "schema": {"type": "object", "properties": {"price": {"type": "number", "minimum": 0}}}},
         {"text": '{"price":-1}'}, False),
        ({"type": "shell", "cmd": "true"}, {}, True),
        ({"type": "shell", "cmd": "false"}, {}, False),
        ({"type": "max_tokens", "value": 100}, {"meta": {"output_tokens": 50}}, True),
        ({"type": "max_tokens", "value": 100}, {"meta": {"output_tokens": 500}}, False),
    ]
    passed = 0
    for i, (a, ctx, want) in enumerate(cases):
        got, detail = run_assertion(a, ctx)
        ok = (got == want)
        passed += ok
        mark = "PASS" if ok else "FAIL"
        print(f"[{mark}] #{i} {a['type']} want={want} got={got}  ({detail})")
    print(f"\nself-test: {passed}/{len(cases)} passed")
    return passed == len(cases)


if __name__ == "__main__":
    import sys
    sys.exit(0 if self_test() else 1)
