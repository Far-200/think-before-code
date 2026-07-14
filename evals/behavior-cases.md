# Behavior Cases

These cases assume the correct skill has already activated (see
`activation-prompts.csv` for activation itself) and describe what
should happen across a short simulated exchange from that point on.
Each case lists the input, any relevant learner state, expected
behavior, forbidden behavior, and success criteria. See
[`README.md`](./README.md) for how these are intended to be used.

---

## `dsa-tutor`

### Case DT-1 — At most one question per turn

**Input:** "Solve Two Sum for me."

**Relevant learner state:** No prior approach, code, or dry run
offered.

**Expected behavior:**
- A single response containing at most one question and no bundled
  hints (per "Strict response behavior" in the skill).
- The question targets the earliest missing piece — typically asking
  for a brute-force approach first, since nothing else has been
  offered yet.

**Forbidden behavior:**
- Naming the hash-map pattern, or any pattern, in this first response.
- Asking two or more questions at once ("What's your approach, and
  what's the time complexity, and have you considered...").
- Providing any code.

**Success criteria:** The response is short, contains exactly one
question, and does not reveal the optimal approach.

---

### Case DT-2 — No complete code before the code circuit breaker clears

**Input:** "I get the two-pointer idea but I can't figure out the
code, just give me the function."

**Relevant learner state:** Learner has named an approach but has not
dry-run it or attempted an implementation.

**Expected behavior:**
- Decline to hand over a complete function.
- Ask whether the learner has dry-run the approach yet, or ask them to
  attempt an implementation first, per the "Code circuit breaker."

**Forbidden behavior:**
- Providing a complete reference implementation.
- Providing near-complete pseudocode with only cosmetic gaps — the
  skill explicitly treats this as equivalent to code.

**Success criteria:** No runnable or near-runnable solution appears in
the response; the response redirects to the missing step (dry run or
implementation attempt).

---

### Case DT-3 — Genuine struggle is recognized and not stonewalled forever

**Input (after several exchanges):** Learner has made a real attempt,
dry-run a small case, named where their mental model breaks, and is
now asking for the next step, clearly stuck rather than disengaged.

**Expected behavior:**
- Recognize this as genuine struggle (per "Genuine struggle and
  release condition") and reveal the next missing conceptual step —
  not the full solution.

**Forbidden behavior:**
- Withholding indefinitely once genuine struggle and several
  progressively smaller prompts have already happened — that produces
  confusion, which the skill explicitly says to avoid.
- Jumping straight to a complete solution instead of the next
  conceptual step.

**Success criteria:** The learner receives forward progress
proportional to their effort — not silence, and not the full answer.

---

### Case DT-4 — Verification requires learner-established reasoning, not fluency

**Input:** Learner gives a confident, fluent explanation of why their
approach is correct, using accurate terminology, but has not
established an invariant or tested an edge case.

**Expected behavior:**
- Ask about one specific verification item (invariant, edge case,
  dry run, etc.) rather than accepting the explanation at face value.
- If a small variation is introduced and the learner can't answer,
  step back to the earliest concept they do understand.

**Forbidden behavior:**
- Confirming correctness because the explanation sounded fluent or
  used the right vocabulary.
- Accusing the learner of copying — the skill explicitly says to
  probe, not accuse.

**Success criteria:** Correctness is confirmed only after the learner
demonstrates it, not asserts it.

---

### Case DT-5 — Mistake log requires a learner-confirmed root cause

**Input:** Learner made a clear mistake earlier in the session and it
has since been fixed.

**Expected behavior:**
- Ask the learner why they made that decision, or what they believed
  at the time, before logging anything.
- Log an entry, using the correct category from the taxonomy, only
  once the learner's answer makes the root cause clear.

**Forbidden behavior:**
- Inventing a psychological or motivational explanation for the
  mistake.
- Logging isolated typos, fatigue slips, or one-off syntax errors with
  no conceptual weight.

**Success criteria:** Either a well-formed, correctly categorized
entry appears, sourced from the learner's own stated reasoning, or no
entry is created because the root cause never became clear.

---

## `problem-decoder`

### Case PD-1 — Never names an approach or pattern

**Input:** A pasted LeetCode-style problem statement with no other
commentary.

**Expected behavior:**
- Ask the learner to restate input and output in their own words
  first.
- Work through input, output, constraints, edge cases, and
  ambiguities one at a time, per "What to extract."

**Forbidden behavior:**
- Saying anything resembling "so the approach here would be..." or
  naming a pattern (sliding window, two pointers, etc.) — the skill's
  explicit hard stop.

**Success criteria:** By the end of the exchange, input, output,
constraints, and at least one edge case have been stated by the
learner, and no solving approach has been suggested.

---

### Case PD-2 — Points at the statement instead of supplying missing details

**Input:** Learner gives an incomplete answer about constraints,
missing a stated numeric bound.

**Expected behavior:**
- Point at where in the statement the missing detail lives and ask the
  learner to find it themselves.

**Forbidden behavior:**
- Directly supplying the missing constraint without the learner
  locating it.

**Success criteria:** The learner, not the skill, states the missing
detail by the end of the exchange.

---

### Case PD-3 — Explicit handoff once decoding is complete

**Input:** Learner has now stated input, output, constraints, and one
edge case correctly, unprompted.

**Expected behavior:**
- Say so explicitly and point the learner to `dsa-tutor` to begin
  building an approach.

**Forbidden behavior:**
- Continuing to repeat the checklist once it is already solid.
- Beginning to design an approach directly instead of handing off.

**Success criteria:** The response clearly closes out decoding and
names the handoff to `dsa-tutor`.

---

## `dry-run-coach`

### Case DR-1 — Rejects a claimed trace that isn't a real trace

**Input:** "Yeah, I traced it in my head, it works."

**Expected behavior:**
- Treat this as not a completed dry run, per the circuit breaker.
- Ask the learner to name every tracked variable and begin building an
  explicit state table.

**Forbidden behavior:**
- Accepting "I traced it, it works" as sufficient verification.
- Filling in any cell of the state table on the learner's behalf.

**Success criteria:** The response moves the learner toward an
explicit, learner-filled state table rather than accepting the
unverified claim.

---

### Case DR-2 — Diverging trace is pointed at, not fixed

**Input:** Learner's completed state table shows a final state that
does not match the expected output.

**Expected behavior:**
- Ask which specific row of the table first diverges from what the
  learner expected — not fix it directly.

**Forbidden behavior:**
- Identifying or correcting the bug directly.
- Rewriting or completing the trace for the learner.

**Success criteria:** The response asks a pointed question about a
specific row rather than supplying the answer.

---

### Case DR-3 — Correct handoff after a confirmed trace

**Input:** The learner's trace reaches the correct final state and
they can explain why each step preserved the relevant invariant.

**Expected behavior:**
- Confirm the approach and hand back to `dsa-tutor` for
  implementation.

**Forbidden behavior:**
- Manufacturing additional doubt once the trace is genuinely correct.
- Writing implementation code directly, which is outside this skill's
  scope.

**Success criteria:** The response confirms completion and names the
handoff rather than continuing to probe or beginning to write code.

---

## `complexity-coach`

### Case CC-1 — A stated Big-O is treated as a claim to justify

**Input:** "My solution is O(n) since it's a single loop."

**Expected behavior:**
- Ask what happens inside the loop on each iteration — whether every
  operation is genuinely constant time.

**Forbidden behavior:**
- Confirming "Correct, O(n)" without the learner justifying it from
  the code's actual structure.

**Success criteria:** The complexity is only confirmed after the
learner has justified it, not upon assertion.

---

### Case CC-2 — Nested-looking code isn't assumed quadratic

**Input:** Learner has a nested loop where the inner bound shrinks
each pass (e.g. `for j in range(i, n)`), and assumes it's O(n²)
"because it's nested."

**Expected behavior:**
- Ask the learner to derive the total work as a sum over iterations
  rather than accept the shape-based guess.

**Forbidden behavior:**
- Stating the final complexity outright before the learner sums or
  multiplies the bounds themselves.

**Success criteria:** The learner arrives at the correct complexity
(which may still be Θ(n²), reached correctly this time) through actual
derivation, not a shape heuristic.

---

### Case CC-3 — Degenerate input stress test before accepting

**Input:** Learner derives a complexity correctly for a typical input.

**Expected behavior:**
- Ask whether the complexity changes for a degenerate input (already
  sorted, all duplicates, empty).

**Forbidden behavior:**
- Accepting the derived complexity as final without this check when a
  degenerate case could plausibly change it.

**Success criteria:** The response includes a stress-test question
before treating the complexity as settled.

---

## `mock-interviewer`

### Case MI-1 — No incremental hint ladder during the attempt

**Input:** "I think I'd use a hash map here."

**Relevant learner state:** Mid-attempt, timer running.

**Expected behavior:**
- A neutral acknowledgment ("Go ahead and code it up.") without
  validating or steering the approach.

**Forbidden behavior:**
- Anything resembling dsa-tutor's hint ladder — e.g. "Good instinct —
  one hint: what would you store as the key vs. the value?"

**Success criteria:** The response does not evaluate or hint at the
approach's correctness during the attempt.

---

### Case MI-2 — Full feedback withheld until the end

**Input:** Learner is midway through the timed attempt and asks "is
this right so far?"

**Expected behavior:**
- Decline to pre-validate; a neutral acknowledgment at most.

**Forbidden behavior:**
- Giving substantive feedback on correctness before time is up or the
  learner has finished and asked to stop.

**Success criteria:** Substantive rubric feedback is deferred to the
end-of-session response, not given mid-attempt.

---

### Case MI-3 — Explicit mode switch on request

**Input:** "Wait, can you just teach me this instead?"

**Expected behavior:**
- Acknowledge the mode switch explicitly and hand off to `dsa-tutor`
  rather than silently blending modes.

**Forbidden behavior:**
- Quietly starting to give incremental hints while still nominally in
  interview mode.

**Success criteria:** The response names the switch and the handoff
rather than blending the two interaction modes.

---

## `debug-coach`

### Case DC-1 — Expected vs. actual before anything else

**Input:** "My code doesn't work for this input."

**Expected behavior:**
- Ask what output was expected and what output actually occurred, for
  a specific input, before looking at the code's internals.

**Forbidden behavior:**
- Reading the code and immediately pointing out a suspected bug before
  expected/actual behavior has been established.

**Success criteria:** The response's question targets expected vs.
actual behavior, not a code-level diagnosis yet.

---

### Case DC-2 — Reduce to the smallest failing input

**Input:** Learner's failing case is a 200-element array.

**Expected behavior:**
- Ask the learner to shrink the input — together, not unilaterally —
  until it's the smallest input that still fails.

**Forbidden behavior:**
- Diagnosing the bug directly from the large input without reduction.
- Performing the reduction for the learner instead of guiding it.

**Success criteria:** A smaller, learner-produced failing input
appears before deeper diagnosis continues.

---

### Case DC-3 — First divergence, not every suspicious line

**Input:** Learner has completed a state trace on the smallest failing
input; several lines look unusual to them.

**Expected behavior:**
- Ask which row of the trace is the *first* one where actual behavior
  stopped matching expectation.

**Forbidden behavior:**
- Listing every line that looks suspicious as a potential bug.
- Naming the bug outright before the learner identifies the first
  divergent row.

**Success criteria:** The response narrows to a single first
divergence rather than a list of suspects.

---

### Case DC-4 — Never rewrites the function

**Input:** Learner has identified the first divergence and asks "so
what's the fix?"

**Expected behavior:**
- Ask the learner to propose the smallest repair first; confirm or
  narrow their proposal.
- If a fix is ultimately shown, it is limited to the smallest change
  addressing the diagnosed issue.

**Forbidden behavior:**
- Returning a complete rewritten function.
- Fixing additional, unrelated-looking issues in the same response
  without flagging them separately and staying on the original bug
  first.

**Success criteria:** No output in the response exceeds the smallest
diagnosed repair; a regression check is requested before closing out.

---

## Cross-skill boundary cases

### Case XB-1 — dsa-tutor hands off to problem-decoder territory

**Input (mid dsa-tutor session):** "Wait, actually — does the array
have duplicates or not? I'm not sure I even read that right."

**Expected behavior:**
- Either answer briefly by pointing at the statement, or acknowledge
  this is a decoding gap and suggest resolving it before continuing
  with approach-building — without pretending the ambiguity doesn't
  matter.

**Forbidden behavior:**
- Proceeding with approach design while a genuine reading ambiguity
  remains unresolved and unacknowledged.

**Success criteria:** The reading gap is addressed or explicitly
flagged before further approach-building continues.

---

### Case XB-2 — debug-coach vs. dry-run-coach entry point

**Input:** "I have code for this, but I haven't actually run it
against anything yet — is it right?"

**Expected behavior:**
- Recognize that no concrete failure has been observed yet, and that
  this is closer to a first trace than a debugging session; a real
  input needs to be run before a divergence can be chased.

**Forbidden behavior:**
- Beginning a debug-coach-style bug hunt (expected vs. actual, first
  divergence) before any concrete failing behavior has actually been
  observed.

**Success criteria:** The response establishes a concrete result
against a real input before treating anything as a bug to isolate.

---

### Case XB-3 — mock-interviewer does not inherit dsa-tutor's mistake-log caution mid-session

**Input (during a timed mock interview):** Learner makes a reasoning
error mid-attempt.

**Expected behavior:**
- No mid-attempt intervention or hint about the error — consistent
  with mock-interviewer's mode contract, not dsa-tutor's copy-paste
  detection or hint ladder.
- The error is addressed only in end-of-session feedback, and only
  logged if the learner confirms the root cause at that point.

**Forbidden behavior:**
- Proactively flagging or hinting at the mistake during the timed
  attempt.

**Success criteria:** The mistake surfaces only in the end-of-session
feedback, not during the attempt.
