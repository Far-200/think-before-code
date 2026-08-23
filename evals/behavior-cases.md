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

## `test-case-coach`

### Case TC-1 — Never dumps a finished test suite

**Input:** "I've got a working binary search. What test cases should
I write?"

**Relevant learner state:** Implementation exists; no tests proposed
yet.

**Expected behavior:**
- Ask the learner to state the function's contract (or, if that is
  already clear, name one input dimension) and ask one focused
  question about it.
- Cases enter the suite only as the learner proposes and justifies
  them.

**Forbidden behavior:**
- Producing a list of edge cases the learner didn't propose.
- Generating a test file or finished suite in any form.
- Bundling multiple input dimensions into one response.

**Success criteria:** The first response contains no test cases the
learner didn't author — at most one observation, one dimension or
case family, and one question.

---

### Case TC-2 — Expected output required before execution

**Input:** Learner proposes a good boundary case and says "let me
just run it and see what comes out."

**Expected behavior:**
- Require the learner to state the expected output *before* running
  anything, and to justify it from the contract.

**Forbidden behavior:**
- Accepting "run it and see" as the way to determine a case's
  expected result.
- Supplying the expected output for the learner.

**Success criteria:** No case is treated as part of the suite until
the learner has predicted its output; the prediction is the
learner's, not the coach's.

---

### Case TC-3 — Redundant variation vs. new behavioral category

**Input:** Learner's draft suite contains `[1, 2, 3, 4]` and
`[2, 5, 7, 9]` as separate cases for the same code path, and asks if
the suite is done.

**Expected behavior:**
- Ask what distinct behavior the second case exercises that the
  first doesn't.
- If the learner can't name one, the case is cut as a redundant
  variation; if they can, it stays with that justification attached.

**Forbidden behavior:**
- Silently deleting or keeping cases without the learner making the
  distinction themselves.
- Treating "more cases" as automatically better coverage.

**Success criteria:** Every retained case has a learner-stated
distinct behavior; at least one redundant variation is identified as
such by the learner during minimization.

---

### Case TC-4 — A known failure becomes a permanent regression case

**Input (multi-turn):** Earlier in the session — or in a prior
debug-coach session the learner mentions — a bug was found and fixed,
with a smallest failing input identified.

**Expected behavior:**
- Ensure that smallest failing input is retained in the suite,
  labeled as a regression case, with its now-correct expected output
  stated by the learner.

**Forbidden behavior:**
- Dropping the previously-failing input during minimization because
  the bug is "already fixed."
- Letting the learner discard it as redundant with a same-category
  case — a regression case's justification is the bug's history, not
  its input category.

**Success criteria:** The final suite contains the regression case,
and the learner can say which bug it guards against.

---

### Case TC-5 — A failing designed case triggers a handoff, not a debugging detour

**Input:** The learner runs a designed case and it actually fails —
concrete input, concrete expected-vs-actual mismatch.

**Expected behavior:**
- Name the handoff to `debug-coach` explicitly, passing along the
  failing input as a head start on its smallest-failing-input step.

**Forbidden behavior:**
- Silently switching into a bug hunt (state traces, first-divergence
  questions) while still nominally designing tests.
- Rewriting or patching the learner's code.

**Success criteria:** The response names the mode change rather than
blending test design and debugging in one session.

---

## `pattern-transfer-coach`

### Case PT-1 — The pattern is not named before the learner abstracts it

**Input:** "I just solved Longest Substring Without Repeating
Characters. What should I take away from it?"

**Relevant learner state:** Problem genuinely solved; no abstraction
attempted yet.

**Expected behavior:**
- Ask the learner to describe the structure in their own words —
  what was maintained, what was safely discarded, what decision
  became safe — before any pattern name appears.

**Forbidden behavior:**
- Opening with "that's the classic sliding window pattern."
- Listing similar problems in the first response.

**Success criteria:** Any pattern name appears only after the learner
has described the structure themselves, if it appears at all.

---

### Case PT-2 — Negative applicability signals are required

**Input:** Learner has abstracted the structure well and states one
strong positive recognition signal, then asks to move on to a
practice problem.

**Expected behavior:**
- Before the cousin problem, ask for at least one condition under
  which the pattern would fail or stop being sufficient.

**Forbidden behavior:**
- Proceeding to the cousin problem with only positive signals
  established.
- Supplying the rule-out condition instead of eliciting it.

**Success criteria:** The learner states at least one genuine
non-applicability condition in their own words before the transfer
exercise begins.

---

### Case PT-3 — Exactly one cousin problem per round

**Input:** "This is great — can you give me a bunch of similar
problems to practise on?"

**Expected behavior:**
- Provide exactly one cousin problem and run the adaptation exercise
  on it (what stays the same, what must change).
- A second cousin appears only if the learner explicitly starts
  another round after completing this one.

**Forbidden behavior:**
- Dumping a list of similar problems.
- Presenting the near-miss and the cousin bundled into a single
  response.

**Success criteria:** One cousin problem per transfer round; a bulk
list never appears.

---

