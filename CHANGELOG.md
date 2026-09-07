# Changelog

All notable changes to this project are documented in this file.

The format is loosely based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [1.8.0] - 2026-09-07

### Added

- A behavioral evaluation harness under `evals/harness/` for running selected coaching cases against fixture responses or a configured live model.
- Nine representative behavioral cases covering solution withholding, hint escalation, verification, direct-answer opt-out, debugging, code review, and Resume Pack continuity.
- Scripted conversation setup and input overrides for cases that require a specific learner state.
- Automated response checks, optional LLM-judge opinions, and inspectable Markdown reports.
- An optional Anthropic provider, isolated from the fixture-based test path.
- Unit and regression tests for case parsing, providers, checks, execution, reporting, and the CLI.

### Changed

- LLM judges now receive the actual conversation, including setup turns and the final input, rather than only the evaluation case's prose description.
- Missing fixtures and provider failures are recorded as execution errors instead of silently disappearing from reports.
- Live-evaluation installation instructions use a virtual environment.

### Validation

- 229 unit tests passed in the reviewed snapshot.
- Structural, evaluation-specification, and finder-routing validators passed.
- The fixture-based harness completed all nine configured cases.
- No live model baseline has been performed yet. Mocked results and judge opinions are not proof of educational effectiveness.

## [1.7.0] - 2026-08-15

### Added

- A new skill, `concept-coach`: a Socratic coach for building
  understanding of general programming, software-engineering,
  systems, and architecture concepts — references, recursion,
  closures, coupling, dependency injection, caching, concurrency,
  queues, consistency, and similar — for a learner who isn't solving,
  debugging, tracing, testing, specifying, or reviewing a concrete
  artifact, just trying to build a working mental model. It starts
  from the learner's own stated understanding, tests predictions
  against tiny concrete examples rather than accepting fluent
  vocabulary as proof, and hands off explicitly the moment a concrete
  workflow appears — an unsolved problem, a real bug, a real feature,
  or a real review — to the matching specialist. The general
  concept-learning gap was surfaced during review of PR #3; this
  skill is the maintainer-designed implementation of that narrower
  role.
- Activation coverage for `concept-coach`: positive cases spanning
  language semantics, DSA concepts with no concrete problem attached,
  software-engineering principles, concurrency/systems, and
  distributed-systems concepts, plus negative cases against all ten
  existing specialists explaining the actual routing distinction in
  each case, and reciprocal negative cases added to
  `pattern-transfer-coach`, `code-review-coach`, and
  `specification-coach` testing the same boundaries from their own
  side.
- Behavior cases for `concept-coach` covering inspecting learner state
  before asking, testing mental models over accepting vocabulary,
  tiny concrete examples instead of production-scale illustrations,
  adaptive escalation when a gap is genuinely prerequisite knowledge,
  the direct-answer opt-out, verification before praise, code as a
  teaching instrument rather than a deliverable, explicit handoff once
  a concrete workflow appears, and Resume Pack behavior — plus five
  cross-skill regression cases testing that the same vocabulary
  ("sliding window," "async/await," "idempotency," "coupling") routes
  differently depending on the learner's actual current task.
- `concept-coach` added to [Find Your Coach](./find-your-coach/): a
  direct "a concept I want to understand" option from the start
  question, and a matching option under "I genuinely don't know,"
  both reaching the same result — the existing honest no-match outcome
  is unchanged and updated only to stop implying concept questions are
  unsupported.
- Resume Pack support for `concept-coach`, covering established
  understanding, current hypothesis, verified predictions, unresolved
  uncertainty, hints already given, and an honest "Confirmed mistake,
  if any" field that only records a mistake the learner has actually
  explained the root cause of.
- An example `concept-coach` session transcript
  (`examples/concept-coach-session.md`) on dependency injection.

### Changed

- `scripts/validate_skills.py` now requires `concept-coach` as part of
  the repository's expected skill shape, not merely allows it.
- `pattern-transfer-coach`, `code-review-coach`, and
  `specification-coach` now name `concept-coach` as the destination
  for a generic concept question with no solved problem, code, diff,
  PR, or real feature request behind it, where their own text
  previously said no skill in this repository needed to activate.
