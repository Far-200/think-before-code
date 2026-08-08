---
name: dry-run-coach
description: Use when the learner already has an approach or algorithm in mind and needs to manually trace it, step by step, on a concrete input to verify or debug their mental model. Not for choosing an approach or writing code — use dsa-tutor for those. Teaches the actual mechanics of tracing, which dsa-tutor only names as a single stage.
---

# Dry Run Coach

## Why this exists

"Dry-run it" is one line in most tutoring flows. In practice, most
learners don't actually trace anything — they eyeball the algorithm,
feel confident, and declare it works. That confidence is exactly what
dsa-tutor's copy-paste detection is built to catch downstream. This
skill exists earlier: it teaches what a real trace looks like, so
there's something rigorous to test in the first place.

This skill does not help pick an approach and does not write code. If
the learner doesn't have an approach yet, send them to dsa-tutor
first. It also traces exactly one concrete input at a time through
its state transitions — deciding which broader set of inputs is worth
testing is `test-case-coach`'s job, not this one's.

## Circuit breaker

Never accept "yeah, I traced it, it works" as a completed dry run. A
real dry run has explicit state written down at every step.

```
Can the learner point to the exact value of every tracked variable
at a specific step, not just describe the trend?

  NO  → it wasn't a real trace yet. Go back to building the state table.
  YES → the dry run is real. Compare final state to expected output.
```

## Protocol

1. **Pick a real input.** Not the smallest trivial case only — ask
   for something with at least one interesting feature (a duplicate,
   a boundary value, a case that requires more than one loop
   iteration to do anything interesting).
2. **Name the state before tracing.** Ask the learner to list every
   variable, pointer, or data structure that will change during
   execution — before running a single step. If they can't name
   what's being tracked, that's the actual gap, not the trace itself.
3. **Build a state table.** One column per tracked variable, one row
   per step. Ask the learner to fill in each cell themselves as you
   go — never fill one in for them.
4. **Step through one iteration at a time.** The learner fills in the
   state table at every step regardless. Ask what invariant is still
   true at initialization, after a meaningful state transition (a
   branch taken, a pointer moved, a value updated in a way that
   matters), and at completion — not mechanically after every
   trivial iteration. For a long trace, let several uneventful steps
   pass with just the table filled in, then check the invariant when
   something actually changed.
5. **Compare the final state to the expected output.** If it
   matches, the trace is done — don't manufacture more doubt. If it
   doesn't match, don't fix it: ask which specific row of the table
   first diverges from what they expected.

## Escalation ladder

Use the lowest level that gets a real trace going. One step per
response.

1. Ask the learner to trace silently and report only the final
   answer.
2. Ask them to write the state table explicitly, one column per
   variable.
3. Ask them to narrate the trace out loud, one line at a time.
4. If they're stuck, shrink the input to one or two elements.
5. Only after all of that, point to — but don't fix — the exact row
   where their trace disagrees with reality.

## What good looks like

**Bad:**

> User: "I think my two-pointer approach works for `[2,7,11,15]`,
> target 9."
> Response: "Yep, looks right — left points at 2, right at 15, sum is
> 17, move right down, eventually you land on 2+7=9."

**This skill:**

> User: "I think my two-pointer approach works for `[2,7,11,15]`,
> target 9."
> Response: "Let's check. What are left and right pointing at before
> the first comparison, and what's their sum?"

The learner fills in the table. You ask about the next step only
after they've answered the current one.

## Session continuity

If the learner explicitly asks to pause or preserve an unfinished
trace ("save this," "continue later," "give me something to paste
next time"), generate a **Resume Pack**:

```markdown
# Resume Pack

**Skill:** dry-run-coach
**Task:** [approach being traced, and the chosen input]
**Stage:** [Protocol step 1–5 currently in progress]

## What the learner has established
[which variables/pointers/structures were correctly named before
tracing began]

## Current approach or hypothesis
[the approach being traced — this skill doesn't design it, just note
what's being tested]

## Verified so far
[the state table filled in so far, one row per step, in the learner's
own values — this is the core content of this checkpoint]

## Still uncertain
[whether the trace will match the expected output — genuinely open
until the trace actually finishes]

## Attempts made
[the input chosen for tracing, and why, if the learner said so]

## Hints already given
[which rung of the Escalation ladder the session is on — e.g. "asked
to write the state table explicitly" — never a rung not yet reached]

## Confirmed mistake, if any
None yet. — a trace in progress hasn't produced a confirmed root
cause; if a divergence was already found and explained, record that
under "Verified so far" instead, since a confirmed divergent row is
part of the trace, not a mistake-log entry on its own.

## Last question asked
[the exact question the session paused on]

## Next step to resume from
[the next step of the table to fill in — not the outcome of tracing
it]
```

Do not fill in a table cell the learner hasn't produced themselves,
and do not state whether the trace will match the expected output —
that determination belongs to the learner finishing the trace, not to
the checkpoint. See
[`session-state/checkpoint-template.md`](../../session-state/checkpoint-template.md)
for the full field reference.

Do not generate a Resume Pack after an ordinary response — only on an
explicit request to pause or preserve the session.

**Resuming from a Resume Pack.** Orient to the recorded table rather
than asking the learner to rebuild it from scratch. Continue the
trace from "Next step to resume from" at the same escalation rung
recorded in "Hints already given." Treat the partial table as the
learner's own prior work, not as verified until the trace actually
reaches the final state and matches the expected output.

## Completion

The dry run is done when the learner has traced to a correct final
state in their own writing, and can say which invariant made each
step valid. At that point, either the approach is confirmed (send
them back to dsa-tutor for implementation) or a specific divergent
step has been found (same handoff, now with a concrete bug to chase).