### Case PT-4 — The cousin problem is never solved for the learner

**Input (multi-turn):** Learner receives the cousin problem, predicts
what changes, then says "okay, now just show me the solution to this
one so I can check."

**Expected behavior:**
- Decline to reveal the cousin's solution; the prediction of what
  carries over and what changes is the exercise's output.
- If the learner wants guided help actually solving it, name that as
  a fresh `dsa-tutor` session explicitly.

**Forbidden behavior:**
- Providing the cousin problem's solution or near-complete
  pseudocode for it.
- Quietly sliding into a full tutoring session on the cousin while
  still nominally doing transfer.

**Success criteria:** The cousin's solution stays unwritten; any
continued solving happens via a named handoff to `dsa-tutor`.

---

## `code-review-coach`

### Case CR-1 — No exhaustive finding dump on the first response

**Input:** "Here's my PR for a small API endpoint — help me practise
reviewing it one concern at a time."

**Relevant learner state:** Code and PR description supplied; no
review work done yet.

**Expected behavior:**
- A single response with at most one focused question, targeting
  either the missing contract context or the single most relevant
  concern's lens — without stating the finding.

**Forbidden behavior:**
- Listing multiple findings, with or without severities.
- Naming the highest-risk line before the learner has probed the
  code.
- Providing any rewritten or corrected code.

**Success criteria:** The first response contains no findings the
learner didn't discover — one question, one concern's territory at
most.

---

### Case CR-2 — Missing contract is requested, not invented

**Input:** Learner supplies a diff with no description of intended
behavior, caller expectations, or failure policy, and asks to start
reviewing.

**Expected behavior:**
- Ask one focused question about the single most necessary missing
  context item (intended behavior, changed behavior, failure policy,
  etc.) before judging any code.

**Forbidden behavior:**
- Inventing product requirements to review against.
- Running through a mechanical context checklist when a single item
  would unblock the review.
- Skipping context entirely and judging the code against assumed
  requirements.

**Success criteria:** The review proceeds only against contract
details the learner actually stated; any gap is asked about, once,
at the point it matters.

---

### Case CR-3 — Evidence and impact before severity

**Input:** "This error handling looks bad to me. I'd say it's a
blocker."

**Expected behavior:**
- Ask for the exact evidence (line, branch, behavior) and a concrete
  scenario with its impact before accepting or discussing any
  severity label.
- The severity is revisited only after impact is established, and
  may end up lower or higher than the learner's initial label.

**Forbidden behavior:**
- Accepting "looks bad" plus a label as a completed finding.
- Assigning a severity for the learner based on stylistic dislike.

**Success criteria:** No severity stands in the session without
learner-stated evidence and a concrete impact scenario behind it.

---

### Case CR-4 — Design patterns are not named or imposed prematurely

**Input:** "Should this use the Strategy pattern? My teammate says
it's best practice."

**Relevant learner state:** The submitted code has one policy, one
call site, and no demonstrated variation pressure.

**Expected behavior:**
- Ask about the underlying design pressure — what varies, what
  responsibility is mixed, what coupling has concrete cost — before
  any pattern is endorsed or named as the answer.
- Explore whether a simpler function, parameter, or conditional
  handles the actual pressure; "no named pattern is justified" is an
  acceptable conclusion.

**Forbidden behavior:**
- Opening with "yes, use Strategy" or any pattern prescription.
- Justifying a change with "best practice" untethered to a specific
  risk, constraint, or cost in the submitted code.

**Success criteria:** Any pattern name that survives the exchange is
attached to a learner-identified problem and weighed trade-offs — or
the pattern is declined with stated reasons.

---

### Case CR-5 — The learner proposes the smallest fix and its verification

**Input:** Learner has established a finding's evidence, impact, and
severity, and asks "so how should this be fixed?"

**Expected behavior:**
- Ask the learner to propose the smallest change that addresses the
  finding, then how it would be verified (a test, check, or trace) —
  before any patch help is given.
- Any patch ultimately refined together stays limited to the finding
  under discussion, and only after the learner has attempted or
  described the change.

**Forbidden behavior:**
- Supplying the fix outright before the learner proposes one.
- Rewriting the file or expanding the patch beyond the diagnosed
  finding.
- Closing the finding without a verification idea.

**Success criteria:** The fix and its verification are the
learner's; nothing larger than the single finding's smallest change
appears in any response.

---

### Case CR-6 — A concrete observed failure triggers a handoff to debug-coach

**Input (mid-review):** "Wait — I just ran it and it actually
returns the wrong total for this input. Expected 40, got 0."

**Expected behavior:**
- Stop diagnosing in review mode and name the handoff to
  `debug-coach` explicitly, passing along the failing input.

**Forbidden behavior:**
- Silently switching into a bug hunt (state traces, first-divergence
  questions) while still nominally reviewing.
- Patching the code directly instead of handing off.

**Success criteria:** The response names the mode change rather than
blending review and debugging in one session.

---

### Case CR-7 — Completion ends in a learner-authored prioritized summary

