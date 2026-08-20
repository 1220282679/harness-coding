#!/usr/bin/env python3
"""Static consistency validation for the harness-coding skill documents (pure standard library, no third-party deps).

Cross-document checks over the skill's .md files:
1. Frontmatter: every .md has a name: + description: block (except the root README.md, which carries
   no frontmatter by convention) and the block is strict-YAML-safe (a ': ' inside a plain-scalar value
   breaks strict parsers — "mapping values are not allowed here")
2. Internal references: every path mention under references/ templates/ scripts/ adapters/ exists on disk
   (paths prefixed templates/ or adapters/ are relative to the references/ directory; scripts/ is relative
   to the repo root — both bases are tried)
3. Capability usage: backticked snake_case identifiers in SKILL.md are all either contract capabilities
   or known phase names (WARN, not FAIL)
4. Role dispatch: roles explorer / implementer / reviewer each have a dispatch template under references/templates/
5. Phase set: the report-template skeleton's PHASE markers match the stage-table phase set
6. Adapter mappings: every adapter/template §1 capability table lists all 12 contract capabilities
   (scanned within the §1 section only, not the whole file)
7. Capability-name typos: backticked snake_case identifiers anywhere in the skill docs within edit
   distance 1 of a contract capability name are flagged as likely typos (WARN, not FAIL)
8. Protocol invariants: canonical reporting-protocol literals (default report dir / truncation
   thresholds / archive threshold / DONE marker / status line) appear in every doc that should carry
   them — changing the protocol in one place and not its siblings fails the run, killing the drift risk
   from the protocol being specified across SKILL.md, capability-contract.md, report-template.md,
   write-report.md, and the adapters.

Usage: python scripts/consistency-check.py
All checks print PASS and exit 0; any failure prints FAIL and exits 1.
Note: on Windows consoles that garble text under GBK, set PYTHONIOENCODING=utf-8 first (this script already tries to force UTF-8 in main).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
# Only the skill's own documents are validated. Runtime report files (capability-contract
# report.dir, default harness-reports/) carry no frontmatter and must not fail the checks; the
# report archive directory is likewise excluded. READMEs (README.md and its translations
# like README-zh.md) are validated for internal references but not for frontmatter
# (a README carries no frontmatter by convention).
# Exclusions match path *components* (a directory named docs/ / archive/ / harness-reports/), not
# loose substrings — a loose "archive in str(p)" would silently skip any skill doc whose name merely
# contains "archive" (e.g. references/archives.md), hiding real validation failures. harness-reports/
# is the runtime report dir (capability-contract report.dir default) when the skill runs in its own repo.
MD_FILES = sorted(
    p
    for p in REPO.rglob("*.md")
    if "archive" not in p.parts and "docs" not in p.parts and "harness-reports" not in p.parts
)
FRONTMATTER_FILES = [p for p in MD_FILES if not p.name.startswith("README")]

# Capability set, derived from the capability contract (8 required + 4 optional).
REQUIRED = {"read", "write", "edit", "glob", "grep", "run_command", "ask_user", "write_report"}
OPTIONAL = {"spawn_agent", "create_branch", "check_command", "run_quality_gate"}
CAPABILITIES = REQUIRED | OPTIONAL

# Path mentions under the skill's own directories, e.g. references/templates/write-report.md
PATH_RE = re.compile(r"\b(?:references|templates|scripts|adapters)/[\w./-]+")

SKILL_MD = REPO / "SKILL.md"
REPORT_TEMPLATE = REPO / "references/templates/report-template.md"
ROLES = ("explorer", "implementer", "reviewer")

# Sections of the report template we anchor on; heading text is matched loosely (non-ASCII-safe).
SKELETON_RE = re.compile(r"## Skeleton[^\n]*\n(.*?)(?=\n## )", re.S)
STAGE_TABLE_RE = re.compile(r"## Stage[^\n]*Content to Write[^\n]*\n(.*?)(?=\n## )", re.S)


def frontmatter_problems(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8").lstrip(chr(0xFEFF))
    m = re.match(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n", text, re.S)
    if not m:
        return ["missing or unterminated frontmatter"]
    head = m.group(1)
    problems = []
    if not re.search(r"^name:\s*\S", head, re.M):
        problems.append("frontmatter lacks name:")
    if not re.search(r"^description:\s*\S", head, re.M):
        problems.append("frontmatter lacks description:")
    # Strict-YAML plain-scalar safety: in a plain scalar a ':' followed by whitespace is a mapping
    # indicator, so a single-line `key: <value>` whose value contains ': ' fails strict YAML parsers
    # ("mapping values are not allowed here"). This is a pure-stdlib approximation of that rule
    # (no pyyaml dependency): flag any such sequence inside the value of a frontmatter key line.
    for line in head.splitlines():
        kv = re.match(r"^([\w-]+):\s+(.*)$", line)
        if kv and re.search(r":(?=\s)", kv.group(2)):
            problems.append(
                f"frontmatter {kv.group(1)!r} value contains ': ' (plain-scalar break) — "
                "reword the value to remove the colon+space so strict YAML parsers can load it"
            )
    return problems


def check_frontmatter() -> list[str]:
    return [
        f"{p.relative_to(REPO)}: {msg}"
        for p in FRONTMATTER_FILES
        for msg in frontmatter_problems(p)
    ]


def clean_ref(ref: str) -> str:
    """Strip markdown/backtick wrappers and anchors so the path can be checked on disk."""
    ref = ref.split("#")[0]
    return ref.rstrip("/").rstrip(".").strip("`)]'\"").rstrip(".,;:")


def check_references() -> list[str]:
    problems = []
    for p in MD_FILES:
        text = p.read_text(encoding="utf-8")
        for m in PATH_RE.finditer(text):
            target = clean_ref(m.group(0))
            if not target:
                continue
            # docs write templates/ and adapters/ relative to references/, but scripts/ relative to repo root
            if not (REPO / target).exists() and not (REPO / "references" / target).exists():
                problems.append(f"{p.relative_to(REPO)}: missing reference {m.group(0)!r}")
    return problems


def phase_names() -> set[str]:
    """The real phase set: PHASE markers inside the report template's Skeleton section (not the prose
    placeholder `<!-- PHASE: xxx -->` that merely describes the marker format)."""
    text = REPORT_TEMPLATE.read_text(encoding="utf-8")
    m = SKELETON_RE.search(text)
    if not m:
        return set()
    return set(re.findall(r"<!-- PHASE:\s*(\S+)", m.group(1)))


def check_capability_usage() -> list[str]:
    """The methodology body uses only contract capability names plus known phase names. Unknown
    snake_case identifiers are reported as WARN (they may be prose, not capability typos) and do not
    fail the run."""
    text = SKILL_MD.read_text(encoding="utf-8")
    known = CAPABILITIES | phase_names()
    unknown = []
    for m in re.finditer(r"`([a-z][a-z0-9_]*)`", text):
        tok = m.group(1)
        if tok not in known:
            unknown.append(tok)
    return [f"unrecognized capability-like identifier: {u!r}" for u in dict.fromkeys(unknown)]


def levenshtein(a: str, b: str) -> int:
    """Edit distance between two short strings (used for typo detection)."""
    if len(a) < len(b):
        a, b = b, a
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def check_capability_typos() -> list[str]:
    """Backticked snake_case identifiers anywhere in the skill docs that sit within edit distance 1 of a
    contract capability name are flagged as likely typos (WARN, not FAIL). Adapters legitimately name
    harness tools (`read_file`, `apply_patch`, `tool.bash`, …), so the exact-match capability check stays
    limited to SKILL.md (check_capability_usage); this check catches the dangerous class — a capability
    name misspelled by a single character (`writ_report`, `run_commandd`) that would silently break the
    adapter layer or a template."""
    problems = []
    for p in MD_FILES:
        text = p.read_text(encoding="utf-8")
        for m in re.finditer(r"`([a-z][a-z0-9_]*)`", text):
            tok = m.group(1)
            if tok in CAPABILITIES:
                continue
            for cap in CAPABILITIES:
                if levenshtein(tok, cap) == 1:
                    problems.append(
                        f"{p.relative_to(REPO)}: {tok!r} is a likely typo of capability {cap!r}"
                    )
                    break
    return problems


def check_roles() -> list[str]:
    return [
        f"missing dispatch template for role {role!r}"
        for role in ROLES
        if not (REPO / f"references/templates/dispatch-{role}.md").exists()
    ]


def check_phases() -> list[str]:
    skeleton = phase_names()
    if not skeleton:
        return ["no PHASE markers found in report template skeleton"]
    text = REPORT_TEMPLATE.read_text(encoding="utf-8")
    m = STAGE_TABLE_RE.search(text)
    table = set(re.findall(r"^\|\s*`([\w-]+)`\s*\|", m.group(1), re.M)) if m else set()
    if skeleton != table:
        return [f"phase mismatch: skeleton {sorted(skeleton)} vs stage table {sorted(table)}"]
    return []


def check_workflow_phases() -> list[str]:
    """workflow-check.py's hardcoded PHASES list must match the report-template skeleton phase set;
    a phase added to the template but not to the lifecycle validator (or vice versa) would let the
    per-channel lifecycle check drift silently."""
    text = (REPO / "scripts/workflow-check.py").read_text(encoding="utf-8")
    m = re.search(r"PHASES\s*=\s*\[(.*?)\]", text, re.S)
    if not m:
        return ["scripts/workflow-check.py: no PHASES list found"]
    wf_phases = re.findall(r'"([\w-]+)"', m.group(1))
    skeleton = phase_names()
    if not skeleton:
        return ["report template has no skeleton phase set"]
    if set(wf_phases) != skeleton or len(wf_phases) != len(skeleton):
        return [f"workflow-check PHASES {wf_phases} != report-template skeleton {sorted(skeleton)}"]
    return []


ADAPTER_MAPPING_HEADER_RE = re.compile(r"## 1\. Capability Mapping Table")


def section_after(text: str, header: re.Pattern) -> str | None:
    """The text between `header` and the next `## ` (level-2) heading; None when `header` is absent."""
    m = header.search(text)
    if not m:
        return None
    rest = text[m.end():]
    nxt = re.search(r"\n## ", rest)
    return rest[: nxt.start()] if nxt else rest


def check_adapter_mappings() -> list[str]:
    """Every adapter layer and the adapter template must list all 12 contract capabilities in
    the first column of its §1 capability mapping table. A typo'd capability name there (e.g.
    `writ_report`) would silently break the adapter layer. Only backticked first-column cells
    that are contract capabilities are counted, so the legitimate non-capability cells (gate
    names / role names / config keys) don't interfere with the comparison.

    Scanned within the §1 section only — a table elsewhere in the file (e.g. a deviation table)
    whose first column happens to name a capability must not count toward the mapping."""
    problems = []
    for p in MD_FILES:
        text = p.read_text(encoding="utf-8")
        section = section_after(text, ADAPTER_MAPPING_HEADER_RE)
        if section is None:
            continue
        cells = set(re.findall(r"^\|\s*`([a-z][a-z0-9_]*)`\s*\|", section, re.M))
        missing = sorted(CAPABILITIES - (cells & CAPABILITIES))
        if missing:
            problems.append(
                f"{p.relative_to(REPO)}: capability mapping table missing {missing}"
            )
    return problems


# Canonical reporting-protocol literals (capability-contract runtime config + §8). The protocol is
# specified across several documents (SKILL.md / capability-contract.md / report-template.md /
# write-report.md / the adapters), so each literal must appear in every document that carries it —
# a change in one place and not its siblings FAILs, killing the drift risk.
PROTOCOL_INVARIANTS = [
    ("default report dir", "harness-reports/", [
        "SKILL.md",
        "references/capability-contract.md",
        "references/templates/report-template.md",
        "README.md",
        "references/adapters/_adapter-template.md",
        "references/adapters/claude-code.md",
        "references/adapters/codex.md",
        "references/adapters/opencode.md",
        "scripts/report_lib.py",
    ]),
    # The numeric thresholds are anchored to report_lib.py too (its module docstring restates
    # them), so a code change to 100/500/20 without the docs following fails the run.
    ("quality-gate truncation threshold", ">100 lines", [
        "SKILL.md",
        "references/capability-contract.md",
        "references/templates/write-report.md",
        "scripts/report_lib.py",
    ]),
    # SKILL.md's reporting protocol is the high-level summary and carries only the quality-gate
    # truncation (>100); the agent-output truncation (>500) is a §8/write-report detail.
    ("agent-output truncation threshold", ">500 lines", [
        "references/capability-contract.md",
        "references/templates/write-report.md",
        "scripts/report_lib.py",
    ]),
    ("archive threshold", "exceed 20", [
        "SKILL.md",
        "references/capability-contract.md",
        "references/templates/report-template.md",
        "scripts/report_lib.py",
    ]),
    ("DONE marker suffix", "DONE -->", [
        "references/capability-contract.md",
        "references/templates/write-report.md",
        "references/templates/report-template.md",
        "references/adapters/claude-code.md",
        "references/adapters/codex.md",
        "references/adapters/opencode.md",
        "scripts/report_lib.py",
    ]),
    ("report status line", "**Final status**: 🔄 in progress", [
        "references/capability-contract.md",
        "references/templates/report-template.md",
        "references/templates/write-report.md",
        "scripts/report_lib.py",
    ]),
    # Two precise "report not persisted" markers (inline-only vs write anomaly) — every doc that
    # should carry a marker must use the exact literal; a shorthand like a bare "⚠️ report not
    # persisted" would otherwise silently drift from the code's INLINE_MARKER constant.
    ("inline-only report marker", "⚠️ report not persisted (inline-only)", [
        "SKILL.md",
        "README.md",
        "references/capability-contract.md",
        "references/templates/write-report.md",
        "scripts/report_lib.py",
    ]),
    ("write-anomaly report marker", "⚠️ report not persisted — write anomaly", [
        "SKILL.md",
        "README.md",
        "references/capability-contract.md",
        "references/templates/write-report.md",
    ]),
]


def check_protocol_invariants() -> list[str]:
    """Every canonical protocol literal must appear in every document that should carry it."""
    problems = []
    for desc, literal, relpaths in PROTOCOL_INVARIANTS:
        for rel in relpaths:
            p = REPO / rel
            if not p.exists() or literal not in p.read_text(encoding="utf-8"):
                problems.append(f"{rel}: protocol invariant {desc!r} missing literal {literal!r}")
    return problems


VALIDATION_SCRIPTS = ("smoke-report.py", "workflow-check.py", "consistency-check.py")


def check_harness_permissions() -> list[str]:
    """The harness configs (opencode.json / .claude/settings.json) must allow the validation
    scripts plus the `echo exit` exit-code readback, so the README/opencode.md claims about
    them stay true. A config that only allows the echo would silently break non-interactive
    validator runs — this is the .md-to-config drift that the doc-only checks cannot catch."""
    problems = []
    cc = REPO / ".claude/settings.json"
    if not cc.exists():
        problems.append(".claude/settings.json: missing")
    else:
        text = cc.read_text(encoding="utf-8")
        for script in VALIDATION_SCRIPTS:
            if f"Bash(python scripts/{script})" not in text:
                problems.append(f".claude/settings.json: missing allow rule for scripts/{script}")
        if "echo exit" not in text:
            problems.append(".claude/settings.json: missing 'echo exit' exit-code readback rule")
    oc = REPO / "opencode.json"
    if not oc.exists():
        problems.append("opencode.json: missing")
    else:
        text = oc.read_text(encoding="utf-8")
        for script in VALIDATION_SCRIPTS:
            if f'"python scripts/{script}": "allow"' not in text:
                problems.append(f"opencode.json: missing allow pattern for scripts/{script}")
        if '"echo exit*"' not in text:
            problems.append("opencode.json: missing 'echo exit' exit-code readback pattern")
    return problems


CHECKS = [
    ("frontmatter completeness", check_frontmatter, "fail"),
    ("internal file references", check_references, "fail"),
    ("capability usage in SKILL.md", check_capability_usage, "warn"),
    ("capability-name typos across docs", check_capability_typos, "warn"),
    ("role dispatch templates", check_roles, "fail"),
    ("adapter capability mappings", check_adapter_mappings, "fail"),
    ("report phase set", check_phases, "fail"),
    ("workflow-check phase set vs template", check_workflow_phases, "fail"),
    ("reporting-protocol invariants", check_protocol_invariants, "fail"),
    ("harness config permissions for validators", check_harness_permissions, "fail"),
]


def main() -> int:
    # Windows consoles default to GBK and garble non-ASCII; force stdout to UTF-8 (ignore if unavailable)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    failed = 0
    warned = 0
    for name, fn, mode in CHECKS:
        problems = fn()
        if not problems:
            print(f"  PASS  {name}")
        elif mode == "warn":
            # Unknown capability-like identifiers are prose, not necessarily typos:
            # report as WARN, never fail the run (see check_capability_usage docstring)
            warned += 1
            print(f"  WARN  {name}")
            for msg in problems:
                print(f"        {msg}")
        else:
            failed += 1
            print(f"  FAIL  {name}")
            for msg in problems:
                print(f"        {msg}")
    print("---")
    if failed:
        print(f"{failed} check(s) failed")
        return 1
    if warned:
        print(f"all passed ({len(CHECKS)} checks, {warned} with warnings)")
    else:
        print(f"all passed ({len(CHECKS)} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
