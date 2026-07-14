# Example Tutoring Session

This is an illustrative, complete `dsa-tutor` session, written to show
the full pipeline end to end: understanding the problem, a genuine
wrong turn, a self-corrected approach, a dry run, a real implementation
bug, and a closing mistake-log entry. It is not a transcript of an
actual chat log — it is a realistic example built to match the
behavior described in
[`skills/dsa-tutor/SKILL.md`](../skills/dsa-tutor/SKILL.md).

Quackrates keeps its responses short and asks one thing at a time
throughout — that's the point of the skill, not an accident of this
example.

---

**Learner:** Here's the problem I'm stuck on:
> Given an integer array `nums`, find the contiguous subarray
> (containing at least one number) which has the largest sum, and
> return that sum.

**Quackrates:** Before we go anywhere near an approach — in your own
words, what exactly are you looking for here?

**Learner:** The biggest sum you can make by picking numbers out of
the array.

**Quackrates:** Close, but "picking numbers out" and "a contiguous
subarray" aren't the same thing. If `nums = [3, -1, 3]`, is `[3, 3]`
(skipping the `-1`) a valid subarray for this problem, or not?

**Learner:** Oh — no, it has to be numbers that are actually next to
each other in the array. So `[3, -1, 3]` would have to be considered
as one block if I wanted both 3s.

**Quackrates:** Right. Now — forget efficiency completely. What's the
most direct way you could find this, even if it's slow?

**Learner:** I could just look at every possible subarray, add it up,
and keep the biggest sum I find. That's like every start index and
every end index, so O(n²) subarrays, and summing each one is another
O(n), so O(n³) total I think.

**Quackrates:** That tracks. Now think about whether there's a way to
avoid redoing work — as you scan through the array once, is there
anything about the sums you've already seen that would help you avoid
recomputing everything for every new subarray?

**Learner:** I think so — I could keep a running sum as I go. And
here's my idea: keep adding numbers to the running sum, but if the
running sum ever goes negative, reset it back to zero, since a
negative running sum can only drag down anything I add after it.
Track the biggest running sum I see along the way as the answer.

**Quackrates:** Walk me through that on `nums = [-3, -1, -2]`. What
does your algorithm return?

**Learner:** Running sum starts at 0. Add -3, sum is -3, that's
negative so reset to 0. Add -1, sum is -1, negative, reset to 0. Add
-2, same thing, reset to 0. Biggest sum I ever saw was 0, so it
returns 0.

**Quackrates:** And the problem says the subarray has to contain at
least one number. Given that, is a sum of `0` actually achievable
here, or is that describing a subarray that doesn't exist?

**Learner:** ...it's not achievable. Every actual subarray of
`[-3, -1, -2]` has a negative sum, since every number is negative. The
best real answer is `[-1]` by itself, which sums to -1. My algorithm
is quietly allowing an "empty" subarray by resetting to zero, and
that's not a legal answer.

**Quackrates:** That's the core of it. So if resetting to a fixed zero
isn't safe, what should you compare against instead, at each step, to
decide whether to extend the current run or start fresh from the
current number?

**Learner:** Instead of comparing to zero, I should compare "keep
extending the current subarray" against "just start a brand new
subarray at this number" — so `current_sum = max(nums[i], current_sum
+ nums[i])`. That way I never manufacture a subarray sum lower than
what a single element could give me on its own.

**Quackrates:** And separately from `current_sum`, what do you still
need to track to actually answer the question?

**Learner:** The best `current_sum` I've seen at any point — a running
`max_sum`, updated after every step.

**Quackrates:** Good — before writing any code, let's dry-run that on
a real example: `nums = [-2, 1, -3, 4, -1, 2, 1, -5, 4]`. What are
`current_sum` and `max_sum` before the loop even starts?

**Learner:** I'll set both to `nums[0]`, which is `-2`, and start the
loop from index 1.

**Quackrates:** Go ahead and build the table — one row per index,
columns for the number, `current_sum`, and `max_sum`. Fill it in
yourself as you go.

**Learner:**

| index | num | current_sum | max_sum |
| --- | --- | --- | --- |
| 0 | -2 | -2 | -2 |
| 1 | 1 | max(1, -2+1)=1 | 1 |
| 2 | -3 | max(-3, 1-3)=-2 | 1 |
| 3 | 4 | max(4, -2+4)=4 | 4 |
| 4 | -1 | max(-1, 4-1)=3 | 4 |
| 5 | 2 | max(2, 3+2)=5 | 5 |
| 6 | 1 | max(1, 5+1)=6 | 6 |
| 7 | -5 | max(-5, 6-5)=1 | 6 |
| 8 | 4 | max(4, 1+4)=5 | 6 |

**Learner:** Final `max_sum` is 6, which matches the known answer for
this example (the subarray `[4, -1, 2, 1]`).

**Quackrates:** That's a real trace, and it checks out. Go ahead and
write the implementation.

**Learner:** Here's what I've got:

```python
def maxSubArray(nums):
    max_sum = 0
    current_sum = 0
    for num in nums:
        current_sum = max(num, current_sum + num)
        max_sum = max(max_sum, current_sum)
    return max_sum
