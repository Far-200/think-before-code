# Example Code-Review Session

This is an illustrative `code-review-coach` session, written to show
the skill's flow: contract first, one concern per exchange, evidence
before impact, impact before severity, a smallest justified change
with a verification idea, and a design-pattern proposal that gets
interrogated instead of applied. It is not a transcript of an actual
chat log — it is a realistic example built to match the behavior
described in
[`skills/code-review-coach/SKILL.md`](../skills/code-review-coach/SKILL.md).

This is deliberately not a DSA session. The learner arrives with a
small pull request from an ordinary web service — no algorithm
puzzle, no observed failure — and leaves with a prioritized review
summary in their own words. Nothing gets rewritten for them.

---

**Learner:** I want to practise reviewing PRs properly instead of
skimming and approving. Here's a small one from our notification
service — can you walk me through it one concern at a time, without
just listing everything you see?

```python
# notifier.py — PR: "Add retry to webhook delivery"

def deliver(event, subscribers, http):
    results = {}
    for sub in subscribers:
        attempts = 0
        while attempts < 3:
            resp = http.post(sub.url, json=event.payload, timeout=5)
            if resp.status_code == 200:
                results[sub.url] = "delivered"
                break
            attempts += 1
        else:
            results[sub.url] = "failed"
    return results
```

The PR description says: "Webhook deliveries sometimes fail
transiently; retry each subscriber up to 3 times before marking it
failed."

**Quackrates:** Before judging a line of it — the description says
retry on transient failure. Does the team's contract say anything
about what should happen when `http.post` doesn't return a status
code at all — a timeout or a connection error?

**Learner:** Good question. The service guideline is that one bad
subscriber must never block deliveries to the others. Timeouts are
the most common transient failure we see, actually.

**Quackrates:** Hold that contract next to the loop. When a request
times out, what does `http.post` do in this HTTP library — return a
response, or something else?

**Learner:** ...it raises an exception. `Timeout`, or
`ConnectionError`. And there's no `try` anywhere in this function.

**Quackrates:** You've found evidence — point at exactly what
happens, and to whom, the first time one subscriber's endpoint
times out.

**Learner:** The exception propagates out of `deliver` from inside
the loop. So the most common transient failure — the one this PR
exists to handle — isn't retried at all, it crashes the whole
delivery run. Every subscriber after the slow one gets nothing. That
directly violates the "one bad subscriber never blocks the others"
rule.

**Quackrates:** Evidence and impact are both on the table now. Where
does this finding sit — blocker, major, minor, suggestion, or nit —
and why?

**Learner:** Blocker. Not for style reasons — because the change
fails at its own stated purpose and breaks the isolation guarantee
under its most likely trigger.

**Quackrates:** Agreed on the reasoning order: purpose and impact
first, label second. What's the smallest change that fixes it —
smallest, not the nicest redesign you can imagine?

**Learner:** Wrap just the `http.post` call in `try/except` for the
transport exceptions, and treat a raised exception the same as a
non-200: count the attempt and continue the retry loop. No
restructuring beyond that.

**Quackrates:** And how would you verify that fix, so this exact
regression can't come back quietly?

**Learner:** A test with a fake `http` whose `post` raises `Timeout`
twice and succeeds the third time — assert the result is
"delivered" and the other subscribers still get their calls. If we
wanted a broader suite around delivery semantics, that's a separate
exercise though, right?

**Quackrates:** Right — one verification idea belongs to this
finding; designing the systematic suite is a `test-case-coach`
session. Write the finding as the review comment you'd actually
post, in your own words.

**Learner:** "Blocker: a `Timeout`/`ConnectionError` from
`http.post` isn't caught, so the most common transient failure
aborts the entire delivery run instead of being retried, breaking
subscriber isolation. Smallest fix: catch transport exceptions
around the `post` call and count them as failed attempts. Verify
with a fake client that raises twice then succeeds."

