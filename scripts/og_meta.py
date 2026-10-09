#!/usr/bin/env python3
"""Inject Open Graph + Twitter card meta into a Trench Radar report so links unfurl
with the hero image on X, Slack, Discord, iMessage, etc.

Usage: og_meta.py --reports <reports_dir> --site <https://site> YYYY-MM-DD

Rewrites both <reports_dir>/<date>/index.html and <reports_dir>/index.html (only if
the latter holds the same date). Pages are assumed to be served at <site>/trenches/. Reads the hero <img src>, the h1, and the one-liner
from the page itself, so it does not depend on the model emitting meta tags.
Idempotent: the managed block between the marker comments is replaced each run.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

REPORTS = Path(".")
SITE = ""
START, END = "<!-- og-meta:start -->", "<!-- og-meta:end -->"


def text(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", fragment))).strip()


def build_block(page: str, date: str) -> str:
    hero = re.search(r'<figure[^>]*class="[^"]*\bhero\b[^"]*"[^>]*>\s*<img[^>]*\bsrc="([^"]+)"', page)
    if not hero:
        raise SystemExit("no hero figure img found")
    src = hero.group(1)
    image = src if src.startswith("http") else SITE + src
    h1 = re.search(r"<h1\b[^>]*>(.*?)</h1>", page, re.S)
    one = re.search(r'class="[^"]*\bone-liner-text\b[^"]*"[^>]*>(.*?)</', page, re.S)
    title = "Trench Radar: " + (text(h1.group(1)) if h1 else date)
    desc = text(one.group(1)) if one else title
    url = f"{SITE}/trenches/{date}/"
    alt = re.search(r'\balt="([^"]*)"', page[hero.start():hero.end() + 300])
    e = lambda v: html.escape(v, quote=True)
    tags = [
        f'<meta name="description" content="{e(desc)}">',
        f'<meta property="og:type" content="article">',
        f'<meta property="og:site_name" content="Trench Radar">',
        f'<meta property="og:title" content="{e(title)}">',
        f'<meta property="og:description" content="{e(desc)}">',
        f'<meta property="og:url" content="{e(url)}">',
        f'<meta property="og:image" content="{e(image)}">',
        f'<meta property="og:image:alt" content="{e(alt.group(1) if alt else title)}">',
        f'<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{e(title)}">',
        f'<meta name="twitter:description" content="{e(desc)}">',
        f'<meta name="twitter:image" content="{e(image)}">',
    ]
    return "\n".join([START, *tags, END])


def apply(path: Path, date: str) -> str:
    page = path.read_text(encoding="utf-8")
    block = build_block(page, date)
    page = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\n?", "", page, flags=re.S)
    # Drop any stray og/twitter/description tags the model may have written itself.
    page = re.sub(r'<meta\s+(?:property="og:[^"]*"|name="twitter:[^"]*"|name="description")[^>]*>\n?', "", page)
    if "</head>" not in page:
        raise SystemExit(f"no </head> in {path}")
    page = page.replace("</head>", block + "\n</head>", 1)
    path.write_text(page, encoding="utf-8")
    return re.search(r'og:image" content="([^"]+)"', block).group(1)


def main() -> int:
    global REPORTS, SITE
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--reports", required=True, type=Path, help="directory served as <site>/trenches")
    ap.add_argument("--site", required=True, help="public base URL, e.g. https://reports.example.com")
    ap.add_argument("date", help="YYYY-MM-DD")
    args = ap.parse_args()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.date):
        raise SystemExit("date must be YYYY-MM-DD")
    REPORTS, SITE, date = args.reports, args.site.rstrip("/"), args.date
    dated = REPORTS / date / "index.html"
    image = apply(dated, date)
    print(f"ok {dated} og:image={image}")
    latest = REPORTS / "index.html"
    if f"/trenches/{date}" in latest.read_text(encoding="utf-8"):
        apply(latest, date)
        print(f"ok {latest}")
    else:
        print(f"skipped {latest}: not today's report")
    return 0


if __name__ == "__main__":
    sys.exit(main())
