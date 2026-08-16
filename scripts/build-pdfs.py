#!/usr/bin/env python3
"""build-pdfs.py — render every published Haven policy as a styled PDF.

Runs in CI (GitHub Actions) as part of the deploy pipeline; can also be run
locally anywhere Python + WeasyPrint are available.

Two phases (run separately because the library page must exist BEFORE the
Quartz build, while the PDFs land in public/ AFTER it):

  python3 scripts/build-pdfs.py --page          # writes content/pdf-library.md
  python3 scripts/build-pdfs.py --pdfs          # writes public/pdf/** + the all-policies zip

Options:
  --content DIR   content directory (default: <site>/content)
  --out DIR       output directory for --pdfs (default: <site>/public/pdf)

Styling follows the Haven house style (masthead maroon #7A3B4F, plum #3D2B33)
so the PDFs match the formal Word documents. Roles, never names, appear in the
metadata — exactly as in the vault frontmatter.

Dependencies: weasyprint, markdown, pyyaml
  (CI installs: libpango-1.0-0 libpangoft2-1.0-0 fonts-crosextra-carlito)
"""

import argparse
import datetime
import re
import sys
import zipfile
from pathlib import Path

import markdown
import yaml

SITE_ROOT = Path(__file__).resolve().parent.parent
CHARITY_LINE = "Operated by the Autistic Girls Network charity — 1196655 (England and Wales), SC054837 (Scotland)"
SITE_URL = "policies.thehavenonline.school"
ZIP_NAME = "haven-policies-all.zip"

MAROON = "#7A3B4F"
PLUM = "#3D2B33"
GREY = "#555555"
SHADE = "#F2EEF0"

CSS = """
@page {
  size: A4;
  margin: 2.2cm 2cm 2.4cm 2cm;
  @bottom-left { content: "The Haven \\2014  MAROON_URL"; font-size: 8pt; color: #555555; font-family: Carlito, Calibri, 'DejaVu Sans', sans-serif; }
  @bottom-right { content: "Page " counter(page) " of " counter(pages); font-size: 8pt; color: #555555; font-family: Carlito, Calibri, 'DejaVu Sans', sans-serif; }
}
html { font-family: Carlito, Calibri, 'DejaVu Sans', sans-serif; font-size: 10.5pt; color: #000; }
body { line-height: 1.45; }
.masthead { text-align: center; font-size: 24pt; font-weight: bold; color: MAROON; letter-spacing: 0.08em; margin-bottom: 2pt; }
.strapline { text-align: center; font-style: italic; font-size: 10pt; color: #555555; margin: 0 0 18pt 0; }
h1.doc-title { text-align: center; font-size: 19pt; font-weight: bold; color: #000; margin: 0 0 4pt 0; }
.doc-subtitle { text-align: center; font-size: 12pt; color: PLUM; margin: 0 0 16pt 0; }
table.meta { width: 100%; border-collapse: collapse; margin: 0 0 20pt 0; font-size: 9.5pt; }
table.meta td { border: 0.5pt solid #000; padding: 4pt 7pt; }
table.meta td.k { background: SHADE; font-weight: bold; width: 32%; }
h1 { font-size: 14.5pt; font-weight: bold; color: MAROON; margin: 16pt 0 6pt 0; page-break-after: avoid; }
h2 { font-size: 12.5pt; font-weight: bold; color: PLUM; margin: 13pt 0 5pt 0; page-break-after: avoid; }
h3 { font-size: 11pt; font-weight: bold; color: #000; margin: 11pt 0 4pt 0; page-break-after: avoid; }
p, li { margin: 0 0 6pt 0; }
ul, ol { margin: 0 0 8pt 0; padding-left: 1.4em; }
table { border-collapse: collapse; margin: 8pt 0 12pt 0; font-size: 9.5pt; width: 100%; }
th { background: MAROON; color: #fff; font-weight: bold; border: 0.5pt solid #000; padding: 4pt 6pt; text-align: left; }
td { border: 0.5pt solid #000; padding: 4pt 6pt; vertical-align: top; }
tr, img { page-break-inside: avoid; }
blockquote { margin: 8pt 0; padding: 6pt 10pt; border-left: 3pt solid MAROON; background: SHADE; }
blockquote p { margin: 0 0 4pt 0; }
.callout { margin: 8pt 0; padding: 7pt 10pt; border-left: 3pt solid MAROON; background: SHADE; }
.callout .callout-title { font-weight: bold; color: MAROON; margin-bottom: 3pt; }
code { font-family: 'DejaVu Sans Mono', monospace; font-size: 9pt; background: #f5f5f5; padding: 0 2pt; }
a { color: PLUM; text-decoration: none; }
hr { border: none; border-top: 0.5pt solid #999; margin: 12pt 0; }
.provenance { font-size: 8.5pt; color: #555555; font-style: italic; margin-top: 22pt; border-top: 0.5pt solid #999; padding-top: 6pt; }
""".replace("MAROON_URL", SITE_URL).replace("MAROON", MAROON).replace("PLUM", PLUM).replace("SHADE", SHADE)

