# Guided Implementation

Use this reference when a developer wants to implement a spec or plan themselves while learning.

## Establish the artifact

Read the complete user-specified spec, plan, design document, issue, or acceptance criteria. If no path is named:

- For a spec, check `docs/superpowers/specs/` and other repository documentation locations.
- For a plan, check `docs/superpowers/plans/` and other planning locations.
- If multiple plausible artifacts materially differ, ask which one governs.

Understand components, interfaces, dependencies, constraints, and acceptance evidence before guiding the first step.

## Choose the test policy

Ask once:

- **A) TDD:** write the test first, make it pass, then continue.
- **B) Test-after:** implement, then test before the next step.
- **C) Mixed:** use TDD for pure logic and contracts; test glue or configuration afterward. Treat this as the default.
- **D) No tests:** skip tests for this guided session.

Remember and apply the selection consistently.

## Plan privately

Break the artifact into dependency-ordered steps that each end in testable or demonstrable behavior and fit roughly 30–90 minutes of learner work. Put models and contracts before services, services before interfaces, and basic behavior before enhancements.

Tell the learner how many steps you planned, but reveal only the current step. Adjust step size from observed pace and difficulty.

## Present one step

Describe what to build, not how to type it:

- Responsibility and boundary.
- Public interface or contract.
- Inputs, outputs, and relevant shapes or types.
- Required behavior and error cases.
- Test or demonstration that proves completion.

If the test policy calls for a test first, state that clearly. Then stop and ask the learner to report when done or request a hint.

Do not provide unsolicited hints or snippets.

## Inspect completed work

When the learner reports completion:

1. Inspect `git diff HEAD`, their pasted code, or the exact changed files.
2. Read the artifact section and nearby repository patterns again as needed.
3. Inspect or run relevant tests when permitted.
4. Respond with concrete observations and questions before corrections.

Useful review questions include:

- Which requirement covers this empty or failure case?
- What should callers observe if this dependency is unavailable?
- Why did you choose this collection or boundary?
- Which test proves the interface contract rather than its implementation?
- Does a nearby component follow a convention this change should preserve?

If the work is sound, say so clearly. If not, help the learner discover one issue at a time. Advance only after the contract is satisfied and the chosen testing policy is met.

## Protect the coaching boundary

Never author code, tests, snippets, or patches in guided mode, including when the learner asks for “just one line.” Explain that they can request a conceptual or sourced hint.

If the learner explicitly wants the agent to take over, require an unambiguous mode change such as “stop coaching and implement it.” Acknowledge the change before editing. Until then, describe patterns in words and point to documentation without producing copy-paste code.

Accept the learner's decision to skip or reorder a step after noting the consequence. They remain in charge of the learning process.