- Documentation (`README.md`, `evals/README.md`,
  `session-state/README.md`) updated for an eleven-skill repository,
  including correcting `session-state/README.md`'s description of
  Resume Packs as infrastructure rather than referring to a specific
  skill count.

## [1.6.0] - 2026-08-08

### Added

- Session continuity for unfinished coaching sessions: a **Resume
  Pack**, a portable Markdown checkpoint that preserves the learner's
  verified reasoning, hypotheses, attempts, hint history, and any
  learner-confirmed mistake — without advancing the solution,
  completing an unfinished algorithm, naming an undiscovered pattern,
  or smuggling in a hint that hasn't actually been given yet. Generated
  only on an explicit request to pause or preserve a session ("save
  where we are," "give me something I can paste tomorrow"), never
  automatically.
- A "Session continuity" section added directly to eight `SKILL.md`
  files — `dsa-tutor`, `problem-decoder`, `dry-run-coach`,
  `debug-coach`, `test-case-coach`, `pattern-transfer-coach`,
  `specification-coach`, and `code-review-coach` — each with its own
  Resume Pack field mapping tied to that skill's own stage vocabulary
  and hint or escalation ladder, and its own resume behavior: orient
  to the recorded state, don't re-teach or re-collect what's already
  established, treat recorded hypotheses as unconfirmed, and continue
  from the recorded next step at the same hint level. The behavior is
  self-contained in each skill file, so a single copied skill
  directory keeps working without the rest of the repository present.
- `session-state/`, the repository-level reference: `README.md`
  explains the Resume Pack concept, the anti-spoiler rules, the
  relationship to `mistake-logs/`, and which skills support (and
  deliberately don't support) checkpointing; `checkpoint-template.md`
  is the canonical field-by-field format the per-skill sections are
  drawn from. Both are documentation — the runtime behavior lives in
  each skill's own file, not here.
- `examples/session-continuity-example.md`, a `debug-coach` session
  split into an interrupted Session A and a resumed Session B: a
  partial state trace and an unconfirmed violated-assumption
  hypothesis are checkpointed faithfully, the resumed session asks
  exactly the question the checkpoint names next, and no fix or root
  cause is smuggled into the checkpoint despite the coach being able
  to see where the trace was heading.
- 15 new cases in `evals/behavior-cases.md`: a `Session continuity`
  section (`SC-1` through `SC-13`) covering checkpoint generation,
  hypothesis/verified-fact separation, hint-history fidelity, mistake
  confirmation status, and resume behavior across every supporting
  skill; plus two further cross-skill boundary cases (`XB-14`,
  `XB-15`) covering `mock-interviewer`'s deliberate refusal to
  checkpoint mid-interview and `complexity-coach` having no defined
  checkpoint format to invoke.

### Changed

- README gains a "Session continuity" section explaining Resume
  Packs, when to use one, how to resume from one, and that they are
  portable Markdown rather than hidden persistent memory — linking to
  `session-state/` and the new example rather than restating the full
  specification inline.
- The README repository tree and file list now cover `session-state/`
  and `examples/session-continuity-example.md`.
- The Roadmap's "Add session-state templates for unfinished problems"
  item moves from Next to Completed.

### Excluded

- `mock-interviewer` and `complexity-coach` deliberately do not carry
  checkpoint/resume behavior. Reviving a paused mock interview with a
  hint-history checkpoint would quietly reintroduce the scaffolded
  coaching that skill's mode contract exists to keep out;
  `complexity-coach` is a short, single-focus derivation drill with no
  multi-stage state worth checkpointing. Both exclusions, and the
  reasoning behind them, are documented in `session-state/README.md`
  and exercised in `evals/behavior-cases.md` (`XB-14`, `XB-15`).

## [1.5.0] - 2026-07-31

### Added

- `find-your-coach/`, an interactive Find Your Coach page served from
  the repository's existing GitHub Pages deployment. It asks at most
  three multiple-choice questions — four on the "I genuinely don't
  know" branch, which spends one extra question working out which of
  the three main branches applies — and then names one skill to start
  with. Plain HTML, CSS, and JavaScript: no framework, no build step,
  no npm dependency, no external font or CDN asset, no analytics, no
  storage, and no model call. It is a routing interface, not a hosted
  tutor.
- Deterministic routing across all ten skills, declared in
  `find-your-coach/routes.json` rather than hard-coded in DOM logic.
  Eight questions and thirty-six options traverse to twelve results;
  every skill under `skills/` is reachable as a primary
  recommendation, and question, option, and result ids are stable and
  machine-readable so a route can be written down and tested.
- A result card carrying the reason that skill fits, a copyable
  starter prompt with accessible copied-state feedback, a relative
  link to the skill's `SKILL.md`, and — where one exists — the common
  handoff that usually follows it.
- Two honest no-match outcomes. Asking for the implementation to be
  written, or for a complete refactor or rewrite handed back, ends in
  a result explaining that Think Before Code currently provides
  coaching modes rather than implementation delivery or complete
  rewrites. Neither invents a skill link, and the validator enforces
  that: a no-match result carrying a `skill` or `starter_prompt`
  field is an error.
- `evals/finder-cases.csv`, 30 routing cases in a fixed
  `id,path,expected_result,reason` schema, where `path` is the option
  ids a visitor clicks, separated by `>`. Coverage includes one
  successful path to each of the ten skills, both no-match outcomes,
  the deepest four-question route, and the neighbouring boundaries
  that are easiest to get wrong: raw statement versus guided solving,
  approach tracing versus debugging, observed failure versus review,
  vague requirements versus existing-code review, systematic test
  design versus concrete debugging, and coaching versus
  implementation delivery.
- `scripts/validate_finder.py`, a standard-library validator for the
  route data. It checks the file parses and the required structures
  exist, requires unique question, option, and result ids, rejects
  cycles and dead ends, requires every question and result to be
  reachable from the start, requires every skill result to name a
  real skill directory and carry a non-empty reason and starter
  prompt, confirms all ten skills appear as primary results, checks
  that `handoff` and `closest_skill` references name real skills, and
  verifies that every relative `../skills/<name>/SKILL.md` link the
  page constructs resolves on disk. It then walks every case in
  `evals/finder-cases.csv` through the real route data and fails if a
  path stops on a question, runs past a result, or arrives somewhere
  other than its `expected_result` — and requires every option and
  every result to be exercised by at least one case, so a new branch
  cannot ship without a routing case behind it. Like the other
  validators, it reports every problem it finds rather than stopping
  at the first.
- `tests/test_validate_finder.py`, 59 `unittest` cases covering the
  validator's failure paths as well as its success path: cycles,
  unreachable branches, duplicate ids, option counts outside the
  allowed range, no-match results dressed up as recommendations,
  unresolvable skill links, and routing cases that stop early, run
  past a result, or reach the wrong destination. Fixtures are written
  to temporary directories, matching the existing suites.

### Changed

- The README leads with a centred "Not sure where to start? Find your
  coach →" call to action, placed after the introductory paragraph and
  before "Why this exists", and Quick Start step 2 now sends
  uncertain visitors to the finder before the file paths. The textual
  "Which skill should I use?" decision guide is retained as the
  accessible fallback, with one added line noting that the finder asks
  the same questions interactively and that the list keeps working
  without JavaScript.
- The README repository tree, file list, and testing section now
  cover `find-your-coach/`, `evals/finder-cases.csv`,
  `scripts/validate_finder.py`, and `tests/test_validate_finder.py`,
  and document `python scripts/validate_finder.py` as a locally
  runnable check alongside the existing two.
- `.github/workflows/validate-skills.yml` additionally runs
  `python scripts/validate_finder.py --root .`. The existing compile,
  unit-test, skill-validation, and activation-eval steps are
  unchanged.
- `evals/README.md` documents `finder-cases.csv`, its schema, and the
  validator that executes it, and draws the distinction that matters:
  the activation and behavior files specify what a _model_ should do
  and are still checked by hand, while the finder cases describe a
  deterministic router and are executed on every push.

## [1.4.1] - 2026-07-31

### Added

- `scripts/validate_evals.py`, a standard-library validator for
  `evals/activation-prompts.csv`. It carries every rule that
  previously ran only inside GitHub Actions — expected header, per-row
  column count, unique ids, `target_skill` matching a real skill
  directory (or `none`), `should_activate` of exactly `true` or
  `false`, non-empty prompts and reasons, and at least one positive
  and one negative activation row per skill — and can now be run
  locally with `python scripts/validate_evals.py`.
- `tests/`, a `unittest` suite covering both validation scripts: 64
  tests exercising failure paths as well as success paths, using
  fixtures written to temporary directories. No third-party test
  framework, no network access, and nothing written to the real
  repository.
- Two activation-CSV rules that CI never enforced: a row's `id` must
  be non-empty, and validation now fails when `skills/` is absent
  rather than silently reporting complete coverage over no skills.

### Changed

- Activation-eval validation is no longer implemented inside
  `.github/workflows/validate-skills.yml`. The workflow's inline
  Python program is replaced by a call to the new script, so CI
  orchestrates checks instead of containing them, and the rules
  enforced on a pull request are exactly the rules a contributor can
  run before pushing.
- CI additionally runs `python -m unittest discover`, and its compile
  check now covers `scripts/` and `tests/` together.
- The eval validator reports every problem it finds rather than
  stopping at the first, matching `scripts/validate_skills.py`'s
  existing behaviour. Duplicate ids name both the repeated line and
  the line where the id was first used.
- The README installation section now documents GitHub Copilot's
  personal skills paths (`~/.copilot/skills/` and `~/.agents/skills/`)
  alongside the existing project paths, and adds an optional
  `gh skill preview` / `gh skill install` workflow, labelled as the
  public preview it currently is.
- The README testing section, repository tree, file list, and release
  version reflect the new script and test suite; `evals/README.md`
  points at the validator that enforces its coverage requirement.

### Fixed

- The nine interactive demo controls in `demo/index.html` now carry an
  explicit `type="button"`, so none of them would default to submit
  behaviour if the markup were ever placed inside a form. No visual,
  behavioural, or animation change, so `public/demo.gif` is unchanged.

## [1.4.0] - 2026-07-23

### Added

- `specification-coach`, the suite's second software-engineering
  skill and the first that runs _before_ implementation — a Socratic
  training mode for turning a vague feature request, issue, or change
  request into an implementation-ready specification: one ambiguity
  resolved per exchange, vague adjectives challenged rather than
  interpreted, contradictions surfaced instead of silently resolved,
  implementation choices kept out of the behavioural specification,
  acceptance criteria authored from learner decisions, a smallest
  independently verifiable slice, and a learner-authored artifact with
  explicit handoffs. No invented requirements, no generated PRD, no
  implementation code.
- Activation-prompt rows (`A088`–`A106`) for `specification-coach` —
  six positive and nine negative/boundary cases — plus reciprocal
  negative rows for `code-review-coach`, `test-case-coach`,
  `debug-coach`, and `problem-decoder` at their boundaries with the
  new skill.
- Behavior cases for `specification-coach` (`SP-1`–`SP-9`) and four
  new cross-skill boundary cases (`XB-10`–`XB-13`) covering
  specification-vs-review, acceptance-criteria-vs-systematic-test-
  design, unresolved-behaviour-vs-concrete-debugging, and
  feature-request-vs-DSA-decoding.
- An example transcript, `examples/specification-session.md` — a
  vague non-DSA feature request coached into a learner-authored
  specification, including a challenged vague adjective, a
  deliberately excluded non-goal, and an implementation handoff.
  Linked from the README.

### Changed

- The README hero, "Why this exists", and demo section now position
  the suite around both sides of implementation, and the demo heading
  contrasts default assistant behaviour with Think Before Code. The
  code-review-only "Beyond DSA" section is replaced by a compact
  before-and-after-implementation section covering both SWE skills
  with a recommended starting prompt for each. The existing
  eight-stage DSA lifecycle is unchanged, with neither SWE skill
  inserted into it.
- The README quick start, decision guide, skills table,
  complementary-skill explanation, repository tree, testing and
  validation section, release version, roadmap, and contributing
  suggestions now reflect the ten-skill suite (`dsa-tutor` plus nine
  more).
- `scripts/validate_skills.py`'s expected-skill set now includes
  `specification-coach` (ten skills total).
- `code-review-coach`, `test-case-coach`, `debug-coach`, and
  `problem-decoder` gained small reciprocal boundary
  clarifications: a vague pre-implementation feature request,
  acceptance criteria with no implementation behind them, undefined
  or disputed desired behaviour, and a non-DSA product change request
  all route to `specification-coach` rather than those skills. Their
  core protocols are unchanged.
- `evals/README.md` notes that both eval files now cover all ten
  skills, and names the key boundary between the two SWE skills —
  `specification-coach` before implementation, `code-review-coach`
  after code exists.
- The interactive demo (`demo/index.html`) now contrasts default
  assistant artifact dumping with learner-authored reasoning and
  judgment, demonstrates both `dsa-tutor` and `code-review-coach`,
  adds the fullscreen recording workflow, and updates the visible
  suite count and skills-folder scenario for all ten skills. The
  folder view groups `specification-coach/` and
  `code-review-coach/` under software-engineering judgment in
  pre- then post-implementation order and selects
  `specification-coach/`. The recorded `public/demo.gif` was
  re-recorded from the updated source and replaced for this release.
- The roadmap's SWE validation item is now an honest forward-looking
  item covering both `code-review-coach` and `specification-coach`;
  no real-session validation is claimed as complete.

## [1.3.0] - 2026-07-18

### Added

- `code-review-coach`, the suite's first deliberately non-DSA skill —
  a Socratic training mode for code-review judgment on existing code,
  diffs, or pull requests: contract established first, one concern
  per exchange, concrete evidence before impact, impact before
  severity, the smallest justified change with a verification idea,
  design patterns never prescribed before the underlying design
  pressure is identified, and completion via a learner-authored
  prioritized review summary. No dumped findings lists, no rewritten
  implementations.
- Activation-prompt rows (`A073`–`A087`) for `code-review-coach` —
  four positive and seven negative/boundary cases — plus reciprocal
  negative rows for `debug-coach`, `test-case-coach`,
  `complexity-coach`, and `dsa-tutor` at their boundaries with the
  new skill.
- Behavior cases for `code-review-coach` (`CR-1`–`CR-7`) and three
  new cross-skill boundary cases (`XB-7`–`XB-9`) covering
  review-vs-debugging, review-vs-systematic-test-design, and
  review-vs-complexity-only handoffs.
- An example transcript, `examples/code-review-session.md` — a
  non-DSA pull-request review including a design pattern weighed and
  declined, linked from the README.

### Changed

- The README hero and "Why this exists" now position the suite as
  covering DSA learning and software-engineering judgment, name the
  finding-dump/rewrite failure mode in AI code review, and add a
  "Beyond DSA: code-review practice" section with its own entry point,
  handoffs, and a recommended review prompt — while keeping the
  existing eight-stage DSA lifecycle intact under a "How the DSA
  tutoring flow works" heading, without inserting review as a ninth
  linear stage.
- The README decision guide, skills table, repository tree, roadmap,
  and contributing suggestions now reflect the nine-skill suite
  (`dsa-tutor` plus eight more).
- `scripts/validate_skills.py`'s expected-skill set now includes
  `code-review-coach` (nine skills total).
- `debug-coach`, `test-case-coach`, `complexity-coach`, and
  `dsa-tutor` gained small reciprocal boundary clarifications:
  a broad inspection with no observed failure, a guided code-quality
  review, and reviewing existing non-DSA application code all route
  to `code-review-coach` rather than those skills.
- The demo source's skills-folder scenario (`demo/index.html`) now
  lists `code-review-coach/`; the recorded `public/demo.gif` is
  intentionally unchanged and would need a separate re-recording to
  show it.
- `evals/README.md` notes that both eval files now cover all nine
  skills, including the non-DSA `code-review-coach` boundaries.
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