CALLOUT_RE = re.compile(r"^> \[!(\w+)\][+-]?\s*(.*)$")
TITLE_VERSION_RE = re.compile(r"\s+v\.?\d{2}\.\d{2}\s*$")


def display_title(title: str) -> str:
    """Some vault titles embed the version ("Quality Assurance Policy v01.26");
    strip it for display — the version is shown separately."""
    return TITLE_VERSION_RE.sub("", title or "")
WIKILINK_RE = re.compile(r"\[\[([^\]|]+)\|([^\]]+)\]\]|\[\[([^\]]+)\]\]")


def parse_frontmatter(text: str):
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?", text, re.S)
    if not m:
        return {}, text
    body = text[m.end():]
    try:
        fm = yaml.safe_load(m.group(1)) or {}
        if not isinstance(fm, dict):
            fm = {}
    except yaml.YAMLError:
        fm = {}
        for line in m.group(1).splitlines():
            km = re.match(r"^(\w+):\s*(.+?)\s*$", line)
            if km:
                fm[km.group(1)] = km.group(2).strip('"')
    return fm, body


def transform_body(body: str, title: str) -> str:
    """Markdown-level cleanups before conversion."""
    # Wikilinks -> plain text
    body = WIKILINK_RE.sub(lambda m: m.group(2) or m.group(3), body)
    lines = body.splitlines()
    out = []
    i = 0
    dropped_title = False
    dropped_status_callout = False
    while i < len(lines):
        line = lines[i]
        # Drop the first H1 (repeated in the PDF title block)
        if not dropped_title and re.match(r"^#\s+", line):
            dropped_title = True
            i += 1
            continue
        cm = CALLOUT_RE.match(line)
        if cm:
            # Collect the whole callout block
            block = []
            j = i + 1
            while j < len(lines) and lines[j].startswith(">"):
                block.append(lines[j][1:].lstrip())
                j += 1
            # Drop the standard status callout (duplicated by the metadata table)
            if not dropped_status_callout and cm.group(1).lower() == "info" and any(
                "**Status:**" in b for b in block
            ):
                dropped_status_callout = True
                i = j
                continue
            ctype = cm.group(1).capitalize()
            ctitle = cm.group(2).strip() or ctype
            inner = markdown.markdown("\n".join(block), extensions=["tables", "sane_lists"])
            out.append(
                f'<div class="callout"><div class="callout-title">{ctitle}</div>{inner}</div>'
            )
            i = j
            continue
        out.append(line)
        i += 1
    return "\n".join(out)


def esc(s) -> str:
    return (
        str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if s is not None
        else ""
    )


def fmt_date(v) -> str:
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.strftime("%d %B %Y")
    return esc(v) if v else "—"


