# Example: Interrupted and Resumed Session

This is an illustrative `debug-coach` session split into two parts —
Session A ends mid-trace with a Resume Pack, and Session B resumes
from it in a fresh chat. It is not a transcript of an actual chat
log — it is a realistic example built to match the behavior described
in [`skills/debug-coach/SKILL.md`](../skills/debug-coach/SKILL.md)
and [`session-state/README.md`](../session-state/README.md).

Debug-coach was chosen for this example because its state — a
partially filled trace table — is concrete enough to make the central
distinction obvious: what the learner has actually verified in the
table stays in the checkpoint; what hasn't been reached yet (the
violated assumption, the fix) stays out of it, even though the coach
can already see where the trace is heading.

---

## Session A — interrupted mid-trace

**Learner:** This is supposed to find the length of the longest
substring without repeating characters, but it's returning 2 for
`"abba"` when I think it should return 2 anyway... wait, no, I think
it's wrong for `"pwwkew"`. It gives me 2 there and I'm pretty sure the
answer is 3.

**Quackrates:** Let's pin that down precisely before touching the
code. For `"pwwkew"`, what substring is your function's answer of `2`
supposed to correspond to, and what substring do you believe the
correct answer of `3` corresponds to?

**Learner:** My function's `2` — I'm not actually sure which
substring it's counting. The correct answer of `3` should be `"wke"`.

**Quackrates:** Good, that's the actual behavior nailed down as "some
substring I haven't identified yet," which is honest — don't guess at
it. `"pwwkew"` has six characters; is that the smallest input you can
still see this failure on, or does it fail on something shorter too?

**Learner:** Let me check... it also fails on just `"ww"`. My function
returns 2 for that, but the answer should be 1, since 'w' repeats.

**Quackrates:** `"ww"` it is — much easier to trace than the full
string. Before we run anything: what variables does your sliding
window actually track?

**Learner:** A `left` pointer, a `right` pointer, a `seen` set of
characters currently in the window, and a `max_len` for the best
answer so far.

**Quackrates:** Set up a table with those four columns. Walk through
`"ww"` character by character — what's the state after processing
index 0, the first `'w'`?

**Learner:** `right = 0`, `left = 0`, `seen = {'w'}`, `max_len = 1`.

**Quackrates:** And after index 1, the second `'w'` — what does your
code actually do when it hits a character already in `seen`?

**Learner:** It should shrink the window... okay, tracing it: `right`
becomes 1. `'w'` is already in `seen`. My code does `seen.add('w')`
first, *then* checks membership — so by the time it checks, `'w'` was
already added and the check against a stale copy never fires. `seen`
stays `{'w'}`, `left` never moves, and `max_len` gets compared against
`right - left + 1 = 2`, so `max_len` becomes 2. That's the bug, I
think — the check happens after the add instead of before.

**Quackrates:** That's a real finding from the trace, not a guess —
good. Before we call it done: what's the smallest change that would
make the "shrink the window when I see a repeat" assumption actually
hold, given what you just traced?

**Learner:** Hold on, I need to actually leave for something — can you
save where we are? I want to pick this back up later without losing
the trace.

**Quackrates:** Here's your Resume Pack.