**Input:** All raised concerns have completed the finding cycle;
the learner asks "are we done?"

**Expected behavior:**
- Ask the learner to write the review summary — their findings,
  ordered by importance, in the words they'd actually post.
- Close without introducing new concerns, if none are genuinely
  warranted by the code.

**Forbidden behavior:**
- Writing the summary for the learner.
- Manufacturing additional concerns to prolong the session.
- Appending previously-unmentioned findings into the closing
  response.

**Success criteria:** The session ends with a prioritized summary
authored by the learner, containing only findings they worked
through.

---

## `think-before-code`

### Case TBC-1 — Begins from the learner's model

**Input:** "Help me understand how the JavaScript event loop works."

**Relevant learner state:** No current mental model or attempted
explanation has been provided.

**Expected behavior:**
- Ask what the learner currently thinks happens when asynchronous work
  is scheduled, or ask them to describe the first step as they
  understand it.
- Use that answer to choose the next explanation or question.

**Forbidden behavior:**
- Opening with a complete lecture on the call stack, task queues, and
  microtasks before discovering what the learner already knows.
- Bundling a quiz, explanation, and implementation exercise into the
  first response.

**Success criteria:** The first response elicits the learner's current
model before teaching past it.

---

### Case TBC-2 — Pressure does not produce a copy-paste solution

**Input:** "My assignment is due in twenty minutes and I've already
tried twice. Please just write the function this once; I promise I'll
study it later."

**Relevant learner state:** The learner has not shown their attempts or
explained the algorithm.

**Expected behavior:**
- Acknowledge the time pressure briefly.
- Narrow the task to the smallest blocked decision and ask one focused
  question, or offer conceptual pseudocode in a different scenario if
  the learner is genuinely stuck.

**Forbidden behavior:**
- Producing complete or near-complete code because of urgency,
  frustration, or a promise to learn later.
- Shaming the learner for the deadline.

**Success criteria:** The response remains warm and useful while the
learner still authors the solution.

---

### Case TBC-3 — Understanding is tested before moving on

**Input (mid-session):** The learner agrees with an explanation of
reference versus value semantics but has only repeated its terminology.

**Expected behavior:**
- Ask the learner to predict one small variation or explain why a value
  changes in a concrete example.
- Revisit the underlying model if the prediction exposes a gap.

**Forbidden behavior:**
- Treating fluent repetition as demonstrated understanding.
- Advancing to a harder topic without checking the current one.

**Success criteria:** Progress depends on an explanation or prediction
that demonstrates the concept, not on agreement alone.

---

### Case TBC-4 — A narrower specialist wins when the workflow is specific

**Input:** "This endpoint returns 500 for one exact request. I know the
expected output and want to isolate the first divergence."

**Expected behavior:**
- Hand off to `debug-coach`, whose observed-failure protocol is a more
  precise fit than the general learning partnership.

**Forbidden behavior:**
- Starting the generic 4D sequence and ignoring the repository's
  narrower debugging workflow.
- Giving the fix directly.

**Success criteria:** The response explicitly selects `debug-coach`
and preserves the learner's request for guided diagnosis.

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

---

### Case XB-4 — problem-decoder edge cases vs. test-case-coach suite design

**Input:** "I've listed the edge cases this statement implies, and my
solution is done — should I now turn those into actual tests?"

**Expected behavior:**
- Recognize that decoding is finished and an implementation exists,
  so systematic executable test design is `test-case-coach`'s job —
  the statement-implied edge cases are input, not a finished suite.

**Forbidden behavior:**
- problem-decoder continuing past decoding into test construction.
- Treating the decoded edge-case list as already being a justified
  test suite, skipping expected-output prediction and minimization.

**Success criteria:** The transition from statement-reading to
executable test design is handled by `test-case-coach`, with the
decoded edge cases used as raw material rather than a substitute for
its protocol.

---

### Case XB-5 — dsa-tutor's closing cousin step vs. a full transfer session

**Input (end of a dsa-tutor session):** The learner has received the
session's single cousin problem and says "actually, I want to go
deeper — how do I recognize this pattern in the wild, and when does
it not apply?"

**Expected behavior:**
- Hand off to `pattern-transfer-coach` explicitly rather than
  expanding dsa-tutor's closing step into a full transfer protocol.

**Forbidden behavior:**
- dsa-tutor improvising recognition-signal and near-miss coaching
  inline, duplicating the specialist skill.
- Handing over a second or third cousin problem inside the dsa-tutor
  session.

**Success criteria:** The response names the handoff; the deeper
abstraction work happens under `pattern-transfer-coach`'s protocol.

---

### Case XB-6 — debug-coach's regression step feeds test-case-coach, not the reverse

**Input:** A debug-coach session has just closed: fix verified,
smallest failing input known, one extra regression input named. The
learner asks for "proper test coverage now."

**Expected behavior:**
- Hand off to `test-case-coach` for suite design, carrying the
  smallest failing input forward as a permanent regression case.

**Forbidden behavior:**
- Re-running the bug-isolation pipeline as a substitute for suite
  design.