def render_html(fm: dict, body_md: str, generated: str) -> str:
    title = display_title(fm.get("title") or "Untitled policy")
    meta_rows = [
        ("Document", title),
        ("Version", fm.get("version", "—")),
        ("Status", fm.get("status", "—")),
        ("Last reviewed", fmt_date(fm.get("last_reviewed"))),
        ("Next review", fmt_date(fm.get("next_review"))),
        ("Owner", fm.get("owner_role", "—")),
        ("Approved by", fm.get("approver_role", "—")),
    ]
    rows = "".join(
        f'<tr><td class="k">{esc(k)}</td><td>{esc(v)}</td></tr>' for k, v in meta_rows
    )
    subtitle = fm.get("subtitle")
    sub_html = f'<p class="doc-subtitle">{esc(subtitle)}</p>' if subtitle else ""
    body_html = markdown.markdown(
        transform_body(body_md, title), extensions=["tables", "sane_lists"]
    )
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="masthead">THE HAVEN</div>
<p class="strapline">{esc(CHARITY_LINE)}</p>
<h1 class="doc-title">{esc(title)}</h1>
{sub_html}
<table class="meta">{rows}</table>
{body_html}
<p class="provenance">This PDF was generated from the published policy at {SITE_URL} on {generated}.
The website is the authoritative, most current version of this policy.</p>
</body></html>"""


def pdf_name(md_path: Path) -> str:
    stem = md_path.stem
    stem = stem.replace("&", "and").replace("—", "-").replace("–", "-")
    stem = re.sub(r"[^A-Za-z0-9.()\-]+", "-", stem).strip("-")
    stem = re.sub(r"-{2,}", "-", stem)
    return stem + ".pdf"


def collect(content_dir: Path):
    """Yield (md_path, category, frontmatter, body) for every published policy."""
    for p in sorted((content_dir / "policies").rglob("*.md")):
        fm, body = parse_frontmatter(p.read_text(encoding="utf-8"))
        if str(fm.get("status", "live")).strip() != "live":
            continue  # belt and braces; sync only publishes live
        category = p.relative_to(content_dir / "policies").parts[0]
        yield p, category, fm, body


def build_pdfs(content_dir: Path, out_dir: Path):
    from weasyprint import HTML  # imported late: --page must not need it

    generated = datetime.date.today().strftime("%d %B %Y")
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    failures = []
    for p, category, fm, body in collect(content_dir):
        target = out_dir / category / pdf_name(p)
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            html = render_html(fm, body, generated)
            HTML(string=html).write_pdf(str(target))
            written.append(target)
            print(f"  ok  {target.relative_to(out_dir)}")
        except Exception as e:  # keep going; report at the end
            failures.append((p.name, str(e)))
            print(f"  FAIL {p.name}: {e}", file=sys.stderr)
    # Zip of everything, stable name so the library page can link it
    zip_path = out_dir / ZIP_NAME
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in written:
            z.write(f, arcname=str(f.relative_to(out_dir)))
    print(f"\n{len(written)} PDFs written to {out_dir}; zip: {zip_path.name}")
    if failures:
        print(f"{len(failures)} FAILED: {[f[0] for f in failures]}", file=sys.stderr)
        sys.exit(1)


def build_page(content_dir: Path):
    """Write content/pdf-library.md — the download page, grouped by category,
    regenerated on every CI run so it stays in lockstep with the vault."""
    cats = {}
    for p, category, fm, _ in collect(content_dir):
        cats.setdefault(category, []).append(
            (display_title(fm.get("title") or p.stem), fm.get("version", ""), category, pdf_name(p))
        )

    def cat_label(c):
        return {
            "safeguarding": "Safeguarding",
            "attendance-engagement": "Attendance and engagement",
            "behaviour-regulation": "Behaviour and regulation",
            "health-safety-medical": "Health, safety and medical",
            "data-digital-ai": "Data, digital and AI",
            "hr-staff-conduct": "HR and staff conduct",
            "equality-inclusion-send": "Equality, inclusion and SEND",
            "governance-legal": "Governance and legal",
            "curriculum-teaching-quality": "Curriculum, teaching and quality",
            "admissions-referrals": "Admissions and referrals",
            "parent-family-guidance": "Parent and family guidance",
        }.get(c, c)

    lines = [
        "---",
        'title: "Download policies as PDF"',
        "---",
        "",
        "Every published Haven policy is available here as a PDF, regenerated automatically whenever the policy library is updated. These are provided for Local Authority framework applications, commissioning paperwork, and anywhere else an attached document is needed. The website remains the authoritative, most current version of every policy.",
        "",
        f"**[Download all policies as a single zip](/pdf/{ZIP_NAME})**",
        "",
    ]
    total = 0
    for c in sorted(cats, key=cat_label):
        lines.append(f"## {cat_label(c)}")
        lines.append("")
        for title, version, category, name in sorted(cats[c], key=lambda e: e[0].lower()):
            v = f" (v{version})" if version and version != "unversioned" else ""
            lines.append(f"- [{title}{v}](/pdf/{category}/{name})")
            total += 1
        lines.append("")
    lines.append(f"*{total} policies. PDFs are generated from the live policy pages at every site deploy.*")
    lines.append("")
    out = content_dir / "pdf-library.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out} ({total} entries)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", action="store_true", help="write content/pdf-library.md")
    ap.add_argument("--pdfs", action="store_true", help="render PDFs + zip")
    ap.add_argument("--content", type=Path, default=SITE_ROOT / "content")
    ap.add_argument("--out", type=Path, default=SITE_ROOT / "public" / "pdf")
    args = ap.parse_args()
    if not (args.page or args.pdfs):
        ap.error("choose --page and/or --pdfs")
    if args.page:
        build_page(args.content)
    if args.pdfs:
        build_pdfs(args.content, args.out)


if __name__ == "__main__":
    main()
