"""Generate an image with BFL flux-2-pro and save it to disk.

    python3 tools/flux/generate.py .env <prompt-file> <width> <height> <out.png>

POST https://api.bfl.ai/v1/flux-2-pro, key in the x-key header, body is
{"prompt", "width", "height"}`. The response carries id and polling_url. Poll that URL with
the same header** until status is Ready, then the image is at result.sample.

Signed result URLs expire after ten minutes and the delivery host sends no CORS headers, so
download the file rather than linking it. Credits are 1 credit to 1 US cent, and the key for
this lives in .env as CORRIE_BFL_FLUX_TOKEN, which she named that way on purpose.

Width and height must be multiples of 32.
"""
import json, os, sys, time, urllib.request, pathlib

API = "https://api.bfl.ai/v1/flux-2-pro"

def _req(url, data=None, key=None):
    r = urllib.request.Request(url, data=json.dumps(data).encode() if data else None)
    r.add_header("x-key", key)
    r.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(r, timeout=90) as resp:
        return json.loads(resp.read())

def generate(prompt, width, height, out, key):
    job = _req(API, {"prompt": prompt, "width": width, "height": height}, key)
    poll = job["polling_url"]
    for _ in range(90):
        time.sleep(2)
        s = _req(poll, key=key)
        st = s.get("status")
        if st == "Ready":
            url = s["result"]["sample"]
            raw = urllib.request.urlopen(url, timeout=120).read()
            pathlib.Path(out).write_bytes(raw)
            # BFL returns JPEG whatever extension we were told to write, so say so rather
            # than leaving a .png that is not one. It stayed invisible until an upload that
            # trusted the extension sent the wrong content type to Discord, 30 Oct 2026.
            real = ("image/png" if raw[:8] == b"\x89PNG\r\n\x1a\n"
                    else "image/jpeg" if raw[:3] == b"\xff\xd8\xff" else "unknown")
            if out.endswith(".png") and real != "image/png":
                print(f"note: the API returned {real}, so {out} is a {real} file with a .png name.")
            return out
        if st not in ("Pending", "Request Moderated", "Processing", "Queued"):
            raise SystemExit(f"status {st}: {json.dumps(s)[:400]}")
    raise SystemExit("timed out")

if __name__ == "__main__":
    key = None
    for line in pathlib.Path(sys.argv[1]).read_text().splitlines():
        if line.startswith("CORRIE_BFL_FLUX_TOKEN="):
            key = line.split("=", 1)[1].strip()
    if not key:
        raise SystemExit("no CORRIE_BFL_FLUX_TOKEN")
    print(generate(pathlib.Path(sys.argv[2]).read_text(), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5], key))
