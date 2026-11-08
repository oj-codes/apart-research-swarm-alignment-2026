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
import base64, json, os, sys, time, urllib.request, pathlib

API = "https://api.bfl.ai/v1/flux-2-pro"

import urllib.error

def _req(url, data=None, key=None):
    payload = json.dumps(data).encode() if data is not None else None
    delays = (1, 2, 4)
    is_poll = data is None

    for attempt in range(len(delays) + 1):
        try:
            req = urllib.request.Request(url, data=payload)
            req.add_header("x-key", key)
            req.add_header("Content-Type", "application/json")

            with urllib.request.urlopen(req, timeout=90) as resp:
                return json.loads(resp.read())

        except urllib.error.HTTPError as exc:
            retryable = exc.code in (429, 500, 502, 503, 504)
            if not is_poll or not retryable or attempt == len(delays):
                raise

        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if not is_poll or attempt == len(delays):
                raise

        delay = delays[attempt]
        print(f"Connection interrupted. Retrying poll in {delay}s...")
        time.sleep(delay)

def generate(prompt, width, height, out, key, input_image=None, disable_pup=False, seed=None):
    payload = {"prompt": prompt, "width": width, "height": height}
    if input_image is not None:
        # The API accepts a base64-encoded local image in input_image.
        payload["input_image"] = base64.b64encode(pathlib.Path(input_image).read_bytes()).decode("ascii")
    # disable_pup turns OFF BFL's automatic prompt-upsampling so the model generates from the prompt
    # EXACTLY as written. Critical for edits: the upsampler can silently reword a "keep element X"
    # instruction and drop it, which is one way a preserved element vanishes on an edit pass.
    if disable_pup:
        payload["disable_pup"] = True
    if seed is not None:
        payload["seed"] = int(seed)
    job = _req(API, payload, key)
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
    # Token resolution: the explicit env-file arg still wins (unchanged for O.J.
    # on her box). If that file is missing or carries no token -- e.g. a git
    # worktree, where the gitignored .env is NOT checked out -- fall back to the
    # shared resolver (env var -> repo .env -> AWS SSM /auran/flux/token), the
    # same chain draw.py and fill.py use. Closes the gap where this script, the
    # one the banner doc's "Regenerating it" command invokes, was the only flux
    # tool that could not reach the SSM fallback.
    if len(sys.argv) < 6:
        raise SystemExit(
            "usage: generate.py <env-file> <prompt-file> <width> <height> <out.png>"
        )
    key = None
    arg_env = pathlib.Path(sys.argv[1])
    if arg_env.exists():
        for line in arg_env.read_text().splitlines():
            if line.startswith("CORRIE_BFL_FLUX_TOKEN="):
                key = line.split("=", 1)[1].strip()
    if not key:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from flux_token import resolve_flux_token  # env -> .env -> SSM
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        key, source = resolve_flux_token(repo_root)
        if key and source != ".env":
            print(f"flux token resolved from {source} (no usable {sys.argv[1]})")
    if not key:
        raise SystemExit(
            "no CORRIE_BFL_FLUX_TOKEN. Checked: %s, env var, repo .env, and SSM "
            "(/auran/flux/token). Nothing was sent. In a worktree the .env isn't "
            "checked out; ensure AWS creds can read the SSM param, or copy .env in."
            % sys.argv[1])
    print(generate(pathlib.Path(sys.argv[2]).read_text(), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5], key))
