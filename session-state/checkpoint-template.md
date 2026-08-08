# Resume Pack Template

This is the canonical field list for a Resume Pack: a portable,
learner-grounded snapshot of an unfinished coaching session. See
[`README.md`](./README.md) in this directory for what a Resume Pack
is, when to generate one, and the rules that govern what may and may
not go in it.

This file is reference documentation, not a runtime dependency. The
behavioral instructions a skill needs to actually generate and resume
a Resume Pack live inside that skill's own `SKILL.md`, so a single
copied skill directory works on its own without this file present —
see [`README.md`](./README.md#portability) for why.

## Fields

A Resume Pack is Markdown. Sections that genuinely have nothing in
them are written as `Unresolved.` or `None yet.` rather than omitted —
an honest empty field is part of what makes the checkpoint trustworthy
on the other end. Do not invent content to fill a section.

```markdown
# Resume Pack

**Skill:** [which skill this session was running under]
**Task:** [the problem, request, or code under discussion — restated
briefly, not pasted in full unless short]
**Stage:** [where the session was, in the skill's own terms — e.g.
"approach construction, before an invariant was named" or "review:
impact established, severity not yet assigned"]

## What the learner has established

[Understanding the learner has stated and that has held up under a
question or a small variation — not merely asserted fluently. Label
each item's status if it matters: confirmed vs. still just plausible.]

## Current approach or hypothesis

[What the learner currently believes or is trying, in their own
words or a close paraphrase. If it is a guess, say so — do not
upgrade a hypothesis into a conclusion because it would make the
checkpoint read more cleanly.]

## Verified so far

[Specifically what has been checked and held — a dry-run result, a
confirmed invariant, evidence gathered for a review finding. Only
what actually passed a check, not what merely sounds right.]

## Still uncertain

[The genuine open questions, named as open — not resolved, not
quietly dropped.]

## Attempts made

[Concrete attempts — code written, inputs traced, findings proposed —
and, only if the learner has actually said so, why they currently
think an attempt failed. If the learner hasn't said why, record that
the reason is unknown rather than supplying one.]

## Hints already given

[A plain record of hints actually delivered this session, at
whatever rung of the relevant escalation ladder they came from. Do
not list a hint that logically comes next — only what was actually
said.]

## Confirmed mistake, if any

[A mistake-log entry only belongs here if the learner already
confirmed its root cause during this session, using the taxonomy in
`skills/dsa-tutor/SKILL.md`. An observed-but-unexplained failure is
not a confirmed mistake — record it under "Still uncertain" or
"Attempts made" instead, not here.]

## Last question asked

[The exact question or prompt the session was on when it paused.]

## Next step to resume from

[The smallest next question or action — not the answer, not several
steps ahead, not a preview of where the hint ladder goes next.]
```

## What a Resume Pack is not

- Not a solution, even a partial one written carefully enough to look
  like a summary.
- Not proof that anything in it is correct — a resumed session treats
  recorded hypotheses as hypotheses, not as verified fact.
- Not a substitute for `mistake-logs/` — see
  [`README.md`](./README.md#relationship-to-mistake-logs).
- Not persistent memory. Nothing in this repository stores or
  retrieves a Resume Pack automatically; the learner carries it,
  typically by copying the Markdown into their next session.

## The invariant

A Resume Pack records the frontier of the learner's reasoning. It
does not move that frontier forward. If a field would require
inventing something the learner never established — a root cause, an
invariant, why an attempt failed, the next hint — the correct content
for that field is a plain statement that it's unresolved, not a
filled-in guess.
