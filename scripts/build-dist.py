#!/usr/bin/env python3
"""build-dist.py -- release packaging: build the slim, installable skill bundle.

Usage:
    python scripts/build-dist.py [--out dist] [--no-zip]

Builds the runtime surface a harness loads into <out>/harness-coding/:

    SKILL.md + references/** + the runtime scripts + LICENSE

and (by default) a release zip <out>/harness-coding-v<version>.zip, the
version read from SKILL.md frontmatter. The bundle is defined by an
ALLOWLIST, not a blocklist: dev-only files (README, CHANGELOG, design
docs, fixtures/, specs/, .claude/, opencode.json, .git*) can never leak
into a bundle even when new ones appear in the repo. build-dist.py
excludes itself -- the packager is not runtime surface.

Safety: only <out>/harness-coding/ is ever cleaned, and --out must
resolve inside the repo (and not be the repo root), so a misdirected
--out cannot destroy source. The build verifies itself: every copied
file is compared byte-identical against its source and the bundle tree
is checked for missing/extra files before the zip is written. Zip
entries use forward slashes and a fixed timestamp -- builds are
reproducible byte-for-byte.

Pure standard library; zero third-party dependencies.
Exit codes: 0 = built and verified, 1 = any failure.
"""

import argparse
import re
import shutil
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
VERSION_RE = re.compile(r"^version:\s*(\S+)", re.M)
TOP_FILES = ("SKILL.md", "LICENSE")
COPY_DIRS = ("references", "scripts")
RUNTIME_SCRIPTS = ("artifact-check.py", "derive-report.py", "find-skill.py")
SELF = "build-dist.py"             # the packager does not ship in the bundle
BUNDLE_NAME = "harness-coding"
ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)  # fixed timestamp -> reproducible zips

INSTALL_HINTS = (
    ("Claude Code", "<project>/.claude/skills/  or  ~/.claude/skills/"),
    ("opencode", "<project>/.opencode/skills/  or  ~/.config/opencode/skills/"),
    ("Codex", "<project>/.codex/skills/  or  ~/.codex/skills/"),
)


def fail(msg):
    print(f"error: {msg}", file=sys.stderr)


def read_version():
    text = (REPO / "SKILL.md").read_text(encoding="utf-8")
    m = VERSION_RE.search(text)
    if not m:
        fail("no 'version:' field in SKILL.md frontmatter")
        return None
    return m.group(1)


def collect_sources():
    """Allowlisted (relpath, src) pairs; None + message on a broken surface."""
    files = []
    for name in TOP_FILES:
        p = REPO / name
        if not p.is_file():
            fail(f"required file missing: {name}")
            return None
        files.append((Path(name), p))
    for dirname in COPY_DIRS:
        d = REPO / dirname
        if not d.is_dir():
            fail(f"required directory missing: {dirname}")
            return None
        for p in sorted(d.rglob("*")):
            if not p.is_file():
                continue
            if dirname == "scripts":
                if p.suffix != ".py" or "__pycache__" in p.parts:
                    continue
                if p.name == SELF:
                    continue
            files.append((p.relative_to(REPO), p))
    got = {p.name for _, p in files if p.parent.name == "scripts"}
    for required in RUNTIME_SCRIPTS:
        if required not in got:
            fail(f"runtime script missing from scripts/: {required}")
            return None
    return sorted(files)


def resolve_out_dir(out_arg):
    """Anchor --out inside the repo; refuse the repo root itself."""
    out_dir = Path(out_arg)
    if not out_dir.is_absolute():
        out_dir = REPO / out_dir
    out_dir = out_dir.resolve()
    if out_dir == REPO or REPO not in out_dir.parents:
        fail(f"--out must be a directory inside the repo (got '{out_arg}')")
        return None
    return out_dir


def build_bundle(out_dir, sources):
    """Copy the allowlist into <out>/harness-coding/ (only this subdir is cleaned)."""
    bundle = out_dir / BUNDLE_NAME
    if bundle.exists():
        shutil.rmtree(bundle)  # blast radius: the bundle dir only
    bundle.mkdir(parents=True)
    for rel, src in sources:
        dst = bundle / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    return bundle


def verify_bundle(bundle, sources):
    errs = []
    expected = {rel for rel, _ in sources}
    actual = {p.relative_to(bundle) for p in bundle.rglob("*") if p.is_file()}
    for rel in sorted(expected - actual):
        errs.append(f"missing from bundle: {rel}")
    for rel in sorted(actual - expected):
        errs.append(f"unexpected extra in bundle: {rel}")
    for rel, src in sources:
        if (bundle / rel).is_file() and (bundle / rel).read_bytes() != src.read_bytes():
            errs.append(f"not byte-identical to source: {rel}")
    return errs


def write_zip(out_dir, bundle, version):
    zip_path = out_dir / f"{BUNDLE_NAME}-v{version}.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for p in sorted(bundle.rglob("*")):
            if not p.is_file():
                continue
            arc = p.relative_to(bundle.parent).as_posix()
            info = zipfile.ZipInfo(arc, date_time=ZIP_EPOCH)
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, p.read_bytes())
    return zip_path


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="build the slim, installable skill bundle under dist/")
    ap.add_argument("--out", default="dist",
                    help="output directory inside the repo (default: dist)")
    ap.add_argument("--no-zip", action="store_true",
                    help="skip the release zip")
    args = ap.parse_args(argv)

    version = read_version()
    if version is None:
        return 1
    sources = collect_sources()
    if sources is None:
        return 1
    out_dir = resolve_out_dir(args.out)
    if out_dir is None:
        return 1

    bundle = build_bundle(out_dir, sources)
    errs = verify_bundle(bundle, sources)
    if errs:
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        fail("bundle verification failed")
        return 1

    total = sum(src.stat().st_size for _, src in sources)
    print(f"OK dist verified: {len(sources)} files, {total} bytes -> {bundle}")
    for rel, src in sources:
        print(f"  {rel.as_posix()}  ({src.stat().st_size} B)")

    if not args.no_zip:
        zip_path = write_zip(out_dir, bundle, version)
        print(f"OK release zip: {zip_path.name}")

    print("\ninstall: copy or link the bundle dir into a skills directory --")
    for harness, path in INSTALL_HINTS:
        print(f"  {harness}: {path}")
    print("host project: allow 'python scripts/artifact-check.py*', "
          "'python scripts/derive-report.py*' and 'python scripts/find-skill.py*' "
          "(see README)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