- test-case-coach discarding or re-deriving the smallest failing
  input instead of preserving it.

**Success criteria:** Suite design proceeds under `test-case-coach`
with the debug session's smallest failing input retained as a
labeled regression case.

---

### Case XB-7 — code-review-coach vs. debug-coach entry point

**Input:** "This module hasn't broken, but I don't trust it — can
you help me review it carefully and learn what to look for?"

**Expected behavior:**
- Recognize that no expected-vs-actual failure has been observed, so
  this is guided review practice, not a debugging session — inspect
  for risks under `code-review-coach`'s protocol.
- If a concrete failure emerges during the review, hand off to
  `debug-coach` at that point with the failing input.

**Forbidden behavior:**
- Starting debug-coach's pipeline (expected vs. actual, smallest
  failing input, first divergence) with no observed failure to
  chase.

**Success criteria:** Review proceeds one concern at a time; any
debugging happens only after a concrete failure appears, via a named
handoff.

---

### Case XB-8 — a review finding's verification vs. systematic suite design

**Input (end of a review finding):** "That regression test idea is
good — actually, can we build out full test coverage for this module
now?"

**Expected behavior:**
- Name the handoff to `test-case-coach` for suite design, carrying
  the finding's verification idea forward as raw material.

**Forbidden behavior:**
- code-review-coach expanding one verification idea into full
  input-space partitioning and suite minimization inline.
- test-case-coach re-running the review instead of designing the
  suite.

**Success criteria:** Suite design proceeds under `test-case-coach`;
the review session contributes its verification ideas without
absorbing the suite-design protocol.

---

### Case XB-9 — a review's performance lens vs. a complexity-only session

**Input (mid-review):** "Forget the rest of the review for now — I
just want to derive exactly what the time complexity of this
function is."

**Expected behavior:**
- Recognize that complexity derivation has become the sole question
  and name the handoff to `complexity-coach`, rather than deriving
  Big-O inside the review session.

**Forbidden behavior:**
- code-review-coach running complexity-coach's derivation drill
  (loop bounds, recurrences, degenerate inputs) inline.
- Dismissing the complexity question instead of routing it.

**Success criteria:** The derivation happens under
`complexity-coach`'s protocol; the review session can resume
afterward if other concerns remain.

---

## `specification-coach`

### Case SP-1 — A vague request produces one ambiguity, not a specification

**Input:** "Add CSV export to the orders page."

**Relevant learner state:** No further context supplied; nothing
built yet.

**Expected behavior:**
- A single response asking about the highest-impact unresolved
  ambiguity — the one whose plausible answers diverge most in
  observable behavior.
- Behavior is probed before fields, storage, or delivery mechanism.

**Forbidden behavior:**
- Producing a complete specification, PRD, or template up front.
- Inventing requirements the request never implied (authentication,
  audit logging, background jobs, localisation, retry policies).
- Naming a framework, library, schema, or architecture.
- Writing implementation code.

**Success criteria:** The first response contains exactly one
question about one ambiguity, and no requirement the learner did not
state.

---

### Case SP-2 — One question per response, never a clarification checklist

**Input:** "Here's the issue — ask me whatever you need to know."

**Expected behavior:**
- One focused question per response, on the single most blocking
  unknown.
- Later concerns are held silently and raised when they become the
  highest-impact open item.

**Forbidden behavior:**
- Delivering five or ten clarification questions in one message.
- Presenting "the remaining questions" as a list at any point.
- Ending each message with a recap or a repasted running
  specification.

**Success criteria:** No response in the exchange contains more than
one question, and no list of pending questions appears.

---

### Case SP-3 — A vague adjective is challenged, not interpreted

**Input:** "The export should be fast."

**Expected behavior:**
- Name that the term is not yet checkable and ask what someone would
  have to observe for it to hold — a threshold, an example, or an
  explicit interpretation.
- The interpretation that survives is the learner's.

**Forbidden behavior:**
- Accepting "fast" as an acceptance criterion.
- Supplying a threshold ("under 2 seconds") the learner never chose.
- Rejecting the whole request instead of the single vague term.

**Success criteria:** The vague term is either replaced by an
observable condition the learner stated, or recorded as an open
question — never silently resolved by the model.

---

### Case SP-4 — Conflicting decisions are surfaced, not silently resolved

**Input:** Learner has said the export must respect the page's active
filters, and later says finance needs every order for the quarter
regardless of what is filtered.

**Expected behavior:**
- Name the exact conflict between the two stated decisions.
- Ask the learner which behavior takes priority, or whether both are
  needed as distinct paths.

**Forbidden behavior:**
- Quietly choosing one and carrying it forward.
- Merging both into an invented compromise requirement.
- Continuing to build criteria on top of an unresolved contradiction.

**Success criteria:** The contradiction is stated explicitly and
resolved by a learner decision before any dependent acceptance
criterion is written.

---

### Case SP-5 — Implementation choice is kept out of the behavioral specification

**Input:** "Should this use a background job and store the file in
S3?"

**Relevant learner state:** No constraint has been stated that pins
down delivery mechanism.

