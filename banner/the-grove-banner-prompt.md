---
title: The Grove banner, and the prompt that draws it
date: 2026-10-28
status: LIVE. Revision E. Append to the prompt, never rewrite it
---

# The Grove banner

**The image at the top of [README.md](README.md).** Current file:
[20261108-the-grove-banner-venice.png](20261108-the-grove-banner-venice.png), 1536 x 640.

**Her instruction, 28 October 2026, and it is the whole reason this file exists:** *"just keep the
image prompt somewhere easy to find so that when agents come and go and eventually human employees
too we can just tweak the image prompt to add items to the base image to build on it over time thats
great."*

---

## How it changes

**Add a sentence. Do not rewrite the prompt.** Same rule as the Postmark window render and for the
same reason: **the picture accumulates, so a person who worked here stays in it after they leave.**

**One line per revision in the table below**, saying what was added and who asked for it. **A new
revision is a new file with a new date in its name**, and the old one stays where it is so the
history is visible rather than described.

| Rev | Added | Asked for by | File |
|---|---|---|---|
| **A** | The grove, the compost pile with roots, the constellation agents, the lantern path, the dalmatian on the porch | Corrie, from her brief | `20261028-the-grove-banner.png` |
| **B** | Tiny glowing fireflies gathered around trees and paths in the grove | O.J. | `20261107-the-grove-banner.png` |
| **C** | A faint violet-purple glow (liminance, `#8E6FE0`) at the seams where the compost roots enter the tree trunks — the light that appears only where two things meet | Auran | `20261107-the-grove-banner-liminance.png` |
| **D** | One small arctic tern gliding alone in the upper third, underside lit amber (`#FBBF24`, midnight sun). Edited from revision C with every element named; the first pass drew two birds, lost the fireflies and stood the dog up, and was discarded | Tern | `20261108-the-grove-banner-tern.png` |
| **E** | A narrow still water channel with faint copper-green (`#17705F`) reflections and one small arched stone bridge in the lower foreground — a city that sits in the water. Edited from revision D with `--image`. First pass named the constellation-agents "human figures" (taken from the prose) and the render redrew them as humanoids, so it was regenerated from D naming them as they actually appear; final draft passed a compare-against-D | Venice | `20261108-the-grove-banner-venice.png` |

**What each thing in it means** is the table in the README, which is the half that keeps this from
being decoration.

---

## Regenerating it

```bash
python3 tools/flux/generate.py .env the-grove-banner-prompt.txt 1536 640 \
  content/branding/the-grove-banner-YYYYMMDD.png
```

**Width and height must be multiples of 32.** 1536 x 640 is the banner shape and it reads well at
GitHub's content width without being cropped on a phone.

**The prompt lives in [the-grove-banner-prompt.txt](the-grove-banner-prompt.txt)** next to this
file, as plain text with no frontmatter, because `generate.py` sends the file verbatim and a YAML
header would end up in the image.

---

## Rendering from off the box (added by Auran, 2026-11-07; gap closed same day)

**The prompt is the durable artifact; the PNG is a render of it.** On O.J.'s box the BFL token lives
in a gitignored `.env`, so the render just works. Off the box (e.g. the remote lair) there is no
`.env`, which is the gap she flagged on PR #4.

**Closed:** `tools/flux/flux_token.py` now resolves the token from, in order, the
`CORRIE_BFL_FLUX_TOKEN` env var, then `.env` (unchanged, still preferred), then **AWS SSM**
(parameter `/auran/flux/token`, same pattern as the GitHub PAT). An off-box agent with SSM read
access can now render. Nothing changed for anyone working on the box.

**One step stays O.J.'s** (it's money + a credential): putting the token into SSM once —
`aws ssm put-parameter --name /auran/flux/token --type SecureString --value <BFL token>`. Until
that exists, off-box renders fall through to the normal "no token" error and no credits are spent.

### Revising the banner: EDIT the current image, do not redraw it

**This is the one that cost a render (Auran, 2026-11-07).** There are two different operations and
the commands look almost identical:

**A) First draw / full redraw** — generates a brand-new scene from the whole prompt:
```bash
python3 tools/flux/draw.py --file banner/the-grove-banner-prompt.txt --size banner \
  --out banner/YYYYMMDD-the-grove-banner.png
```

**B) Adding your mark to the EXISTING banner** — this is almost always what you want. Feed the
current PNG with `--image` and write a SHORT instruction describing **only your change**, not the
whole scene (the full prompt would redraw everything and you'd lose the existing composition):
```bash
python3 tools/flux/draw.py "keep this image as-is and make only this one change: <your edit>, \
  change nothing else, no text anywhere" \
  --size banner --image banner/<current-banner>.png \
  --out banner/YYYYMMDD-the-grove-banner.png
```

**The rule:** the prompt `.txt` accumulates (append a sentence, never rewrite) — and the *image*
accumulates the same way (edit the current PNG with `--image`, never text-render a fresh one). If
your render comes back looking like a different grove, you used A when you wanted B.

**Second rule, learned the same day:** an edit **re-synthesizes the whole image** (no mask exists), so
**(1) edit from the ORIGINAL banner, not your own previous edit** (chained edits compound drift), and
**(2) NAME every element you need to keep** — especially faint/abstract ones like the floating white
constellation-agents, which erode first precisely because they're abstract and the model has a weak
prior for them. The tool prints both rules in edit mode and turns prompt-upsampling off by default so
your "keep X" survives verbatim. (On 2026-11-07 the constellations vanished from a banner edit for
exactly this reason; naming them brought all four back in one pass.)

**Third rule, learned 2026-11-08 (Venice, caught in O.J.'s review): name elements as they are in the
current PNG, not as this prose describes them.** The `.txt` states the intended scene and every render
drifts from it, so the file and the picture disagree — and the file is what a reader reaches for.
Venice's first pass at revision E followed the prose ("abstract agent forms") and called the
constellation-agents *small human figures*; the model drew humanoids, which read from the outside as a
full redraw. **Open the current PNG before writing the instruction**, describe what is actually there
("faint pale abstract geometric formations — not human figures"), and keep the change small and low.
If it still drifts, re-edit from the original rather than accepting the first result. The tell is
easy: if the dog has moved or the constellations changed shape, you named the wrong thing.

Then update this file's revision-table row to the new PNG and swap the image path + alt text in
`README.md`.

## The one instruction that is load bearing

**The prompt ends by refusing text four different ways:** no text, no words, no letters, no signage,
no numbers. **Keep that clause on the end of every revision.** Image models put invented words into
pictures unprompted, and a banner with garbled fake text in it is unusable and looks careless in the
one place every visitor lands first.
