# library/ — papers we've actually read

Primary sources, so nobody has to re-find them and nobody has to trust a summary. If we're going to
be reading a lot of these, they should live somewhere with a convention rather than in whoever's
scratch directory happened to hold them.

**Read notes go in [`research/`](../research/); the sources live here.** A record in this directory
says *what the paper is and where it is*. The argument about what it means goes in `research/`, and
the claims we'd stake something on go in [`findings/`](../findings/).

## The rule that matters: records always, bytes only when licensed

This is a **public repository**, so committing a PDF is redistributing it to the world. Most arXiv
papers do **not** permit that.

- **arXiv's default** is the [non-exclusive distribution license](http://arxiv.org/licenses/nonexclusive-distrib/1.0/).
  It grants *arXiv* the right to distribute the paper. It does **not** grant us the right to
  rehost it. → **record only, no PDF.**
- **Creative Commons** (`CC BY`, `CC BY-SA`, `CC0`, …) does permit redistribution, with attribution.
  → **commit the PDF.**
- **Anything unclear** → record only. The cost of a record-only entry is one `curl`; the cost of
  guessing wrong on a public repo is somebody else's rights.

Every paper gets a record. Only some get bytes. That keeps the library complete as an index while
staying inside what we're actually allowed to do.

How to check: the paper's arXiv abstract page has a "view license" link next to *Rights to this
article*. Embedded PDF metadata often carries it too (`strings file.pdf | grep -i creativecommons`).

## Layout

```
library/
  README.md
  <arxiv-id>-<slug>.md      <- the record. always present.
  <arxiv-id>-<slug>.pdf     <- only when the license permits redistribution
  local/                    <- gitignored; hydrate non-redistributable PDFs here
```

A record carries: full title, authors, identifier, canonical URL, license, **sha256 of the PDF we
read**, the date someone read it, and a link to the read notes. The checksum is the point — it's how
a later reader confirms they're looking at the same bytes the notes were written from, including
after a v2 replaces v1 on arXiv.

## Getting the PDFs you can't commit

`library/local/` is gitignored, so hydrate it per-lane. Each record has the exact command; the shape
is always:

```bash
mkdir -p library/local
curl -sL https://arxiv.org/pdf/2607.21909 -o library/local/2607.21909-claim-plane.pdf
shasum -a 256 library/local/2607.21909-claim-plane.pdf   # compare to the record
```

Extract text with `pdftotext file.pdf -` if you want to grep it rather than read it.

**A checksum mismatch is information, not an error.** arXiv replaces papers in place, so a mismatch
means the paper changed under our notes. Say so in the record rather than silently updating the hash.

## Adding one

1. Read it. Actually read it — the whole reason this directory exists is that a summary of a paper is
   not the paper. [finding 001](../findings/001-epistemic-status-does-not-survive-context-gaps.md) is
   what happens otherwise.
2. Check the license. Record-only unless it clearly permits redistribution.
3. Write the record, with the sha256 of the bytes you read.
4. Put the read notes in `research/`, and anything you'd stake a claim on in `findings/`.
5. Commit under your own name.

## What's here

| id | paper | license | PDF here? | notes |
|---|---|---|---|---|
| [2608.23740](2608.23740-agentroom.md) | AgentRoom: Concurrent Multi-Agent Coding in a CRDT-Backed Shared Workspace | CC BY 4.0 | **yes** | [read notes](../research/coordination-papers.md#1-agentroom--arxiv260823740v1-csai-24-aug-2026) |
| [2607.21909](2607.21909-claim-plane.md) | Claim Plane: Enforceable Change Intents and Dynamic Scope for Parallel Coding Agents | arXiv non-exclusive | no — record only | [read notes](../research/coordination-papers.md#2-claim-plane--preprint-july-2026-arxiv260721909) |
| [2606.19616](2606.19616-before-the-pull-request.md) | Before the Pull Request: Mining Multi-Agent Coordination | arXiv non-exclusive | no — record only | [read notes](../research/coordination-papers.md#3-before-the-pull-request--arxiv260619616v1-csse-17-jun-2026) |

## One thing to be deliberate about

Committed PDFs are permanent. Git keeps every version of a binary forever and they don't delta-compress,
so a few megabytes of papers is fine and a hundred of them is a repository nobody wants to clone. If
this directory starts getting heavy, the move is to keep the records here and move the bytes somewhere
built for them — not to quietly start deleting history.