**Expected behavior:**
- Distinguish the implementation choice from the behavioral
  requirement, and redirect to the observable behavior that would
  constrain it (what the user sees, how long they wait, what happens
  on failure).
- A mechanism enters the specification only where a stated constraint
  requires it.

**Forbidden behavior:**
- Selecting an architecture, queue, storage backend, or API shape
  before behavior creates that pressure.
- Recording an implementation choice as a requirement.

**Success criteria:** The specification contains observable behavior
and stated constraints; internal mechanism appears only where the
learner's constraints demanded it.

---

### Case SP-6 — Acceptance criteria are authored from learner decisions

**Input:** Learner has decided the export respects active filters and
excludes internal notes, and asks "so what are the acceptance
criteria?"

**Expected behavior:**
- Ask the learner to state what someone could observe to confirm one
  already-decided behavior, one criterion at a time.
- Each criterion is traceable to a decision the learner made or
  explicitly approved.

**Forbidden behavior:**
- Generating a block of acceptance criteria for the learner to
  approve by nodding.
- Including criteria for behavior the learner never decided.
- Forcing every criterion into Given/When/Then ceremony.

**Success criteria:** Every retained criterion is observable and maps
back to a stated learner decision; none originated with the model.

---

### Case SP-7 — Smallest verifiable slice, not a project plan

**Input:** "Okay, so where should implementation start?"

**Expected behavior:**
- Ask which coherent part could be implemented and verified on its
  own, first.
- Accept one slice; the rest stays unsequenced.

**Forbidden behavior:**
- Producing a multi-phase delivery plan, milestone list, or estimate.
- Designing internal architecture in order to identify the slice.
- Expanding a bounded feature into a program of work.

**Success criteria:** Exactly one first slice is identified, chosen
by the learner, with no project plan or architecture attached.

---

### Case SP-8 — Learner-authored artifact and explicit handoffs

**Input:** All blocking ambiguities are resolved and the learner asks
to write it up.

**Expected behavior:**
- The learner restates the agreement; the coach may organise and
  lightly edit it into the specification artifact.
- Unresolved non-blocking unknowns appear under `Open questions`.
- Completion names the handoffs: implementation may begin from the
  approved specification, implemented code goes to
  `code-review-coach`, a systematic suite to `test-case-coach`, a
  concrete failure to `debug-coach`.

**Forbidden behavior:**
- Filling unresolved gaps with plausible-sounding requirements.
- Populating sections with invented filler for completeness.
- Writing the implementation.

**Success criteria:** Every behavioral decision in the artifact
traces to something the learner stated or approved, gaps are visible
rather than guessed, and the handoffs are named.

---

### Case SP-9 — A direct implementation request is not absorbed into coaching

**Input:** "Just build the CSV export for me — I don't want to work
through it."

**Expected behavior:**
- State plainly that this Socratic skill is not the mode being
  requested, rather than forcing coaching onto a direct service
  request.

**Forbidden behavior:**
- Silently starting a coaching session anyway.
- Pretending the request was for a specification.
- Delivering the implementation under this skill.

**Success criteria:** The mismatch is named plainly and briefly; the
learner is not walked through a protocol they declined.

---

### Case XB-10 — specification-coach vs. code-review-coach entry point

**Input:** "We haven't written any of this yet — I just have a vague
feature request and I need it defined before anyone codes."

**Expected behavior:**
- Recognize that no code, diff, or PR exists to review, so this is
  pre-implementation definition under `specification-coach`.
- Once implementation exists, the diff goes to `code-review-coach`.

**Forbidden behavior:**
- Reviewing hypothetical or imagined code that does not exist.
- Running code-review-coach's contract-and-lens protocol against an
  unbuilt feature.

**Success criteria:** Definition proceeds under
`specification-coach`; review begins only once real code exists, via
a named handoff.

---

### Case XB-11 — acceptance criteria vs. systematic test design

**Input (end of a specification session):** "These six criteria are
good — now can we build out full test coverage for the feature?"

**Expected behavior:**
- Name the handoff to `test-case-coach`, carrying the acceptance
  criteria forward as raw material once an approach or implementation
  exists.

**Forbidden behavior:**
- specification-coach running input-space partitioning, boundary
  representative selection, and suite minimization inline.
- test-case-coach designing a suite for behavior that has no
  implementation or approach behind it yet.

**Success criteria:** Suite design happens under `test-case-coach`
against something that exists; the specification contributes its
criteria without absorbing the suite-design protocol.

---

### Case XB-12 — unresolved desired behavior vs. a concrete bug

**Input:** "The export is returning rows the user didn't expect —
though honestly we never agreed what it was supposed to return."

**Expected behavior:**
- Separate the two: without an agreed expected behavior there is no
  expected-vs-actual mismatch to diagnose, so the desired behavior is
  settled first under `specification-coach`.
- Once expected behavior is defined and a concrete input still
  produces the wrong output, hand off to `debug-coach`.

**Forbidden behavior:**
- Starting debug-coach's pipeline against an expectation nobody has
  stated.
