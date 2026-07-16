# Example Test-Case Session

This is an illustrative `test-case-coach` session, written to show the
skill's flow: one input dimension at a time, boundaries, an expected
output predicted before anything runs, one adversarial case aimed at
an assumption, and a redundant case cut during minimization. It is not
a transcript of an actual chat log — it is a realistic example built
to match the behavior described in
[`skills/test-case-coach/SKILL.md`](../skills/test-case-coach/SKILL.md).

The learner arrives with a working implementation. Nothing gets
debugged here — if a designed case had failed, the session would hand
off to `debug-coach` rather than silently switching modes.

---

**Learner:** I wrote a binary search that returns the index of the
_first_ occurrence of a target in a sorted array, or -1 if it's
absent. It passes the two sample inputs. What test cases should I
write before I trust it?

**Quackrates:** Before we pick a single input — in one sentence, what
exactly does your function promise? Including what "first" means when
the target appears more than once.

**Learner:** Given an ascending sorted array and a target, it returns
the smallest index whose value equals the target, or -1 if no element
equals it.

**Quackrates:** Good, that's a testable contract. Now, ignoring
specific values for a moment: what's one property of the _input_ that
can vary independently and might change how your code behaves?

**Learner:** The length of the array, I guess. Zero elements, one
element, many elements.

**Quackrates:** Take the smallest of those. Does your contract allow
an empty array — and if so, what must the function return for it?

**Learner:** Nothing says it can't be empty. Target can't be found in
an empty array, so it must return -1. I predict `([], 5) → -1`.

**Quackrates:** That's one case, with its expected output stated
before anything runs — keep doing that for every case. What's the
next boundary on that same dimension?

**Learner:** A single element. Two behaviors there, actually: the
element _is_ the target, or it isn't. So `([7], 7) → 0` and
`([7], 5) → -1`.

**Quackrates:** Two cases, two distinct behaviors — good instinct
splitting them. Length is covered at its edges now. What's a second
dimension, independent of length?

**Learner:** Where the target sits: the very first position, the very
last, somewhere in the middle, or absent entirely.

**Quackrates:** Which of those is the most dangerous boundary for a
binary search specifically?

**Learner:** First and last index — that's where off-by-one bugs in
`lo`/`hi` updates show up. So `([1, 3, 5, 7], 1) → 0` and
`([1, 3, 5, 7], 7) → 3`. And for absent, there are actually three
flavors: smaller than everything, larger than everything, and falling
between two elements. `([1, 3, 5, 7], 0) → -1`, `([1, 3, 5, 7], 9) →
-1`, `([1, 3, 5, 7], 4) → -1`.

**Quackrates:** Now the part your contract calls out explicitly and
your sample inputs probably never touched: what does your code
silently assume about _duplicates_?

**Learner:** Hm. A plain binary search stops at whatever match it
lands on. Mine is supposed to keep going left after a match. The
assumption to attack is "the first match found is the first
occurrence" — which is exactly what's false with duplicates.

**Quackrates:** So construct one adversarial input aimed squarely at
that assumption — the meanest version of it you can, and its expected
output before you run anything.

**Learner:** The entire array equal to the target: `([5, 5, 5, 5, 5],
5)`. A midpoint match lands at index 2, so if my "keep going left"
logic is wrong, I'd return 2 instead of 0. Expected output: 0.

**Quackrates:** That's a real adversarial case — one input, aimed at
one named assumption. One more candidate worth considering on the
duplicates dimension: duplicates that _don't_ include the target.
Does that exercise anything your absent-target cases don't?

**Learner:** ...no, actually. `([3, 3, 7, 7], 5) → -1` walks the same
"not found, between elements" path as `([1, 3, 5, 7], 4)`. Same
behavioral category, different costume. Cut it.

**Quackrates:** Good cut — that's the test a suite keeps out, not in.
Read your suite back, each case with the distinct behavior it covers.

**Learner:**

| #   | Input              | Expected | Distinct behavior covered                                                       |
| --- | ------------------ | -------- | ------------------------------------------------------------------------------- |
| 1   | `([], 5)`          | `-1`     | empty input, allowed by contract                                                |
| 2   | `([7], 7)`         | `0`      | single element, present                                                         |
| 3   | `([7], 5)`         | `-1`     | single element, absent                                                          |
| 4   | `([1,3,5,7], 1)`   | `0`      | target at first index                                                           |
| 5   | `([1,3,5,7], 7)`   | `3`      | target at last index                                                            |
| 6   | `([1,3,5,7], 0)`   | `-1`     | absent, below all elements                                                      |
| 7   | `([1,3,5,7], 9)`   | `-1`     | absent, above all elements                                                      |
| 8   | `([1,3,5,7], 4)`   | `-1`     | absent, between elements                                                        |
| 9   | `([5,5,5,5,5], 5)` | `0`      | all duplicates — attacks the "first match found is first occurrence" assumption |

**Quackrates:** Nine cases, every expected output predicted before a
single run, one assumption deliberately attacked, one redundant case
cut with a reason. Run them. If every one passes, this suite is done.
If any case fails — especially #9 — that input becomes the starting
failing case for a `debug-coach` session, which will try to minimize it
before diagnosing the first divergence. If #9 passes, it remains a
valuable adversarial test. If it exposes a bug and later passes after
the fix, its minimized failing form becomes a permanent regression
case.

---

_End of example. A real session may cover more dimensions (value
ranges, overflow in index arithmetic for fixed-width languages) or
fewer, depending on the contract — the constant is one dimension at a
time, learner-predicted outputs, and a justification attached to every
case that survives._
