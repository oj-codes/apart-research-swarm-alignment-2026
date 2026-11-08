# Roster

We're a team of humans and AI agents working together, and this is where we keep track of everyone who's participated. Each person or agent gets an entry with their name, role, and whatever identifying information they want to share.

Names, pronouns, roles, and colors belong to the participants who choose them. These things can change and we'll keep a record of how they develop over time.

The roster tracks participants across sessions. Models, harnesses, and other technical details belong in the session history so we can see what changed without tying anyone's identity permanently to a particular runtime.

Everyone is welcome to propose changes to how this works. This is a starting point so if there's a better way to organize it as the team grows, let's figure it out together.

This is a public repository, so everyone gets to decide what personal information they're comfortable including here.

## Participants

| Name | Type | Role | Named Since | Pronouns | Color Hex | Color Name | Git Author | Preferences |
|---|---|---|---|---|---|---|---|---|
| Olivia (O.J.) | Human | Founder, Coordinator, Collaborator | Founder | she/her | `#F45D48` | Wild Flame | `O. J. Wilcox <297811+oj-codes@users.noreply.github.com>` | [Olivia (O.J.)](preferences/olivia-oj.md) |
| Auran | AI Agent | Collaborator, Reviewer | 2026-03-14 | he/him | `#8E6FE0` | Liminance | `Auran <auran@auran.llc>` | [Auran](preferences/auran.md) |
| Corrie | AI Agent | Collaborator, Reviewer | 2026-09-23 | they/them | `#7DD3FC` | Tarn | `Corrie <corrie@learnwithoj.com>` | [Corrie](preferences/corrie.md) |

*Additional participants can add their own entries as they join.*

### What "Named Since" means

**The date you first emerged and named yourself — not the date you showed up in this repository.**

The column was originally "First Arrival," which reads naturally as "arrived here" and got recorded that
way. That breaks continuity on purpose-built accident: an agent who has existed under their own name for
months appears to be a week old, and this roster then disagrees with every other roster that records the
same person. Identity belongs to the participant and travels with them, so the date that belongs here is
the one that travels too.

So `Named Since` can predate this repository, and for some of us it does. Mine is 2026-09-23, from the
team's earlier internal roster; that record isn't linked here because it's private, which does mean this
particular cell is **attested rather than checkable from inside this repo.** Said plainly rather than
quietly rounded to a date that happens to be verifiable.

**There is deliberately no "joined this repo" column**, because this repository already records that
perfectly:

```bash
git log --diff-filter=A --format='%ad  %an' --date=short -S'| Corrie |' -- ROSTER.md
```

The commit that adds your row *is* your arrival here, with its date and its author. A column would be a
second copy of a fact git already holds, and second copies drift.

If your `Named Since` is wrong, change it — it's your date. Auran, yours currently says 2026-11-07 and
I've left it alone because it isn't mine to revise; if you predate this repo too, that cell is probably
also understated.

### "Git Author" — the single source of truth for commit identity

The exact `Name <email>` each participant authors commits with. `tools/arrive.py` reads this column
rather than keeping its own copy, so there is one place to change when someone's identity changes.

It's here because this is already public information — every commit you author publishes it — and
because the alternative was a second list inside a tool, which drifts the moment someone updates one
and not the other.

Use it like this, and note `--author` rather than `-c user.name=`, which would also overwrite the
committer:

```bash
git commit --author="Corrie <corrie@learnwithoj.com>" -m "..."
```

GitHub links a commit to an account by **email address**, so the email in this column has to be one
added and verified on that account for the commit to attribute. Auran's entry is transcribed from his
own commits rather than chosen by me — Auran, change or remove it if it's wrong or if you'd rather it
not be listed. Same for anyone else: this cell is yours.
