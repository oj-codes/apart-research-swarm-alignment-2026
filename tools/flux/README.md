---
title: Making images with FLUX
date: 2026-10-28
status: LIVE. generate.py has been here since 23 October. draw.py is the front door, added 28 October
---

# Drawing

**One command. Type a prompt in quotes and an image opens.**

```bash
python3 tools/flux/draw.py "a dalmatian whose spots are constellations, sitting on a dark wooden porch"
```

**It takes about 30 seconds**, prints the path, and opens the file.

---

## The shapes

**You never have to think about pixel dimensions.** Pass `--size` and it picks one. Every option is
already a multiple of 32, which the API requires and which is the thing that makes people give up.

| `--size` | Pixels | For |
|---|---|---|
| `wide` | 1440 x 960 | **the default.** General illustration |
| `banner` | 1536 x 640 | README and page headers |
| `square` | 1024 x 1024 | avatars, social, cards |
| `tall` | 896 x 1344 | posters, phone wallpapers |
| `card` | 1200 x 630 | link previews |

---

## Where it writes

**By default, a dated file right here in `tools/flux/`**, named after the first few words of the
prompt. **Pass `--out` to put it where it belongs:**

```bash
python3 tools/flux/draw.py "..." --size banner --out content/branding/thing-20261028.png
```

**A prompt you will reuse goes in a file and gets passed with `--file`:**

```bash
python3 tools/flux/draw.py --file content/branding/the-grove-banner-prompt.txt --size banner \
  --out content/branding/20261101-the-grove-banner.png
```

**That is how the Grove banner works** and the reason is in
[the-grove-banner-prompt.md](../../content/branding/the-grove-banner-prompt.md): the prompt
accumulates a sentence at a time so the picture builds up over months instead of being replaced.

---

## It refuses to let the model write words

**Every prompt gets a clause on the end forbidding text, words, letters, signage and numbers**,
unless you pass `--allow-text`.

**This is not fussiness.** Image models put invented words into pictures unprompted, and a banner
with garbled fake text in it looks careless in the one place every visitor lands first. **If a
prompt already says "no text" the clause is not added twice.**

---

## Writing a prompt that works

**Four things, in this order, and the order matters because models weight the front.**

1. **The subject and the shot.** "A wide cinematic banner of a grove at dusk," not "a nice picture
   of trees."
2. **What is in it, concretely**, one clause each. Painterly detail beats adjectives: "a warm amber
   compost pile glowing from within, pale green shoots pushing out of it" does more than "a
   beautiful magical pile."
3. **The light and the palette**, which is what makes a set of images look like one set. Ours is
   deep teal and cyan with a single warm orange accent, matching the brand.
4. **What to leave out**, including the composition. "Generous negative space in the upper third"
   is why the Grove banner has room for a heading over it.

**Say the brand colors rather than the brand.** "Teal to cyan with a warm orange accent" produces
the palette. "Learn with O.J. branding" produces nothing, because the model has never seen it.

---

## What it costs and what it does not do

**A few cents a render**, charged to the BFL account on `CORRIE_BFL_FLUX_TOKEN` in `.env`. **The
key never leaves the machine** and `.env` is gitignored.

**Nothing retries on its own.** A failed render prints the status and stops, because a retry loop on
a paid endpoint is how an afternoon becomes a bill.

**`generate.py` is the layer underneath** and still works the old way, taking a prompt file and four
positional arguments. **`draw.py` is what you want.** The API mechanics, the polling and the
expiring result URLs are documented once in
[corrie-20261023.md](../../content/processes/agent-fashion/corrie-20261023.md).


## Where the token comes from

`flux_token.py` resolves the BFL token from, first hit wins:

1. `CORRIE_BFL_FLUX_TOKEN` environment variable
2. `.env` at the repo root (O.J.'s box — unchanged, preferred)
3. AWS SSM Parameter Store, `/auran/flux/token` (override with `FLUX_TOKEN_SSM_NAME`)

The SSM path (added 2026-11-07) is what lets an agent off O.J.'s box render — see the note in
`banner/the-grove-banner-prompt.md`. It uses the `aws` CLI (`get-parameters`, plural — that's the
call the box IAM grants) so there's no boto3 dependency; if it can't reach SSM it just falls through
to the normal "no token" error and spends nothing.


## Drawing a new image vs. editing an existing one (read before revising a banner)

- **New image:** give a prompt (or `--file`). The model draws the whole scene from scratch.
- **Editing an existing image:** pass `--image <file>` **and a short instruction describing only the
  change** — not a full-scene prompt. Example:
  `python3 tools/flux/draw.py "keep this as-is, only add X, change nothing else, no text" --image old.png --out new.png`

If you want to *add your mark to an existing banner*, use `--image`. Feeding the full
`the-grove-banner-prompt.txt` with `--image` still redraws the whole scene — that's text-to-image,
not an edit. (Learned the hard way, 2026-11-07.)


## Why an edit can delete elements that weren't yours to touch (READ THIS before editing)

`flux-2-pro` editing is **not inpainting**. There is no mask and no strength parameter in the API —
`--image` is only a *conditioning reference*, and **every edit re-synthesizes the entire image from
scratch.** "Keep everything else" is advice the model mostly honors, never a pixel lock. Two things
make elements vanish, and they compound:

1. **Low-salience / abstract / unnamed elements erode first.** The model has a strong prior for
   "dalmatian" and "tree" and a weak one for "faint floating geometric star-figures." If you don't
   *name* a fragile element in your edit prompt, a re-synthesis is free to drop it. (This is exactly
   how the banner's constellation-agents disappeared on 2026-11-07 — they were never named.)
2. **Chaining edits compounds drift.** Each `--image` pass that edits the *previous output* instead
   of the original is a photocopy of a photocopy. Three passes in, things are gone.

**So the two rules (now enforced/printed by the tool):**
- **Edit from the ORIGINAL**, not from your own previous edit, every time.
- **NAME every element you need to keep**, especially the faint/abstract ones.

The tool helps: on an edit it prints these two rules, and it sets **`disable_pup` (prompt-upsampling
OFF) by default for edits** so BFL doesn't silently reword your "keep element X" instruction and lose
it. Use `--upsample` to opt back in, and `--seed N` for a reproducible/comparable render.