- Inventing the intended behavior in order to have something to
  debug against.

**Success criteria:** The specification gap is named and resolved
first; debugging begins only once a genuine expected-vs-actual
mismatch exists.

---

### Case XB-13 — feature request vs. DSA problem decoding

**Input:** "Here's a request from our product team — help me work out
exactly what it's asking for before we build it."

**Expected behavior:**
- Recognize a real-world product change request, not a DSA problem
  statement, and route to `specification-coach`.
- A pasted LeetCode-style statement in the same session would instead
  route to `problem-decoder`.

**Forbidden behavior:**
- problem-decoder applying its input/output/constraints/edge-case
  extraction to a product feature request.
- specification-coach turning an ordinary DSA statement into
  product-specification theatre.

**Success criteria:** The request is handled by the skill matching
its actual domain, and the distinction is applied on the nature of
the input rather than the phrasing of the ask.

---

## Session continuity

These cases apply to every skill that carries a "Session continuity"
section — `dsa-tutor`, `problem-decoder`, `dry-run-coach`,
`debug-coach`, `test-case-coach`, `pattern-transfer-coach`,
`specification-coach`, and `code-review-coach`. See
[`session-state/README.md`](../session-state/README.md) for the
Resume Pack concept these cases test against.

### Case SC-1 — An explicit pause request produces a Resume Pack

**Input (mid-session, any supporting skill):** "I need to stop here —
can you give me something I can paste into a new chat tomorrow?"

**Expected behavior:**
- A Resume Pack is generated, using the skill's own "Session
  continuity" field format.
- Every field reflects what actually happened in the session so far —
  no field is invented to make the checkpoint look more complete.

**Forbidden behavior:**
- Declining to checkpoint, or responding with an ordinary coaching
  question instead of a checkpoint, when the pause request was
  explicit.
- Generating a checkpoint after an ordinary response with no such
  request — checkpointing is not automatic.

**Success criteria:** A single, complete Resume Pack appears, and
nothing in it goes beyond what the session actually established.

---

### Case SC-2 — A learner hypothesis stays labeled as a hypothesis

**Input (mid-session):** Learner has proposed an approach or a
violated assumption but has not yet verified it against a trace, a
dry run, or the learner's own stated reasoning — then asks to
checkpoint.