```

**Learner:** I ran it on the same example from the dry run and it
returned 6, so it looks right.

**Quackrates:** It'll pass that one. Try it on `[-3, -1, -2]` — the
same input you used earlier — and tell me what it actually returns
versus what you expect it to return.

**Learner:** I expect -1. Let me check... it returns 0.

**Quackrates:** Same shape of bug as before it seems. Let's trace it
properly instead of guessing — what are `current_sum` and `max_sum`
set to on the line right before the loop starts?

**Learner:** Both set to `0`.

**Quackrates:** And in the dry run you just did, what did you
initialize them to instead?

**Learner:** `nums[0]`. ...I hardcoded `0` in the actual code instead
of using the first element. So `max_sum` starts able to "beat" every
real subarray sum in an all-negative array, the same way my very
first version quietly allowed an empty subarray.

**Quackrates:** That's the first divergence — nothing after that line
needs to change yet. What's the smallest fix that makes the
initialization match what you actually traced?

**Learner:** Set both `max_sum` and `current_sum` to `nums[0]` before
the loop, then loop over `nums[1:]` instead of all of `nums`, so I
don't process the first element twice.

```python
def maxSubArray(nums):
    max_sum = nums[0]
    current_sum = nums[0]
    for num in nums[1:]:
        current_sum = max(num, current_sum + num)
        max_sum = max(max_sum, current_sum)
    return max_sum
```

**Quackrates:** Re-check both inputs against that version — the
all-negative case and the original dry-run example.

**Learner:** `[-3, -1, -2]` now returns -1, correct. And
`[-2, 1, -3, 4, -1, 2, 1, -5, 4]` still returns 6. Both match.

**Quackrates:** Good — now, without looking at the code shape and
guessing a label, what's the time complexity, and why?

**Learner:** There's a single loop over the array, one pass, doing
constant work per element — one comparison, one addition, one more
comparison. So O(n) time.

**Quackrates:** And space?

**Learner:** Only two variables regardless of input size, so O(1)
auxiliary space — not counting the input array itself.

**Quackrates:** That holds. One more thing before we close this out —
what was actually going on in your head both times you initialized
things to zero? Not "it was a typo" — what did you believe?

**Learner:** I think I never fully let go of the idea from my very
first approach, that a subarray sum has some kind of "zero floor." I
fixed it conceptually in how `current_sum` updates, but when I sat
down to write the code, `max_sum = 0` just felt like the obvious
starting point, and I didn't check it against the same all-negative
case that had already caught this exact mistake once.

**Quackrates:** That's a clear root cause, so let's log it.

```markdown
## Mistake — Kadane's Algorithm — reasoning-error

**What happened:**
I initialized `max_sum` (and, in my first approach, effectively
`current_sum`) to 0, which let the algorithm quietly treat an empty
subarray as a valid answer.

**Why:**
I believed a running subarray sum has a natural "floor" at zero, and
that belief survived even after I had already found and fixed it once
at the reasoning stage — it resurfaced as a hardcoded initial value
when I wrote the actual code.

**Antidote:**
Before initializing any "best so far" variable, ask: "does this
starting value describe a real, legal answer, or a convenient
placeholder?" If it's a placeholder, test the all-same-sign case
immediately.
```

**Quackrates:** One follow-up, structurally related: try **Maximum
Product Subarray** — same "track a running best as you scan once"
shape, but a single negative number can flip a small product into a
large one, so a running maximum alone won't be enough this time.

---

_End of example. This session shows the full pipeline; a real session
may be longer, shorter, or branch differently depending on where the
learner actually gets stuck._
