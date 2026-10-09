#!/usr/bin/env python3
"""Generate the Trench Radar hero image through any OpenAI-compatible images API.

Usage: hero_image.py YYYY-MM-DD "<image prompt>"

Environment:
  IMAGE_API_KEY    required
  IMAGE_API_BASE   default https://api.openai.com/v1 (any /images/generations-compatible base)
  IMAGE_MODELS     comma-separated models to try in order, default gpt-image-1
  REPORTS_DIR      directory served as <SITE_URL>/trenches (images go in REPORTS_DIR/images)
  SITE_URL         public base URL, e.g. https://reports.example.com

Writes REPORTS_DIR/images/<date>-<HHMMSS UTC>.jpg (a fresh filename every run so CDN and
browser caches never show an older same-day image), normalized to exactly 16:9, and prints
only its public URL on stdout. Diagnostics go to stderr. Exit 1 if every model failed.

Snapshot note: our production version also picks the cheapest model in a quality tier from
live provider prices and falls back to a second provider. That part is specific to our
setup; the model order list below is the portable version of it.
"""

from __future__ import annotations

import base64
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

SIZE = "1536x1024"  # ask for landscape; output is normalized to 16:9 regardless
TIMEOUT_S = 180


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def generate(base: str, key: str, model: str, prompt: str) -> bytes:
    body = json.dumps({"model": model, "prompt": prompt, "n": 1, "size": SIZE}).encode()
    req = urllib.request.Request(
        base.rstrip("/") + "/images/generations", data=body, method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": "trench-hero/1"},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as res:
        item = json.loads(res.read())["data"][0]
    if item.get("b64_json"):
        return base64.b64decode(item["b64_json"])
    with urllib.request.urlopen(urllib.request.Request(item["url"], headers={"User-Agent": "trench-hero/1"}), timeout=60) as res:
        return res.read()


def normalize_16x9(img: Image.Image) -> Image.Image:
    """Center-crop anything wider than 16:9; pad anything narrower with the background color.

    The page CSS crops to 16:9 anyway, but the raw file is also the og:image, and Slack
    mobile breaks image cards wider than 16:9. Some models ignore the requested size and
    return squares, which get padded rather than cropped so no panel is cut off.
    """
    w, h = img.size
    target_w = round(h * 16 / 9)
    if w > target_w:
        x0 = (w - target_w) // 2
        return img.crop((x0, 0, x0 + target_w, h))
    if w < target_w:
        corners = [img.getpixel(p) for p in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1))]
        bg = tuple(sorted(c[i] for c in corners)[1] for i in range(3))
        canvas = Image.new("RGB", (target_w, h), bg)
        canvas.paste(img, ((target_w - w) // 2, 0))
        return canvas
    return img


def main() -> int:
    if len(sys.argv) != 3 or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", sys.argv[1]):
        raise SystemExit("usage: hero_image.py YYYY-MM-DD PROMPT")
    date, prompt = sys.argv[1], sys.argv[2]
    key = os.environ.get("IMAGE_API_KEY") or sys.exit("IMAGE_API_KEY is not set")
    base = os.environ.get("IMAGE_API_BASE", "https://api.openai.com/v1")
    models = [m.strip() for m in os.environ.get("IMAGE_MODELS", "gpt-image-1").split(",") if m.strip()]
    reports = Path(os.environ.get("REPORTS_DIR") or sys.exit("REPORTS_DIR is not set"))
    site = (os.environ.get("SITE_URL") or sys.exit("SITE_URL is not set")).rstrip("/")

    dest = reports / "images" / f"{date}-{datetime.now(timezone.utc):%H%M%S}.jpg"
    for model in models:
        try:
            raw = generate(base, key, model, prompt)
            img = normalize_16x9(Image.open(io.BytesIO(raw)).convert("RGB"))
        except urllib.error.HTTPError as exc:
            log(f"{model}: HTTP {exc.code} {exc.read()[:200].decode(errors='replace')}")
            continue
        except Exception as exc:  # timeouts, bad payloads, undecodable images
            log(f"{model}: {exc}")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(".tmp.jpg")
        img.save(tmp, "JPEG", quality=88, optimize=True)
        tmp.chmod(0o644)
        tmp.replace(dest)
        log(f"{model}: ok {img.size[0]}x{img.size[1]} -> {dest}")
        print(f"{site}/trenches/images/{dest.name}")
        return 0
    log("every model failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