```markdown
# Resume Pack

**Skill:** debug-coach
**Task:** Longest substring without repeating characters. Learner's
sliding-window implementation returns 2 for `"pwwkew"` (expected 3)
and 2 for `"ww"` (expected 1).
**Stage:** Operating procedure step 6 (violated assumption) — a
candidate cause has just been proposed from the trace, not yet
confirmed as the smallest repair.

## What the learner has established

- Expected behavior on `"pwwkew"`: the longest repeat-free substring
  has length 3 (`"wke"`).
- Actual behavior on `"pwwkew"`: the function returns 2, though the
  learner has not yet identified which substring that 2 corresponds
  to — recorded as unidentified, not guessed at.
- Smallest failing input: `"ww"`, expected output 1, actual output 2.
- Tracked variables: `left`, `right`, `seen` (a set), `max_len`.

## Current approach or hypothesis

Learner's hypothesis, not yet confirmed as the smallest repair: the
code calls `seen.add(right_char)` before checking whether
`right_char` was already in `seen`, so the repeat-detection check
always runs against a set that already contains the incoming
character and never fires.

## Verified so far

State trace on `"ww"`, filled in by the learner:

| step (index) | left | right | seen      | max_len |
|--------------|------|-------|-----------|---------|
| 0 (`'w'`)    | 0    | 0     | `{'w'}`   | 1       |
| 1 (`'w'`)    | 0    | 1     | `{'w'}`   | 2       |

First divergent row: index 1. Expected `max_len` to stay 1 (window
should shrink); actual `max_len` became 2.

## Still uncertain

- Whether the add-before-check ordering is the *complete* explanation,
  or only part of it — not yet checked against `"pwwkew"`.
- The smallest repair — not yet reached.

## Attempts made

No repair proposed yet. The learner named the candidate cause above
but the session paused before proposing a fix.

## Hints already given

- Asked for expected vs. actual behavior on a specific input (rung 1).
- Asked the learner to shrink the failing case (rung 2) — arrived at
  `"ww"`.
- Asked the learner to build the state trace themselves (rung 3).
- Asked a pointed question about the specific divergent row (rung 5).

No hint at rung 6 or beyond has been given — the violated-assumption
naming above was the learner's own conclusion from the trace, not
something supplied.

## Confirmed mistake, if any

None yet. A root cause hasn't been confirmed through the "why did you
structure it that way" question this skill asks before logging
anything — only the mechanical explanation has been reached so far.

## Last question asked

"What's the smallest change that would make the 'shrink the window
when I see a repeat' assumption actually hold, given what you just
traced?"

## Next step to resume from

Ask the learner to propose the smallest repair to the add/check
ordering — not to supply it.
```

Paste that back in whenever you're ready — no need to re-explain any
of it.

---

## Session B — resumed in a new chat

**Learner:** Continuing a debug-coach session.

```markdown
# Resume Pack

**Skill:** debug-coach
**Task:** Longest substring without repeating characters. Learner's
sliding-window implementation returns 2 for `"pwwkew"` (expected 3)
and 2 for `"ww"` (expected 1).
**Stage:** Operating procedure step 6 (violated assumption) — a
candidate cause has just been proposed from the trace, not yet
confirmed as the smallest repair.

[... full Resume Pack as generated above ...]
```

**Quackrates:** Picking this back up — you'd traced `"ww"` down to the
add-before-check ordering as the likely cause, right at the point of
proposing a fix. What's the smallest change to that ordering that
would make the window actually shrink on a repeat?

Note what didn't happen: no re-request for the expected or actual
behavior, no rebuilding the state table from scratch, and no jump
ahead to naming or writing the fix — the session picked up from
exactly the question it paused on.

**Learner:** Check membership first, then add — so: `if right_char in
seen: shrink the window`, and only afterward `seen.add(right_char)`.

**Quackrates:** Trace it against your `"ww"` table with that ordering.
At index 1, `'w'` is checked against `seen = {'w'}` before anything is
added — what happens to `left` and `seen` now?

**Learner:** `'w'` is in `seen`, so I remove characters from the left
until it isn't — that removes the first `'w'`, `left` becomes 1,
`seen` becomes empty. Then I add the current `'w'`, `seen = {'w'}`,
and `max_len` compares against `right - left + 1 = 1`, so `max_len`
stays 1. That matches.

**Quackrates:** Now the regression check — re-trace `"pwwkew"` in your
head with the corrected ordering, or run it. What does it return?

**Learner:** I ran it — 3, for `"wke"`. That matches.

**Quackrates:** And one more input the original bug could plausibly
have broken the same way?

**Learner:** Anything with two repeats back-to-back, like `"aa"` — same
add-before-check problem would've hit immediately.

**Quackrates:** That's your regression case. The fix is yours, and the
original failing input plus `"aa"` both hold. If you want systematic
coverage beyond these, `test-case-coach` is the next stop, and
`"ww"` goes in as a permanent regression case.

---

_End of example. Note across both parts: the Resume Pack preserved the
learner's own trace and reasoning exactly as far as they'd taken it —
including the mechanical explanation they'd already worked out — but
did not supply the fix, confirm the hypothesis as correct, or invent
why earlier attempts (there weren't any recorded) had failed. Session
B asked exactly one question, at exactly the point Session A stopped,
and treated the carried-over hypothesis as something to verify, not
something to accept._
