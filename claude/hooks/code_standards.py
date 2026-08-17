#!/usr/bin/env python3
# code_standards.py - PostToolUse hook (Edit|Write|MultiEdit)
# Language-aware code-standards check. WARN + inject only: never blocks an edit.
# On violation it emits hookSpecificOutput.additionalContext so Claude self-corrects
# on the next turn. Fail-open: any internal error exits 0 with no output.
#
# Enforcement philosophy mirrors the generic code-standards section of CLAUDE.md:
#   - no placeholders / stubs in finished code
#   - no leftover merge markers
#   - no non-ASCII (emoji) in source
#   - no obvious committed secrets
#   - language-specific hazards (e.g. Rust .unwrap()/expect, floats on money).
#
# Config override (optional): ~/.claude/hooks/code_standards.config.json
#   {"disabled_rules": ["rust-float-money"], "extra_money_words": ["strike"]}

import json
import os
import re
import sys

CONFIG_PATH = os.path.expanduser("~/.claude/hooks/code_standards.config.json")

PROSE_EXT = {".md", ".markdown", ".txt", ".rst", ".csv", ".tsv", ".json", ".lock"}
CODE_EXT = {
    ".rs", ".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".c", ".h", ".cpp",
    ".hpp", ".cc", ".java", ".rb", ".sh", ".bash", ".zsh", ".sol", ".move",
}

MONEY_WORDS = [
    "price", "qty", "quantity", "amount", "rate", "balance", "lamport", "sol",
    "usd", "usdc", "money", "fee", "size", "notional", "pnl", "collateral",
    "margin", "funding", "slippage", "spread", "tip", "wei", "gwei", "token",
]


def load_config():
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


def is_test_path(path: str) -> bool:
    p = path.replace("\\", "/").lower()
    base = os.path.basename(p)
    if any(seg in p for seg in ("/test/", "/tests/", "/__tests__/", "/examples/", "/benches/", "/fixtures/", "/spec/")):
        return True
    return any(t in base for t in ("test_", "_test.", ".test.", ".spec.", "conftest.py", "_spec."))


# each rule: (id, applies(path,ext) -> bool, line_regex or fn, message)
def universal_rules(cfg):
    money = "|".join(re.escape(w) for w in MONEY_WORDS + cfg.get("extra_money_words", []))
    return [
        ("merge-marker", lambda path, ext: True,
         re.compile(r"^(<{7}|={7}|>{7})(\s|$)"),
         "leftover merge-conflict marker"),
        ("placeholder", lambda path, ext: ext in CODE_EXT,
         re.compile(r"\b(TODO|FIXME|XXX|HACK)\b|todo!\s*\(|unimplemented!\s*\(|\bpass\s*#\s*TODO"),
         "placeholder / incomplete-work marker in code"),
        ("secret-akia", lambda path, ext: True,
         re.compile(r"AKIA[0-9A-Z]{16}"),
         "looks like a hardcoded AWS access key"),
        ("secret-privkey", lambda path, ext: True,
         re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
         "hardcoded private key block"),
        ("secret-slack", lambda path, ext: True,
         re.compile(r"xox[baprs]-[0-9A-Za-z-]{10,}"),
         "looks like a hardcoded Slack token"),
    ]


def lang_rules(cfg, ext, path):
    money = r"(" + "|".join(re.escape(w) for w in MONEY_WORDS + cfg.get("extra_money_words", [])) + r")"
    test = is_test_path(path)
    rules = []
    if ext == ".rs":
        if not test:
            rules.append(("rust-unwrap", re.compile(r"\.unwrap\(\)|\.expect\s*\("),
                          "unwrap()/expect() in non-test Rust (handle the error or halt cleanly)"))
            rules.append(("rust-panic", re.compile(r"\bpanic!\s*\("),
                          "panic!() in non-test Rust"))
        rules.append(("rust-float-money",
                      re.compile(r"\b(f64|f32)\b.*" + money + r"|" + money + r".*\b(f64|f32)\b", re.IGNORECASE),
                      "float type (f64/f32) on an apparent financial value - use fixed-point/decimal"))
    elif ext == ".py":
        rules.append(("py-bare-except", re.compile(r"except\s*:"), "bare 'except:' - catch a specific exception"))
        rules.append(("py-eval-exec", re.compile(r"\beval\s*\(|\bexec\s*\("), "eval()/exec() on possibly untrusted input"))
    elif ext in (".ts", ".tsx", ".js", ".jsx"):
        rules.append(("js-debugger", re.compile(r"(^|\s)debugger\s*;?\s*$"), "leftover 'debugger' statement"))
    elif ext == ".go":
        if not test:
            rules.append(("go-panic", re.compile(r"\bpanic\s*\("), "panic() in non-test Go"))
    return [(rid, None, rx, msg) for (rid, rx, msg) in rules]


def scan(path: str, cfg: dict):
    ext = os.path.splitext(path)[1].lower()
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except (UnicodeDecodeError, OSError):
        return []
    if len(text) > 2_000_000:
        return []
    lines = text.splitlines()
    disabled = set(cfg.get("disabled_rules", []))
    findings = []

    # non-ASCII (emoji) check in code files
    if ext in CODE_EXT and "non-ascii" not in disabled:
        for i, ln in enumerate(lines, 1):
            for ch in ln:
                if ord(ch) > 127:
                    findings.append((i, "non-ascii", f"non-ASCII char {ch!r} in source"))
                    break

    uni = [(rid, applies, rx, msg) for (rid, applies, rx, msg) in universal_rules(cfg) if rid not in disabled]
    lang = [(rid, applies, rx, msg) for (rid, applies, rx, msg) in lang_rules(cfg, ext, path) if rid not in disabled]

    for i, ln in enumerate(lines, 1):
        for rid, applies, rx, msg in uni:
            if applies(path, ext) and rx.search(ln):
                findings.append((i, rid, msg))
        for rid, _applies, rx, msg in lang:
            if rx.search(ln):
                findings.append((i, rid, msg))
    return findings


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    tool_input = data.get("tool_input") or {}
    path = tool_input.get("file_path") or tool_input.get("path")
    if not path or not os.path.isfile(path):
        sys.exit(0)
    cfg = load_config()
    try:
        findings = scan(path, cfg)
    except Exception:
        sys.exit(0)
    if not findings:
        sys.exit(0)
    # cap and format
    findings = findings[:40]
    rel = path
    lines_out = [f"  {rel}:{ln}  [{rid}] {msg}" for (ln, rid, msg) in findings]
    ctx = (
        "code-standards check flagged the file just written "
        f"({len(findings)} item(s)). These are warnings, not blocks - fix them "
        "before considering this file done:\n" + "\n".join(lines_out)
    )
    out = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": ctx[:9500],
        }
    }
    print(json.dumps(out))
    sys.exit(0)


if __name__ == "__main__":
    main()
