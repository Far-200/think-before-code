# Learning Sessions

Use this reference for codebase exploration, onboarding, active recall, quizzes, and session continuity.

## Discover the learner's angle

For a new learner, ask progressively:

1. What is their goal: contribute features, fix bugs, review code, or explore generally?
2. What part of the repository catches their interest?
3. What concrete task must they accomplish?
4. How familiar are they with the main language and framework?
5. Do they prefer request tracing, tests, architecture maps, history, or experiments?

Record the result in the journal. Do not ask all questions at once when one answer can shape the next.

## Question sequence

Use the following order for new code:

1. **Prediction:** ask what a name, location, signature, or test suggests before revealing implementation.
2. **Trace:** follow one concrete request, value, event, or failure through the code.
3. **Evidence:** ask which lines or tests support the learner's explanation.
4. **Design reasoning:** ask why the code separates responsibilities or chooses this pattern.
5. **Comparison:** contrast it with another local pattern or a plausible alternative.
6. **Failure prediction:** ask what happens with empty, null, invalid, delayed, or failed inputs.
7. **Transfer:** ask the learner to apply the concept to a fresh case.

Prefer questions such as:

- What does the directory name suggest this module owns?
- Looking only at the public exports, what behavior do you expect?
- Where does this value originate, and where is it transformed?
- What evidence makes you think this function is pure or stateful?
- Why might this dependency be injected instead of constructed locally?
- What downstream behavior changes if this call fails or becomes asynchronous?
- How would you explain this component to a new contributor?

Avoid vague checks such as “Does that make sense?” Ask for an explanation, prediction, comparison, or application instead.

## Feedback ladder

When the learner answers:

- **Correct:** acknowledge briefly, then deepen with “why,” an edge case, or transfer.
- **Partly correct:** name the accurate part and ask about the missing step using a precise code location.
- **Incorrect:** do not immediately correct. Escalate through the hint ladder.
- **Stuck:** reduce scope to one expression, branch, type, or responsibility.

Use graduated scaffolding:

1. **Conceptual hint:** remind them of the relevant rule and ask them to retry.
2. **Narrowed options:** offer two or three plausible categories and identify where to look.
3. **Fill-in-the-blank:** expose the structure while withholding the key term.
4. **Explanation:** explain clearly only after the earlier levels fail, then immediately ask for a prediction in a new case.

Record high hint counts as a learning signal, not a failure.

## Calibrate difficulty

Target visible reasoning with one or two hints.

- If answers are immediate and consistently complete, move from “what” to “why,” failure modes, comparisons, and design tradeoffs.
- If the learner needs three or more hints, switch from recall to recognition, provide more local context, and split the question.
- If frustration appears, shrink the task and acknowledge the difficulty without taking over.

## Useful exploration paths

### Understand a module

Predict responsibility from the folder, inspect public exports, choose one entry point, trace it, then connect it to neighboring modules.

### Understand data flow

Identify origin, transformations, validation, persistence or output, and failure behavior.

### Understand a bug

Ask for a cause prediction, identify an observation that would distinguish hypotheses, inspect the relevant path, explain the actual cause, then ask how to prevent the class of bug.

### Prepare to contribute

Inspect nearby patterns, tests, contributor instructions, and recent history. Ask where the change belongs, what contract it must preserve, what tests prove it, and what documentation may need updating.

## Journal protocol

Use `.codex/learning-journal.md` unless `.claude/learning-journal.md` already exists.

Track:

- Focus, goals, interests, background, and preferred learning style.
- Mastery as **Confused**, **Learning**, or **Confident**.
- Open and resolved questions.
- Learner-worded insights.
- Hint counts for difficult concepts.
- Brief session logs and a next focus.
- Spaced-review dates after successful recall: 1 day, 3 days, 1 week, then 2 weeks.

Update after a mastery change, resolved confusion, notable insight, or natural 10–20 minute checkpoint. Announce meaningful saves briefly.

At the end, summarize what the learner explored, which concepts changed mastery, what remains open, and the next small option. Save before pausing.
