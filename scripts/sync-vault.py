#!/usr/bin/env python3
"""sync-vault.py — copy the Haven Policy Vault into content/ for the Quartz build.

Applies build-target-specific transforms:
  haven (default): role placeholders substituted with names; haven-specific callouts kept; internal-only stripped.
  generic:         placeholders left intact; both haven-specific and internal-only callouts stripped.
  neo:             would use role-holders-neo.json (not yet present).

Usage:
  python3 scripts/sync-vault.py [--target haven|generic|neo] [--vault PATH] [--dry-run]
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

DEFAULT_VAULT = Path.home() / "Documents/Claude/Projects/The Haven/Haven Policy Vault"
SITE_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = SITE_ROOT / "content"
ROLE_HOLDERS = SITE_ROOT / "scripts" / "role-holders.json"

# Vault paths to exclude from sync entirely
EXCLUDE_DIRS = {"_dashboards", "_templates", "_meta", "attachments"}
# Vault root files that should not appear on the public site
EXCLUDE_ROOT_FILES = {"README.md"}
# Files anywhere in the vault that should be excluded by name
EXCLUDE_FILES = {"role-holders.md", "role-holders.DRAFT.md"}

# content/ subdirectories that are NOT sourced from the vault and must be
# preserved across sync runs. The audience/ folder holds curated MOC pages
# (commissioner pack, families, staff, DSL) that link into policies/. They
# live alongside the vault output but aren't generated from it.
PRESERVE_DIRS = {"audience"}

# Frontmatter status values that should NOT be published
EXCLUDE_STATUSES = {"draft", "archived", "superseded", "needs-remediation", "resolved"}


def load_role_holders(target: str) -> dict:
    if target == "generic":
        return {"roles": {}, "emails": {}, "urls": {}}
    role_file = ROLE_HOLDERS
    if target == "neo":
        role_file = SITE_ROOT / "scripts" / "role-holders-neo.json"
    if not role_file.exists():
        sys.exit(f"Role-holders file not found: {role_file}")
    with role_file.open() as f:
        return json.load(f)


def parse_frontmatter(text: str):
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not m:
        return {}, text
    fm_text = m.group(1)
    body = m.group(2)
    fm = {}
    for line in fm_text.split("\n"):
        kv = re.match(r'^([a-zA-Z_]+):\s*(.*)$', line)
        if kv:
            k, v = kv.group(1), kv.group(2).strip()
            v = v.strip('"').strip("'")
            fm[k] = v
    return fm, body


def strip_callout(body: str, callout_type: str) -> str:
    """Strip a callout block of the named type, including all > -prefixed lines."""
    lines = body.split("\n")
    out = []
    in_callout = False
    pattern_open = re.compile(rf">\s*\[!{re.escape(callout_type)}\]")
    for line in lines:
        if pattern_open.search(line):
            in_callout = True
            continue
        if in_callout:
            if line.startswith(">"):
                continue
            in_callout = False
        out.append(line)
    # Collapse multiple blank lines that may result
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out))


def apply_substitutions(text: str, holders: dict) -> str:
    for placeholder, value in holders.get("roles", {}).items():
        text = text.replace(placeholder, value)
    for placeholder, value in holders.get("emails", {}).items():
        text = text.replace(placeholder, value)
    for placeholder, value in holders.get("urls", {}).items():
        text = text.replace(placeholder, value)
    return text


def should_publish(fm: dict) -> bool:
    """Decide whether a policy is published based on its frontmatter."""
    if fm.get("publish", "").lower() == "false":
        return False
    status = fm.get("status", "").lower()
    if status in EXCLUDE_STATUSES:
        return False
    # Default: publish only if status is live (or empty / unset)
    return status in {"live", ""}


def sync_one(src: Path, dst: Path, holders: dict, target: str, dry_run: bool):
    text = src.read_text(encoding="utf-8")
    fm, _ = parse_frontmatter(text)

    if not should_publish(fm):
        return None  # excluded from public build

    # Strip internal-only callouts (always)
    text = strip_callout(text, "internal-only")

    # For generic builds, also strip haven-specific callouts
    if target == "generic":
        text = strip_callout(text, "haven-specific")

    # Apply role/email/URL substitutions
    text = apply_substitutions(text, holders)

    if dry_run:
        return f"[would write] {dst}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    return f"wrote {dst.relative_to(CONTENT_DIR)}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="haven", choices=["haven", "generic", "neo"])
    ap.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.vault.exists():
        sys.exit(f"Vault not found at {args.vault}")

    holders = load_role_holders(args.target)

    # Clear existing content/, preserving directories listed in PRESERVE_DIRS
    # (e.g. audience/ — curated MOC pages that aren't sourced from the vault).
    if CONTENT_DIR.exists() and not args.dry_run:
        for child in CONTENT_DIR.iterdir():
            if child.is_dir():
                if child.name in PRESERVE_DIRS:
                    continue
                shutil.rmtree(child)
            else:
                child.unlink()

    # Walk vault, copy with transforms
    n_published = 0
    n_excluded = 0
    for src in args.vault.rglob("*.md"):
        rel = src.relative_to(args.vault)
        # Exclusion checks
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        if rel.name in EXCLUDE_FILES:
            continue
        # Vault root README — replaced by generated index.md
        if len(rel.parts) == 1 and rel.name in EXCLUDE_ROOT_FILES:
            continue

        dst = CONTENT_DIR / rel
        result = sync_one(src, dst, holders, args.target, args.dry_run)
        if result is None:
            n_excluded += 1
        else:
            n_published += 1

    # Index page
    index_path = CONTENT_DIR / "index.md"
    if not args.dry_run:
        index_path.write_text(_index_md(args.target), encoding="utf-8")

    print(f"\nTarget:    {args.target}")
    print(f"Published: {n_published}")
    print(f"Excluded:  {n_excluded} (status not 'live' or in excluded folders/files)")


def _index_md(target: str) -> str:
    """Emit the homepage. Layout: audience cards first, theme browse second.

    Audience cards link to content/audience/<page>.md files (preserved across
    sync runs by PRESERVE_DIRS). Theme browse links to /policies/<theme>/
    folder pages that Quartz auto-generates.
    """
    return f"""---
