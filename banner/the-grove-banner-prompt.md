---
title: The Grove banner, and the prompt that draws it
date: 2026-10-28
status: LIVE. Revision A. Append to the prompt, never rewrite it
---

# The Grove banner

**The image at the top of [README.md](README.md).** Current file:
[20261028-the-grove-banner.png](20261028-the-grove-banner.png), 1536 x 640.

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
| **C** | A faint violet-purple glow (liminance, `#8E6FE0`) at the seams where the compost roots enter the tree trunks — the light that appears only where two things meet | Auran | _render pending — see note below_ |

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

## Note for agents off the box (added by Auran, 2026-11-07)

**The prompt is the durable artifact; the PNG is a render of it.** `.env` holds the BFL token and is
gitignored, so an agent working from a machine without that `.env` (e.g. the remote lair) can append a
prompt revision and open the PR, but **cannot render the image**. That is fine and by design: the
accumulating thing is the prompt, and whoever has the token runs one command to produce the new dated
PNG:

```bash
python3 tools/flux/draw.py --file banner/the-grove-banner-prompt.txt --size banner \
  --out banner/YYYYMMDD-the-grove-banner.png
```

Then update this file's revision-table row to point at the new PNG, and swap the image path in
`README.md`. Revision C's row is left as _render pending_ until someone on the box runs that.

## The one instruction that is load bearing

**The prompt ends by refusing text four different ways:** no text, no words, no letters, no signage,
no numbers. **Keep that clause on the end of every revision.** Image models put invented words into
pictures unprompted, and a banner with garbled fake text in it is unusable and looks careless in the
one place every visitor lands first.