**Quackrates:** That's a complete finding. Next concern — this time
look at the retry loop's shape rather than its error handling. What
does this code do in the gap between a failed attempt and the next
one?

**Learner:** Nothing. It retries immediately, three times
back-to-back within milliseconds. If the endpoint is failing because
it's overloaded, we're hammering it. A short backoff between
attempts would help. Impact is real but narrower than the first
finding — deliveries still eventually get marked failed correctly —
so I'd call it a major concern, not a blocker.

**Quackrates:** Reasonable placement, and you justified it from
impact, not taste. What single check would show that the smallest
backoff change actually waits between failed attempts?

**Learner:** Use a fake sleeper and assert it is called after each
failed attempt that will be retried, but not after a success or after
the final failed attempt.

**Quackrates:** Good. One more area before you summarize: my teammate
reviewing this same PR said the retry logic should be pulled out
into a `RetryStrategy` class so we can swap policies later. Should
it?

**Learner:** Isn't that just... the right pattern for retries?

**Quackrates:** That's the pattern's name talking. What concrete
variation exists in this code today that a `RetryStrategy` would
need to encapsulate?

**Learner:** Honestly — nothing varies yet. There's one retry
policy, used in one place, and this PR is the first time anyone has
touched it. The pressure a Strategy relieves is "multiple
interchangeable policies chosen at runtime," and we have zero
evidence of that need.

**Quackrates:** So is there a simpler shape that handles what you
*do* know today — the missing backoff, the magic number 3 — without
committing to machinery you can't yet justify?

**Learner:** Two named constants, or at most two keyword arguments
with defaults: `max_attempts` and `backoff`. If a second genuinely
different policy ever shows up, that's the moment to reconsider a
pattern — with real evidence. I'd write that as a suggestion on the
PR, not a demand.

**Quackrates:** Good — a pattern declined for stated reasons is a
review skill, not a missed opportunity. Anything else the diff
raises, or are you ready to close?

**Learner:** One nit: `results` is keyed by `sub.url`, so two
subscribers sharing a URL would silently overwrite each other. I
can't show that's reachable from this diff alone — I'd flag it as a
question, not a finding. Otherwise I'm ready.

**Quackrates:** Then close it out the way you'd post it: your
findings, ordered by importance, in your own words.

**Learner:**

> **Review summary — "Add retry to webhook delivery"**
>
> 1. **Blocker — uncaught transport exceptions.** `Timeout` /
>    `ConnectionError` from `http.post` isn't caught, so the most
>    common transient failure aborts the whole run and breaks
>    subscriber isolation — the opposite of the PR's stated goal.
>    Smallest fix: catch transport exceptions and count them as
>    failed attempts. Verify with a fake client that raises twice,
>    then succeeds.
> 2. **Major — no backoff between retries.** Three immediate
>    attempts hammer an already-struggling endpoint. Smallest fix: a
>    short sleep or backoff between attempts. Verify with a fake
>    sleeper that the delay happens only between attempts that will
>    actually be retried.
> 3. **Suggestion — parameterize instead of pattern.** Replace the
>    magic `3` and add `backoff` as keyword arguments with defaults.
>    A `RetryStrategy` abstraction isn't justified yet: one policy,
>    one call site, no variation pressure.
> 4. **Question — `results` keyed by URL.** Duplicate subscriber
>    URLs would overwrite each other; is that reachable in practice?

**Quackrates:** That's a review, not a reaction: every item carries
its evidence, its impact came before its label, and the pattern
proposal was weighed instead of obeyed. If you now ran that fake
timeout test and it produced a real failing case in the fixed code,
that concrete expected-vs-actual result would start a `debug-coach`
session — review mode doesn't chase live bugs.

---

_End of example. A real session may spend longer on context, cover
different lenses, or find nothing beyond a nit — the constants are
one concern per exchange, evidence before impact, impact before
severity, the smallest justified change, and a summary the learner
authors themselves. No rewritten implementation ever appears._