title: "The Haven — Policy Index"
cssclasses:
  - landing
---

# Welcome to The Haven's policy site

This site publishes The Haven's policies in full. The Haven is owned and operated by the [Autistic Girls Network](https://autisticgirlsnetwork.org/) charity. The Haven's main site is at [thehavenonline.school](https://thehavenonline.school/).

## Quick start by audience

<ul class="audience-grid">
  <li><a href="audience/commissioners-and-schools">
    <span class="audience-card-title">For Commissioners and Schools</span>
    <span class="audience-card-desc">The policies and procurement documents Local Authority and school commissioners typically need.</span>
  </a></li>
  <li><a href="audience/families">
    <span class="audience-card-title">For Families</span>
    <span class="audience-card-desc">Parent- and carer-facing policies, the family attendance agreement, and the digital age of consent guide.</span>
  </a></li>
  <li><a href="audience/staff-and-volunteers">
    <span class="audience-card-title">For Haven Staff and Volunteers</span>
    <span class="audience-card-desc">Induction reading and the annual sign-off set for everyone working at or for The Haven.</span>
  </a></li>
  <li><a href="audience/dsl">
    <span class="audience-card-title">For the Designated Safeguarding Lead</span>
    <span class="audience-card-desc">The full safeguarding-relevant set, with statutory references and information sharing routes.</span>
  </a></li>
</ul>

## Browse by theme

<ul class="theme-list">
  <li><a href="policies/safeguarding/">Safeguarding</a><span class="theme-desc">Child protection, online safety, Prevent, child-on-child abuse, RSHE, drugs and alcohol, safer recruitment, managing allegations.</span></li>
  <li><a href="policies/health-safety-medical/">Health, safety and medical</a><span class="theme-desc">First aid, risk assessment, lone working, medical conditions, off-site visits, transport, business continuity.</span></li>
  <li><a href="policies/data-digital-ai/">Data, digital and AI</a><span class="theme-desc">Data protection, privacy, cyber security, BYOD, the Responsible Use of AI Policy.</span></li>
  <li><a href="policies/hr-staff-conduct/">HR and staff conduct</a><span class="theme-desc">Staff conduct, grievance and disciplinary, whistleblowing, ex-offenders, internet agreement.</span></li>
  <li><a href="policies/equality-inclusion-send/">Equality, inclusion and SEND</a><span class="theme-desc">Anti-racism, equal opportunities, SEND.</span></li>
  <li><a href="policies/governance-legal/">Governance and legal</a><span class="theme-desc">Statement of purpose, terms and conditions, complaints, governance structure, governor responsibilities.</span></li>
  <li><a href="policies/behaviour-regulation/">Behaviour and regulation</a><span class="theme-desc">The Relational Behaviour and Regulation Policy.</span></li>
  <li><a href="policies/curriculum-teaching-quality/">Curriculum, teaching and quality</a><span class="theme-desc">Teaching and learning, examinations, quality assurance.</span></li>
  <li><a href="policies/attendance-engagement/">Attendance and engagement</a><span class="theme-desc">Attendance, children missing from education, family attendance agreement, withdrawal.</span></li>
  <li><a href="policies/admissions-referrals/">Admissions and referrals</a><span class="theme-desc">Referrals and admissions.</span></li>
  <li><a href="policies/parent-family-guidance/">Parent and family guidance</a><span class="theme-desc">Digital Age of Consent guide for parents.</span></li>
</ul>

---

Build target: `{target}`. Last refresh: 29 April 2026.
"""


if __name__ == "__main__":
    main()
