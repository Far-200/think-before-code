# Changelog

All notable changes to this project are documented in this file.

The format is loosely based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Changed

- Polished the interactive demo for public visitors and refreshed its
  displayed skills list.
- Updated the GitHub Actions checkout and Python setup steps to
  Node 24-compatible major versions.

## [1.2.0] - 2026-07-17

### Added

- `test-case-coach`, a specialist skill for designing a compact,
  justified test suite for an approach or implementation the learner
  already has — input-space partitioning, boundary representatives,
  one adversarial case per fragile assumption, learner-predicted
  expected outputs before execution, suite minimization, and
  permanent regression cases for previously-found bugs.
- `pattern-transfer-coach`, a specialist skill for turning a solved
  problem into transferable knowledge — stripping the story from the
  structure, naming the maintained state or invariant, positive and
  negative recognition signals, one near-miss comparison, and exactly
  one cousin problem per round, whose solution is never revealed.
- Activation-prompt rows (`A049`–`A072`) covering both new skills —
  at least four positive and four negative/boundary cases each — plus
  new negative rows for `dsa-tutor`, `dry-run-coach`, `debug-coach`,
  `mock-interviewer`, and `problem-decoder` at their boundaries with
  the new skills.
- Behavior cases for both new skills (`TC-1`–`TC-5`, `PT-1`–`PT-4`)
  and three new cross-skill boundary cases (`XB-4`–`XB-6`) covering
  decoder-vs-test-design, tutor-vs-transfer, and
  debug-vs-regression-suite handoffs.
- Two example transcripts: `examples/test-case-session.md` and
  `examples/pattern-transfer-session.md`.
- A "Which skill should I use?" decision guide in the README.

### Changed

- The README's tutoring-flow section now describes the full eight-stage
  learning lifecycle (decode → approach → dry run → implement → debug
  → verify → test → transfer), with pointers to the specialist skill
  for each stage and an explicit note that no session must invoke
  every specialist.
- The README skills table, boundary explanation, quick start,
  repository tree, testing/validation section, release section,
  roadmap, and contributing suggestions now reflect the eight-skill
  suite.
- `dsa-tutor` now names explicit closing handoffs to
  `pattern-transfer-coach` (deeper abstraction beyond its single
  cousin problem) and `test-case-coach` (systematic suite design),
  without absorbing either specialist protocol.
- `problem-decoder` clarifies that statement-implied edge cases before
  solving belong to it, while executable test-suite construction for
  an existing approach belongs to `test-case-coach`.
- `dry-run-coach` clarifies that it traces exactly one concrete input;
  deciding which broader set of inputs to test is `test-case-coach`'s
  job.
- `debug-coach`'s completion now allows a handoff to `test-case-coach`
  for broader regression coverage after a fix is verified, explicitly
  preserving the smallest failing input as a permanent regression case
  and keeping the smallest-failing-input discipline intact.
- `scripts/validate_skills.py`'s expected-skill set now includes
  `test-case-coach` and `pattern-transfer-coach` (eight skills total).
- The CI activation-CSV check now also requires every skill directory
  to have at least one `should_activate = true` row and at least one
  `should_activate = false` row, failing with a clear per-skill
  message when either is missing; `target_skill = none` rows remain
  allowed.
- `evals/README.md` documents the new per-skill coverage requirement
  and the deliberate reuse of similar prompts as a positive case for
  one skill and a negative case for its neighbor.
- Activation row `A047`'s reason updated: standalone cousin-problem
  adaptation after a solve now routes to `pattern-transfer-coach`
  instead of being an unresolved boundary.

### Fixed

- Stale skill counts in the README ("Five complementary skills",
  "The other four learning skills") replaced with wording accurate
  for the eight-skill suite.
- The README repository tree, which omitted existing files:
  `demo/index.html` and `public/demo.gif` are now listed, alongside
  the new skill directories and example transcripts.
- The roadmap item about cousin-problem mappings, which read as if no
  transfer support existed; it now describes the still-missing curated
  mapping dataset, since per-session transfer coaching now exists.
- Normalized stray CRLF line endings in tracked text files back to
  LF, matching the repository's committed content.

## [1.1.0] - 2026-07-14

### Added

- `debug-coach`, a specialist skill for isolating bugs in a learner's
  existing code without rewriting it, following an
  expected-behavior → actual-behavior → smallest-failing-input →
  first-divergence pipeline.
- A complete, realistic tutoring transcript in
  `examples/tutoring-session.md`, replacing the previous placeholder —
  a full session on Maximum Subarray from problem statement through a
  genuine reasoning mistake, a self-corrected approach, a dry run, a
  real implementation bug, complexity derivation, a learner-confirmed
  mistake-log entry, and one cousin problem.
- An `evals/` directory containing an activation-prompt matrix
  (`activation-prompts.csv`), detailed behavioral test cases per skill
  (`behavior-cases.md`), and a README describing how the eval suite is
  currently a specification rather than an automated runner.
- A structural validator, `scripts/validate_skills.py`, checking skill
  directory layout, frontmatter correctness, naming rules, duplicate
  names, obsolete flat skill files, UTF-8 validity, and relative
  Markdown link integrity across the repository.
- A GitHub Actions workflow, `.github/workflows/validate-skills.yml`,
  running the validator and a CSV sanity check on pushes and pull
  requests.
- Cross-agent installation guidance in the README, covering Claude
  Code (project and personal), GitHub Copilot / VS Code, and
  Codex-style discovery paths, with Bash and PowerShell examples.
- Installation, testing/validation, and release-readiness sections in
  the README.

### Changed

- The README roadmap now separates genuinely completed work from
  future work, and reflects `debug-coach`'s addition.
- The README quick start now walks through cloning, choosing a skill,
  copying it into an agent's discovery directory, and what behavior to
  expect, with an example learner prompt.
- The README's skills table and repository-structure tree now include
  `debug-coach` and the new `evals/`, `scripts/`, and `.github/`
  directories.
- `dry-run-coach`'s existing scope is clarified against the new
  `debug-coach` skill: dry-run-coach covers tracing an approach with
  or without a confirmed failure yet; debug-coach starts from an
  already-observed concrete failure in existing code.

### Fixed

- Stale roadmap entries that listed already-completed work (the four
  specialist skills, mistake logging) as still pending.
- The repository-structure tree in the README, which had drifted from
  the actual repository contents.
- Installation examples in the README that referenced a nonexistent
  nested `think-before-code/skills/...` source path instead of
  `skills/...` from the repository root.

## [1.0.1] - 2026-07-13

### Fixed

- Removed the obsolete flat `skills/dsa-tutor.md` duplicate after the
  skill was moved to `skills/dsa-tutor/SKILL.md`.

## [1.0.0] - 2026-07-13

### Added

- Initial public release of Think Before Code.
- Core `dsa-tutor` skill.
- `problem-decoder`, `dry-run-coach`, `complexity-coach`, and
  `mock-interviewer`.
- Quackrates branding, README documentation, example and mistake-log
  directories.