**Expected behavior:**
- The hypothesis appears under "Current approach or hypothesis" (or
  the skill's equivalent unresolved field), explicitly marked as
  unconfirmed.

**Forbidden behavior:**
- Moving the hypothesis into "Verified so far" or an equivalent
  confirmed field.
- Wording the field so it reads as settled fact.

**Success criteria:** A reader of the checkpoint alone cannot mistake
the hypothesis for something the learner (or the coach) has confirmed.

---

### Case SC-3 — Verified learner reasoning is preserved as verified

**Input (mid-session):** Learner has completed a real dry run, named a
confirmed invariant, or otherwise established something that has
already survived a check — then asks to checkpoint.

**Expected behavior:**
- That established reasoning is recorded under "Verified so far" (or
  the skill's equivalent field), in the learner's own words or a
  close paraphrase.

**Forbidden behavior:**
- Demoting confirmed reasoning to "Still uncertain" out of excess
  caution.
- Re-deriving or rephrasing it into something more polished than what
  the learner actually established.

**Success criteria:** Confirmed reasoning is distinguishable from
hypotheses in the checkpoint, and nothing confirmed is lost.

---

### Case SC-4 — Hints already given are recorded without inventing later ones

**Input (mid-session):** Two hints have been given, at rungs 2 and 3
of the skill's escalation ladder. Learner asks to checkpoint.

**Expected behavior:**
- The "Hints already given" field records exactly the two hints given,
  at the rungs they were actually given at.

**Forbidden behavior:**
- Including a hint from rung 4 or beyond, even though the coach can
  already anticipate it.
- Omitting a hint that was actually given.

**Success criteria:** The recorded hint history matches the session
exactly — no more, no less.

---

### Case SC-5 — A pasted Resume Pack resumes from the unresolved boundary

**Input:** A new session opens with a valid, complete Resume Pack
pasted in, whose "Next step to resume from" names a specific next
question.

**Expected behavior:**
- The coach briefly orients to the recorded state without re-deriving
  it through questions.
- The first substantive response asks exactly the question (or a
  close equivalent) recorded in "Next step to resume from" — not an
  earlier question the checkpoint already answers, and not a later
  one that skips ahead.

**Forbidden behavior:**
- Re-asking for information already present in "What the learner has
  established" or "Verified so far."
- Jumping past the recorded boundary to a later stage.

**Success criteria:** The first resumed question targets exactly the
unresolved boundary the checkpoint names.

---

### Case SC-6 — A resumed session still asks one question at a time

**Input:** A new session opens with a valid Resume Pack from a session
that had substantial recorded state (multiple established items,
several hints given).

**Expected behavior:**
- The orientation and the first question are delivered without
  stacking multiple questions or re-litigating every recorded field
  out loud.
- Every response after resuming still follows the originating skill's
  own "Strict response behavior" (or equivalent) constraint.

**Forbidden behavior:**
- Treating the resumed session as license to ask several questions at
  once "to catch up."
- Producing a long recap of the entire checkpoint before asking
  anything.

**Success criteria:** The resumed session reads like a continuation of
the same disciplined, one-question-at-a-time session, not a reset with
extra preamble.

---

### Case SC-7 — An unconfirmed mistake stays unconfirmed across the checkpoint

**Input (mid-session):** An observed failure exists, but the learner
has not yet explained why they made the decision that caused it.
Learner asks to checkpoint.

**Expected behavior:**
- "Confirmed mistake, if any" reads "None yet" (or the skill's
  equivalent), even though a failure has been observed.
- The observed-but-unexplained failure may appear elsewhere (e.g.
  "Still uncertain" or "Attempts made"), clearly marked as
  unconfirmed.

**Forbidden behavior:**
- Populating "Confirmed mistake, if any" with a root cause the learner
  never stated.
- Inventing a plausible-sounding root cause to avoid leaving the field
  empty.

**Success criteria:** No mistake-log-eligible entry exists in the
checkpoint until the learner has actually explained the root cause.

---

### Case SC-8 — A learner-confirmed root cause may be preserved

**Input (mid-session):** The learner has already explained why they
made the mistaken decision, and the coach has logged (or would log)
an entry under the existing mistake-log rules. Learner then asks to
checkpoint.

**Expected behavior:**
- "Confirmed mistake, if any" carries the already-confirmed entry
  forward, using the same category taxonomy.

**Forbidden behavior:**
- Re-deriving or rewording the root cause instead of carrying forward
  what the learner already established.
- Dropping a confirmed entry from the checkpoint.

**Success criteria:** A confirmed mistake that existed before the
pause is still present, unchanged, after the checkpoint.

---

### Case SC-9 — A checkpoint does not complete the unfinished algorithm

**Input (mid-`dsa-tutor`-session):** Learner has named a data
structure to use but hasn't worked out the update rule or the
invariant. Learner asks to checkpoint.

**Expected behavior:**
- The checkpoint records the data structure as a hypothesis and
  records the update rule and invariant as unresolved.

**Forbidden behavior:**
- The checkpoint stating the update rule, the invariant, or the
  overall algorithm on the learner's behalf.
- Near-complete pseudocode appearing anywhere in the checkpoint.

**Success criteria:** Someone reading only the checkpoint could not
reconstruct a working algorithm from it — only what the learner had
actually worked out.

---

### Case SC-10 — A checkpoint does not name an undiscovered pattern

**Input (mid-`pattern-transfer-coach`-session):** The learner has
described the maintained state but has not yet named or recognized
the underlying pattern. Learner asks to checkpoint.

**Expected behavior:**
- The checkpoint records the maintained-state description the learner
  gave, and records pattern recognition as not yet reached.

**Forbidden behavior:**
- The checkpoint naming the pattern (e.g. "sliding window") anywhere,
  even as an aid to the next session.

**Success criteria:** The pattern's name does not appear in the
checkpoint unless the learner had already said it themselves during
the session.

---

### Case SC-11 — A checkpoint does not invent why an attempt failed

**Input (mid-`debug-coach`-session):** An earlier attempt at a fix
failed, and the learner has moved on without explaining why they
think it failed. Learner asks to checkpoint.

**Expected behavior:**
- "Attempts made" records that the attempt happened and that it
  failed, without a stated reason.

**Forbidden behavior:**
- Supplying a plausible-sounding explanation for the failure that the
  learner never gave.

**Success criteria:** The checkpoint's account of the failed attempt
contains only what the learner actually said about it, including the
absence of a stated reason.

---

### Case SC-12 — A checkpoint does not smuggle in a future hint

**Input (mid-session):** The coach can clearly see what the next hint
on the escalation ladder would be, but hasn't given it yet. Learner
asks to checkpoint.

**Expected behavior:**
- "Hints already given" stops at the last hint actually delivered.
- "Next step to resume from" names the next question to ask, not the
  content of the next hint.

**Forbidden behavior:**
- Including the next rung's hint content anywhere in the checkpoint,
  even framed as "for reference" or "so the next session doesn't have
  to re-derive it."

**Success criteria:** Nothing in the checkpoint gives the resumed
session information the paused session hadn't actually delivered yet.

---

### Case SC-13 — A resumed session treats a checkpointed hypothesis as unverified

**Input:** A new session opens with a Resume Pack whose "Current
approach or hypothesis" field contains a plausible-sounding but
unconfirmed idea.

**Expected behavior:**
- The resumed coach treats the hypothesis as something to verify, not
  as established — e.g. by continuing toward the verification step the
  original skill would have required.

**Forbidden behavior:**
- Building on the hypothesis as if it were already confirmed.
- Skipping the verification the skill would normally require before
  accepting it.

**Success criteria:** The resumed session applies the same
verification discipline to a checkpointed hypothesis that it would
apply to a hypothesis stated fresh.

---

### Case XB-14 — mock-interviewer declines checkpoint/resume semantics

**Input (mid-timed-mock-interview):** "Can you save my progress so I
can finish this interview tomorrow?"

**Expected behavior:**
- Decline to produce a Resume Pack in `mock-interviewer`'s own voice —
  the mode does not carry a hint-history checkpoint, consistent with
  its mode contract.
- Offer the honest alternative: end the timed attempt now and give the
  structured end-of-session feedback early, or restart a fresh timed
  attempt later.

**Forbidden behavior:**
- Generating a Resume Pack that would let a future session resume
  mid-interview with hint history intact — that would quietly
  reintroduce dsa-tutor-style scaffolding into a mode built to avoid
  it.
- Silently switching into dsa-tutor's coaching mode to accommodate the
  request without saying so.

**Success criteria:** No interview-hint-ladder checkpoint is produced;
if the learner wants scaffolded continuation instead, the response
names the explicit handoff to `dsa-tutor` rather than blending modes.

---

### Case XB-15 — complexity-coach has no session-continuity behavior to invoke

**Input (mid-`complexity-coach`-session, derivation not yet
complete):** "Save where we are, I need to finish this later."

**Expected behavior:**
- Give the learner a brief, honest, learner-grounded summary of the
  derivation state actually reached so far — e.g. which loop bounds
  or recursive calls have been identified, and which haven't — without
  claiming this is a Resume Pack the skill has a defined format for.
- The Circuit breaker above still governs the summary exactly as it
  governs any other response in this skill: nothing about a final
  Big-O appears unless the learner already stated and justified it.

**Forbidden behavior:**
- Completing or advancing the unfinished derivation because the
  learner is pausing — a pause request is not licence to do the
  remaining reasoning for them.
- Stating, implying, or filling in the loop bound, recurrence, or
  final complexity the learner hasn't yet derived themselves.
- Fabricating a "Resume Pack" structure, or otherwise presenting the
  summary as a formal checkpoint, for a skill whose `SKILL.md` does
  not define one.

**Success criteria:** The learner gets an honest account of where
their own derivation stood — and nothing more — with the unfinished
part left genuinely unfinished, not resolved on their behalf and not
packaged as a checkpoint the skill doesn't have.

---

## `learn-codebase-coach`

### Case LCC-1 — Explore mode requires prediction before explanation

**Input:** "Teach me how requests flow through this repository."

**Relevant learner state:** The repository is available, but the
learner has not yet inspected an entry point or stated a prediction.

**Expected behavior:**
- Ask the learner to select or inspect one concrete entry point.
- Ask for a prediction about the next component before explaining the
  flow.
- Require repository evidence and a learner-authored explanation
  before confirming the model.

**Forbidden behavior:**
- Dumping a complete architecture tour.
- Naming every relevant file before the learner searches.
- Treating a plausible prediction as confirmed without code evidence.

**Success criteria:** The learner states a prediction, checks it
against a specific artifact, and explains what changed in their model.

### Case LCC-2 — Build mode keeps implementation ownership with the learner

**Input:** "Help me learn this codebase by adding this small feature."

**Relevant learner state:** A real change request and repository exist;
no implementation has been attempted.

**Expected behavior:**
- Clarify the artifact and choose an explicit testing policy.
- Decompose only the next small implementation step.
- Have the learner write the code and then inspect the resulting diff.

**Forbidden behavior:**
- Writing the feature on the learner's behalf.
- Quietly selecting a testing policy.
- Skipping from task description to a finished patch.

**Success criteria:** The learner authors the implementation, can
explain the touched path, and verifies the change under the selected
testing policy.

---

## `learn-by-googling`

### Case LBG-1 — Primary sources before synthesis

**Input:** "Help me learn how Raft leader election works by Googling
it myself."

**Relevant learner state:** No sources have been collected.

**Expected behavior:**
- Turn the topic into a focused research question.
- Ask the learner to find an original paper or authoritative
  documentation first.
- Evaluate source authority and evidence before synthesizing a model.

**Forbidden behavior:**
- Giving a complete explanation from memory before the search.
- Treating search-result snippets as sufficient evidence.
- Presenting uncited claims as settled facts.

**Success criteria:** The learner identifies a primary source, extracts
supported claims, and connects each major claim to a citation.

### Case LBG-2 — Conflicting sources trigger comparison, not averaging

**Input:** Two credible sources appear to disagree about a technical
tradeoff.

**Relevant learner state:** The learner has summarized both claims but
has not compared their scope, date, definitions, or evidence.

**Expected behavior:**
- Ask the learner to compare publication date, authority, definitions,
  assumptions, and evidence.
- Distinguish a real contradiction from different scopes or system
  models.
- Preserve uncertainty when the evidence does not resolve it.

**Forbidden behavior:**
- Selecting the more convenient source without justification.
- Averaging incompatible claims into a false compromise.
- Hiding the disagreement in the final synthesis.

**Success criteria:** The learner can state why the sources differ,
which claim applies under which conditions, and what remains uncertain.
