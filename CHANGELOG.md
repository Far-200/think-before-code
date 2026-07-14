# Changelog

All notable changes to this project are documented in this file.

The format is loosely based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

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
