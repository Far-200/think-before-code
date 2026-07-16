# Example Pattern-Transfer Session

This is an illustrative `pattern-transfer-coach` session, written to
show the skill's flow: stripping the story off a solved problem,
naming the maintained state, finding a rule-out condition, comparing a
near-miss, and adapting to exactly one cousin problem — whose solution
is never revealed. It is not a transcript of an actual chat log — it
is a realistic example built to match the behavior described in
[`skills/pattern-transfer-coach/SKILL.md`](../skills/pattern-transfer-coach/SKILL.md).

The learner arrives with a problem already solved. Note what doesn't
happen: the pattern is never named before the learner has abstracted
it, no list of similar problems appears, and the cousin problem ends
the session unsolved.

---

**Learner:** I just solved Longest Substring Without Repeating
Characters — grow a window rightward, and when a repeat shows up,
move the left edge past the earlier copy. It passes everything. I
don't want this to become "that one substring problem" I forget in a
week. What should I actually take away?

**Quackrates:** Then let's find out what you built, not what it was
called. Forget characters and substrings for a second — as your
solution scanned the input once, what did it maintain at every step,
and what did that let it safely ignore?

**Learner:** It kept a contiguous range — two indices — plus the last
position I'd seen each character at. And the range always satisfied
"no repeats inside it." Everything to the left of the range's left
edge, I never had to look at again.

**Quackrates:** So restate the task itself with the story nouns
removed. No characters, no strings — what is the input structurally,
and what is being computed over it?

**Learner:** Given a sequence, find the longest contiguous run that
satisfies some condition — here, "all elements distinct." I sweep a
window across it, keeping the condition true inside the window the
whole time.

**Quackrates:** What made it *safe* to only ever move the left edge
rightward — to discard those earlier positions forever instead of
reconsidering them?

**Learner:** Because once the condition broke, no run starting at or
before my current left edge could fix it without shrinking past the
violation. Shrinking from the left is the only repair, and it never
needs to be undone. The condition only gets easier to satisfy as the
window shrinks — that's what makes the discard permanent.

**Quackrates:** That last sentence is the load-bearing one. So in a
future problem statement, what should make this structure come to
mind — not "it mentions an array," what property of the *question*?

**Learner:** It asks for a longest or shortest *contiguous* run
satisfying a condition, and the condition behaves monotonically with
the window — growing can only break it, shrinking can only repair it.

**Quackrates:** And the other half, which matters just as much: name
one condition under which this exact structure fails or stops being
enough.

**Learner:** When shrinking doesn't reliably help. Like... a sum
condition over values that can be negative — dropping an element
might *raise* the sum instead of lowering it. The monotonicity is
gone, so the "left edge only moves right" discard isn't safe anymore.

**Quackrates:** Right — so hold that against a near-miss: "shortest
contiguous subarray with sum at least k, where values may be
negative." It reads almost identically to what you solved. Why does
your structure break on it, in one sentence?

**Learner:** Because with negatives, moving the left edge rightward
can increase or decrease the sum unpredictably — the window loses the
one-way repair property, so a plain two-edge sweep can skip the
optimal answer. Same costume, missing the invariant.

**Quackrates:** Good — recognition lives exactly at that boundary.
Now, one cousin, and only one: **Longest substring with at most two
distinct characters.** Before touching it — what carries over from
your solution unchanged, and what must change?

**Learner:** The whole skeleton carries over: two edges, sweep right,
shrink from the left when the condition breaks, condition is still
monotone — more distinct characters can only come from growing, fewer
only from shrinking. What changes is the state and the violation
test: instead of last-seen positions and "any repeat," I need counts
per character and a count of *distinct* characters, and the window is
in violation when distinct > 2. The shrink step decrements counts and
drops a character from the distinct tally when its count hits zero.

**Quackrates:** That's the adaptation, predicted before writing a
line — and that's where it stays. I'm not going to solve that one
with you; if you want guided help on it, that's a fresh `dsa-tutor`
session. Last thing: in one or two of your own sentences, the rule
you'll use to recognize this pattern next time — including one thing
that rules it out.

**Learner:** If a problem asks for an extreme-length contiguous run
satisfying a condition, and the condition can only break by growing
and only mend by shrinking, sweep a window and never move the left
edge backward. If shrinking can't be trusted to repair the condition
— negatives under a sum, anything non-monotone — the window is a
trap, not a tool.

**Quackrates:** Written by you, not recited at you. Go solve the
cousin.

---

_End of example. A second transfer round, with a new cousin, happens
only if the learner explicitly starts one — one cousin per round is
the rule, not a suggestion._
