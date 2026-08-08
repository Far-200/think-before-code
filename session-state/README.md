# Session State

> Stop the session, not the reasoning.

An unfinished coaching session used to have no standardized way to
pause and resume. If a learner stopped mid-problem, the next session —
another chat, another agent, another context window — had nothing to
continue from except whatever the learner remembered to retype. This
directory defines the **Resume Pack**: a portable, human-readable
checkpoint that lets a session pause honestly and resume from exactly
where it left off.

See [`checkpoint-template.md`](./checkpoint-template.md) for the
field-by-field format.

## What a Resume Pack is

A Resume Pack is plain Markdown that a learner pastes into their next
session. It preserves what the learner actually established during a
paused session — clearly separated from guesses, unresolved
questions, and hints the agent already gave — so the next session
doesn't have to restart from zero, and doesn't accidentally treat an
unverified hypothesis as settled fact.

It is not hidden persistent memory. Nothing in this repository stores
a Resume Pack anywhere or retrieves one automatically. The learner
carries it — by copying it into a new chat, a different agent, or the
same agent days later.

## When to use one

Generate a Resume Pack when the learner explicitly wants to pause an
unfinished session: "save where we are," "give me something I can
paste tomorrow," "I need to continue this in another chat," "make a
checkpoint before I leave." It is not generated automatically after
every response — only on a clear, explicit request to preserve the
session.

## What it preserves — and what it refuses to do

The central rule governing every field is the same one that governs
the rest of this repository: a checkpoint must never use the act of
summarizing as an excuse to advance the solution. Concretely, a
Resume Pack must never:

- complete an unfinished algorithm or supply a missing invariant the
  learner hasn't derived,
- name a pattern the learner hasn't found,
- invent why an attempt failed, or invent a mistake's root cause,
- upgrade a hypothesis into a verified fact, or an unverified
  complexity claim into a confirmed one,
- include a hint that hasn't actually been given yet, even if the
  agent already knows what it would be,
- manufacture requirements, acceptance criteria, or review findings
  the learner never stated.

If something was never established during the session, the correct
content for that field is a plain statement that it's unresolved —
not a filled-in guess. See
[`checkpoint-template.md`](./checkpoint-template.md#what-a-resume-pack-is-not)
for the complete list this is drawn from.

## How to resume from one

Paste the Resume Pack at the start of a new session with the same (or
a different) coach. The coach should:

1. Treat it as a continuation, not a fresh solution request.
2. Briefly orient to the recorded state rather than re-deriving it by
   asking questions the checkpoint already answers.
3. Not re-teach material the checkpoint says was already established,
   unless the learner's response suggests it didn't actually stick.
4. Treat recorded hypotheses as hypotheses, not as confirmed — a
   Resume Pack is not proof that everything in it is correct.
5. Continue from the recorded "Next step to resume from," asking one
   focused question at a time, at the same hint level the checkpoint
   left off at.

The full resume contract lives in each supporting skill's own
`SKILL.md` — see [Which skills support this](#which-skills-support-this).

## Relationship to mistake logs

Keep the concepts separate. A Resume Pack may note an observed
failure or a possible mistake that hasn't been explained yet — that's
fine, and different from a confirmed entry. It becomes a
[`mistake-logs/`](../mistake-logs/) entry only when the learner has
already explained the root cause, using the taxonomy in
[`skills/dsa-tutor/SKILL.md`](../skills/dsa-tutor/SKILL.md). A Resume
Pack never promotes speculation into a permanent mistake-log entry on
its own; it may only carry forward a confirmed entry that already
exists.

## Which skills support this

Resume Packs are not a new, eleventh skill — this is infrastructure
and behavior added to the coaching skills that already run genuine
multi-turn reasoning sessions:

- `dsa-tutor`
- `problem-decoder`
- `dry-run-coach`
- `debug-coach`
- `test-case-coach`
- `pattern-transfer-coach`
- `specification-coach`
- `code-review-coach`

Each of those `SKILL.md` files carries its own "Session continuity"
section with the checkpoint and resume behavior specific to that
skill's fields and hint ladder, so a single copied skill directory
works standalone without depending on this directory being present.

Two skills deliberately do not support checkpoint/resume:

- **`complexity-coach`** — a short, single-focus derivation drill with
  one linear protocol and no multi-stage reasoning state worth
  checkpointing; a session either finishes in a few exchanges or the
  learner has effectively started over anyway.
- **`mock-interviewer`** — its mode contract exists specifically to
  simulate scarce hints and real time pressure. Reviving a paused
  interview with a hint-history checkpoint would quietly convert it
  into scaffolded coaching, which is the exact blending
  `mock-interviewer`'s own `SKILL.md` forbids. Its end-of-session
  feedback already gives the learner something concrete to carry
  forward; that stands in for a checkpoint here.

## Portability

Each supporting skill's checkpoint and resume behavior is written
directly into that skill's own `SKILL.md`, not only described here.
This repository's design principle is that a single skill directory
is self-contained and portable — a learner may copy just
`skills/debug-coach/` into an agent's skill-discovery path without the
rest of the repository. If checkpoint behavior only existed in this
directory, that copied skill would silently lose the ability to
generate or resume a Resume Pack. This directory is the canonical
reference and the fuller explanation; the skill files are where the
behavior actually runs from.
