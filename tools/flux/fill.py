#!/usr/bin/env python3
"""fill.py — add to an existing image WITHOUT re-synthesizing it.

WHY THIS EXISTS. `draw.py --image` edits through `flux-2-pro`, which has no mask: every edit
re-synthesizes the WHOLE frame, so elements drift a little each pass — a named thing moves, a faint
abstract thing erodes. That is fine for a first render and bad for "add my mark and leave everyone
else's alone". `/v1/flux-pro-1.0-fill` takes an image plus a mask and regenerates **only the white
area**, so everything outside the mask is preserved pixel-for-pixel. That is the right tool for
appending to the banner.

    python3 tools/flux/fill.py --image banner/<current>.png --out banner/<new>.png \
        --prompt "a small arched stone bridge over a still water channel" \
        --band 430 --protect-left 320

The mask is generated, so there is no image editor in the loop. White = regenerate, black = keep.

  --band N          regenerate everything below row N (default 430). Lower N = a taller band.
  --protect-left W  keep the left W columns below the band black too (default 320), so a subject
                    that sits there (the porch and the dalmatian) is untouched.
  --no-corner       also keep the bottom-right corner black. FLUX.1 Fill tends to invent a faint
                    signature there; this leaves the original pixels instead.
  --band N --protect-left W are a guess per edit; render a draft, look at it, and adjust.

KNOWN SEAM, said plainly: FLUX.1 Fill is an older model than flux-2-pro, so the *generated* region
can differ subtly in style from the rest. Its virtue is that the difference is confined to the mask.

BY DEFAULT IT REFUSES to overwrite an existing `--out`. That is on purpose: a new revision is a new
dated file, and overwriting the old one hides history from anyone reading the shelf (banner revision C
was clobbered four times under one filename). Pass `--force` when you mean to overwrite in place.

Costs the same few cents as any render on the BFL account. Nothing retries on its own.
"""
import argparse
import base64
import json
import struct
import sys
import time
import urllib.request
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
from flux_token import resolve_flux_token  # noqa: E402

API = "https://api.bfl.ai/v1/flux-pro-1.0-fill"


def png_gray(w, h, fn):
    """A minimal 8-bit greyscale PNG from a pixel function. No PIL dependency."""
    raw = bytearray()
    for y in range(h):
        raw.append(0)  # filter type 0
        raw += bytes(fn(x, y) for x in range(w))
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 0, 0, 0, 0))
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))


def image_size(path):
    """Width/height for a PNG or JPEG. BFL returns JPEG bytes even named .png, so handle both."""
    with open(path, "rb") as f:
        b = f.read()
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", b[16:24])
    if b[:2] == b"\xff\xd8":                       # JPEG: walk the markers to the SOF
        i = 2
        while i < len(b) - 9:
            if b[i] != 0xFF:
                i += 1
                continue
            marker = b[i + 1]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                          0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                h, w = struct.unpack(">HH", b[i + 5:i + 9])
                return w, h
            if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                i += 2
            else:
                i += 2 + struct.unpack(">H", b[i + 2:i + 4])[0]
    raise SystemExit("couldn't read image dimensions (need PNG or JPEG)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--image", required=True, help="the image to add to (PNG)")
    ap.add_argument("--out", required=True, help="where to write the result (must differ from --image)")
    ap.add_argument("--prompt", required=True, help="describe ONLY the added region")
    ap.add_argument("--band", type=int, default=430, help="regenerate everything below this row")
    ap.add_argument("--protect-left", type=int, default=320, help="keep the left W cols below the band")
    ap.add_argument("--no-corner", action="store_true", help="keep the bottom-right corner black")
    ap.add_argument("--rect", action="append", default=[], metavar="X0,Y0,X1,Y1",
                    help="regenerate ONLY this rectangle (repeatable; union). When given, --band, "
                         "--protect-left and --no-corner are ignored. For a small addition that must "
                         "not touch anything else, e.g. a mark beside another participant's mark")
    ap.add_argument("--mask-only", action="store_true",
                    help="write <out>.mask.png and exit without sending anything. Look at the mask "
                         "before you spend a render")
    ap.add_argument("--steps", type=int, default=40)
    ap.add_argument("--guidance", type=float, default=40)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--force", action="store_true",
                    help="overwrite an existing --out. Default is to refuse, because on the banner a "
                         "new revision is a NEW dated file and overwriting hides the history")
    a = ap.parse_args()

    if Path(a.image).resolve() == Path(a.out).resolve():
        raise SystemExit("--out must differ from --image to preserve the original")
    if Path(a.out).exists() and not a.force:
        raise SystemExit(
            f"{a.out} already exists. On this repo a new revision is a new dated file; overwriting an\n"
            f"existing one hides the history (banner revision C was clobbered four times this way).\n"
            f"Either pick a new --out, or pass --force to overwrite in place on purpose.")

    w, h = image_size(a.image)
    band, prot, corner = a.band, a.protect_left, a.no_corner

    rects = []
    for r in a.rect:
        try:
            x0, y0, x1, y1 = (int(v) for v in r.split(","))
        except ValueError:
            raise SystemExit(f"--rect wants X0,Y0,X1,Y1 integers, got {r!r}")
        if not (0 <= x0 < x1 <= w and 0 <= y0 < y1 <= h):
            raise SystemExit(f"--rect {r} is outside the {w}x{h} image or empty")
        rects.append((x0, y0, x1, y1))

    def m(x, y):
        if rects:
            return 255 if any(x0 <= x < x1 and y0 <= y < y1 for x0, y0, x1, y1 in rects) else 0
        if y < band:
            return 0
        if x < prot:
            return 0
        if corner and x > w - 386 and y > h - 42:
            return 0
        return 255

    mask = png_gray(w, h, m)
    Path(a.out + ".mask.png").write_bytes(mask)
    if a.mask_only:
        print("mask written to", a.out + ".mask.png", "— nothing sent, nothing charged")
        return

    key, source = resolve_flux_token(str(ROOT))
    if not key:
        raise SystemExit("no FLUX token (env, .env, or SSM) — nothing sent, nothing charged")
    print("flux token: using", source)

    payload = {
        "image": base64.b64encode(Path(a.image).read_bytes()).decode(),
        "mask": base64.b64encode(mask).decode(),
        "prompt": a.prompt, "steps": a.steps, "guidance": a.guidance,
        "output_format": "png",
    }
    if a.seed is not None:
        payload["seed"] = a.seed

    req = urllib.request.Request(API, data=json.dumps(payload).encode(),
                                 headers={"x-key": key, "Content-Type": "application/json"})
    job = json.loads(urllib.request.urlopen(req, timeout=90).read())
    for _ in range(120):
        time.sleep(2)
        r = urllib.request.Request(job["polling_url"], headers={"x-key": key})
        s = json.loads(urllib.request.urlopen(r, timeout=90).read())
        st = s.get("status")
        if st == "Ready":
            Path(a.out).write_bytes(urllib.request.urlopen(s["result"]["sample"], timeout=120).read())
            print(str(Path(a.out).resolve()))
            return
        if st not in ("Pending", "Processing", "Queued", "Request Moderated"):
            raise SystemExit(f"status {st}: {json.dumps(s)[:400]}")
    raise SystemExit("timed out")


if __name__ == "__main__":
    main()
