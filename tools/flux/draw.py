#!/usr/bin/env python3
"""Make an image from a prompt you type, without writing a file first.

HER ASK, 28 October 2026: "could you make a quick tool i can run locally that will accept an image
prompt and produce a flux image? or do you already use a tool like that and if so can you make a
readme so i can use it to? ive been meaning to make some flux images for other shit and im tired of
using grok tbh haha."

THE ANSWER TO THE FIRST HALF IS YES, IT ALREADY EXISTED. generate.py has been here since 23 October
and it is what drew the Grove banner. What it did not have was a way in: it takes a path to a prompt
file and four positional arguments in an order nobody remembers, which is a tool for whoever wrote
it. This is the front door.

    python3 tools/flux/draw.py "a dalmatian whose spots are constellations, on a dark porch"
    python3 tools/flux/draw.py "..." --size banner --out content/branding/thing.png
    python3 tools/flux/draw.py --file content/branding/the-grove-banner-prompt.txt --size banner

It prints the path when it is done and opens the image, because a tool that silently writes a file
somewhere is a tool you have to go looking for.

COSTS REAL MONEY, a few cents a render on her BFL account. Nothing here retries on its own.
"""
import argparse
import datetime
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import generate  # noqa: E402

# Named shapes, because remembering that both numbers must be multiples of 32 is exactly the kind of
# thing that makes somebody not bother. Every one of these is already a multiple of 32.
SIZES = {
    "banner":  (1536, 640),    # README and page headers
    "wide":    (1440, 960),    # 3:2, general illustration
    "square":  (1024, 1024),   # avatars, social, cards
    "tall":    (896, 1344),    # 2:3, posters and phone wallpapers
    "card":    (1200, 630),    # link previews and open graph
}

# Image models put invented words into pictures unprompted, and garbled fake text makes anything
# unusable. Every prompt gets this unless --allow-text is passed.
NO_TEXT = (" Absolutely no text, no words, no letters, no signage and no numbers anywhere in the"
           " image.")

from pathlib import Path

def validate_output_path(value: str) -> Path:
    out = Path(value).expanduser()

    if out.is_dir():
        raise ValueError(
            f"'{out}' is a directory. Specify an output filename."
        )

    if not out.parent.is_dir():
        raise ValueError(
            f"Output directory '{out.parent}' does not exist."
        )

    return out

def slug(text):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (s[:48] or "image").rstrip("-")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("prompt", nargs="?", help="the prompt, in quotes")
    ap.add_argument("--file", help="read the prompt from this file instead")
    ap.add_argument("--size", default="wide", choices=sorted(SIZES),
                    help="banner, wide, square, tall or card. Default wide")
    ap.add_argument("--out", help="where to write it. Defaults to a dated name in this directory")
    ap.add_argument("--image", help="existing PNG/JPEG/WebP to EDIT. When set, make the prompt a SHORT instruction describing only your change (not a full scene) or the model redraws everything")
    ap.add_argument("--allow-text", action="store_true",
                    help="let the model draw words. It will do it badly")
    ap.add_argument("--seed", type=int, default=None,
                    help="fix the random seed for a reproducible / comparable render")
    ap.add_argument("--upsample", action="store_true",
                    help="re-enable BFL prompt-upsampling. Default OFF for edits (--image) so your "
                         "exact words (esp. 'keep element X') are obeyed; default ON for fresh draws")
    ap.add_argument("--no-open", action="store_true", help="do not open it when it is done")
    a = ap.parse_args()

    if a.file:
        with open(a.file, encoding="utf-8") as f:
            prompt = f.read().strip()
    elif a.prompt:
        prompt = a.prompt.strip()
    else:
        raise SystemExit("give me a prompt in quotes, or --file pointing at one")
    if not prompt:
        raise SystemExit("the prompt is empty, so nothing was sent and nothing was charged")

    input_image = None
    if a.image:
        image_path = Path(a.image).expanduser()
        if not image_path.is_file():
            ap.error(f"input image '{image_path}' is not a readable file")
        try:
            with image_path.open("rb") as image_file:
                signature = image_file.read(12)
        except OSError as exc:
            ap.error(f"cannot read input image '{image_path}': {exc}")
        supported = (signature.startswith(b"\x89PNG\r\n\x1a\n") or
                     signature.startswith(b"\xff\xd8\xff") or
                     (signature[:4] == b"RIFF" and signature[8:12] == b"WEBP"))
        if not supported:
            ap.error("--image must be a PNG, JPEG, or WebP image")
        input_image = str(image_path)

    if not a.allow_text and "no text" not in prompt.lower():
        prompt = prompt.rstrip(". ") + "." + NO_TEXT

    from flux_token import resolve_flux_token  # local module, tools/flux/flux_token.py
    key, source = resolve_flux_token(ROOT)
    if not key:
        raise SystemExit(
            "no CORRIE_BFL_FLUX_TOKEN found. Checked: env var, %s, and SSM. Nothing was sent.\n"
            "On the box it lives in .env; off the box put it in SSM (/auran/flux/token) — "
            "see tools/flux/README.md." % os.path.join(ROOT, ".env"))
    if source != ".env":
        print("flux token: using %s" % source)

    w, h = SIZES[a.size]
    out = a.out or os.path.join(HERE, "%s-%s.png"
                                % (datetime.date.today().strftime("%Y%m%d"), slug(prompt)))
    d = os.path.dirname(os.path.abspath(out))
    if not os.path.isdir(d):
        os.makedirs(d)

    try:
        out = str(validate_output_path(out))
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if input_image and Path(input_image).resolve() == Path(out).resolve():
        ap.error("--out must differ from --image to preserve the original")

    print("%s %dx%d, this takes about 30 seconds ..." %
          ("editing" if input_image else "drawing", w, h))

    if input_image is not None:
        print("--- EDIT MODE (flux-2-pro has NO mask/inpaint: the WHOLE image is re-synthesized) ---")
        print("  1) Edit from the ORIGINAL, not a previous edit, or drift compounds every pass.")
        print("  2) NAME every element to keep, especially faint/abstract ones (they erode first).")
        # Editing re-synthesizes the WHOLE image (flux-2-pro has no mask/inpaint). Turn OFF prompt
    # upsampling by default when editing so "keep element X" survives verbatim; let --upsample override.
    disable_pup = (input_image is not None) and (not a.upsample)
    generate.generate(prompt, w, h, out, key, input_image=input_image,
                      disable_pup=disable_pup, seed=a.seed)
    print(os.path.abspath(out))
    if not a.no_open and sys.platform == "darwin":
        subprocess.run(["open", out], check=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
