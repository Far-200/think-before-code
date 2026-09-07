<p align="center">
  <img src="./public/logo.png" alt="Quackrates, the Think Before Code mascot" width="180">
</p>

<h1 align="center">Think Before Code</h1>

<p align="center">
  <strong>Featuring Quackrates — your mildly disappointed Socratic coaching duck.</strong>
</p>

<p align="center">
  A portable suite of Socratic Agent Skills for learning DSA and practicing software-engineering judgment — protecting productive struggle instead of handing you the answer.
</p>

<p align="center">
  <strong><a href="https://far-200.github.io/think-before-code/find-your-coach/">Not sure where to start? Find your coach →</a></strong>
</p>

> **Not a hosted tutoring app.** Copy a skill into a compatible agent, or paste its instructions into a supported instruction field. The optional evaluation harness is a development tool, not a hosted service.

## Why this exists

AI assistants are optimized to be helpful. When a learner gets stuck, that often means receiving the optimal approach, complete code, complexity analysis, and a polished dry run before they have had a real chance to reason.

That feels productive. Usually, it is not.

The same failure mode shows up on both sides of implementation. Before it, an agent handed a vague request infers the missing requirements and starts coding against a product nobody specified. After it, an agent asked to review dumps every finding at once — or quietly rewrites the file — before the learner has noticed a single risk themselves. The work gets done; the specification judgment and review judgment never form.

_Think Before Code_ interrupts that behavior on purpose. It asks one focused question at a time, reveals only the smallest useful hint, requires manual reasoning, and treats getting stuck as part of the learning process rather than something to bypass.

## Same prompt. Different behaviour.

A default assistant dumps the artifact — the solution, the findings, the specification. Quackrates makes the learner author the reasoning.

[![Think Before Code demo](public/demo.gif)](https://far-200.github.io/think-before-code/demo/)

## Core principles

- **Ask before telling.** Inspect what the learner already understands and has attempted.
- **One hint at a time.** Give only the smallest nudge that could move the learner forward.
- **Protect productive struggle.** A concrete wrong attempt is more valuable than passive agreement with a finished solution.
- **Reasoning before code.** Withhold complete code until the learner can explain the algorithm, dry-run it, and attempt implementation.
- **Verification before praise.** Fluent terminology is not enough; reasoning must survive questions and variations.
- **Root-cause mistake logging.** Record a mistake only when the learner can explain the belief or gap that caused it.
- **Transfer through cousin problems.** After a pattern clicks, move to one structurally similar problem without solving it for the learner.

## How the DSA tutoring flow works

The suite covers the full DSA learning lifecycle:

1. **Decode the problem** — `problem-decoder` pins down inputs, outputs, constraints, and edge cases.
2. **Build an approach** — start with brute force, then discover the pattern or invariant and construct the algorithm.
3. **Dry-run manually** — `dry-run-coach` makes the learner trace a concrete input.
4. **Attempt implementation** — write code only after the reasoning is sufficiently established.
5. **Debug concrete failures** — `debug-coach` isolates the first divergence without replacing the learner's code.
6. **Verify correctness and complexity** — `complexity-coach` offers a focused derivation when needed.
7. **Design a justified test suite** — `test-case-coach` develops boundary, adversarial, and assumption-testing cases.
8. **Transfer the structure** — `pattern-transfer-coach` deepens abstraction and applies it to a cousin problem.

`dsa-tutor` coordinates the core learning path one question at a time and can hand off when a stage deserves a dedicated specialist session. A learner does not need to invoke every skill, and the tutor may move backward when an explanation sounds stronger than the learner's actual understanding.

## Beyond DSA: before and after implementation

Two skills sit outside the DSA lifecycle, on either side of the code being written:

```text
vague request
    ↓
specification-coach
    ↓
implementation
    ↓
code-review-coach
```

**`specification-coach`** runs before implementation. Bring a vague feature request, issue, or change request, and it resolves one ambiguity at a time until observable behaviour, scope, non-goals, constraints, failure behaviour, and acceptance criteria are decisions _you_ made. It ends in a learner-authored specification an implementation agent can act on. It never invents requirements or writes the implementation.

```text
Here's the feature request. Help me define it well enough to verify
before I hand it to an agent — one question at a time, and don't
write the spec for me.
```

**`code-review-coach`** runs after code exists. Bring a diff or pull request, and it helps you discover and justify findings one concern at a time: contract first, evidence before impact, impact before severity, the smallest justified change, and a verification idea. It ends in a prioritized review summary in your own words. Design patterns are never prescribed up front; "no pattern is justified" is a valid conclusion.

```text
Here's the code / diff and what it's supposed to do. Help me review
it myself, one concern at a time. Don't list the findings or rewrite
anything — ask me questions until I find and justify them.
```

Both hand off to `debug-coach` for a concrete observed failure, `test-case-coach` for systematic suite design, and `complexity-coach` for a complexity-only question.

**`concept-coach`** is orthogonal to the artifact lifecycle. It builds understanding of a DSA, programming-language, systems, software-engineering, or architecture concept when there is no concrete task behind the question. When a real problem, bug, feature, or review appears, it hands off to the matching specialist.

## Quick start

1. **Clone the repository.**

   ```bash
   git clone https://github.com/Far-200/think-before-code.git
   cd think-before-code
   ```

2. **Choose a skill.** [Find Your Coach](https://far-200.github.io/think-before-code/find-your-coach/) asks a short series of questions and gives you a matching skill and starter prompt. The core skill is [`skills/dsa-tutor/SKILL.md`](./skills/dsa-tutor/SKILL.md); ten others live alongside it. See [Which skill should I use?](#which-skill-should-i-use) for the text-only guide.

3. **Copy it where your agent looks for skills.** The repository's `skills/` directory is the canonical source. Copy or symlink the specific skill directory into your tool's discovery path. See [Installation](#installation).

4. **Invoke it naturally.** Share the problem, what you understand, what you have tried, and where your reasoning breaks.

   ```text
   Help me solve this problem, but do not give me the solution.
   Ask me one question at a time and make me explain my reasoning.
   ```

5. **Expect to do the reasoning.** One focused question, no stacked hints, and no complete code before the reasoning is ready.

A wrong attempt is useful. A copied answer wearing formal language is less useful.

## Which skill should I use?

Match where you actually are, not where you would like to be. [Find Your Coach](https://far-200.github.io/think-before-code/find-your-coach/) asks these questions interactively; this guide works without JavaScript.

| Your current situation                                          | Start with                                                           |
| --------------------------------------------------------------- | -------------------------------------------------------------------- |
| Unsolved DSA problem; want guided end-to-end help               | [`dsa-tutor`](./skills/dsa-tutor/SKILL.md)                           |
| The problem statement itself is unclear                         | [`problem-decoder`](./skills/problem-decoder/SKILL.md)               |
| Have an approach; want to trace a concrete input                | [`dry-run-coach`](./skills/dry-run-coach/SKILL.md)                   |
| Code has a concrete expected-versus-actual failure              | [`debug-coach`](./skills/debug-coach/SKILL.md)                       |
| Want to derive time and space complexity                        | [`complexity-coach`](./skills/complexity-coach/SKILL.md)             |
| Have an approach or implementation; want a justified test suite | [`test-case-coach`](./skills/test-case-coach/SKILL.md)               |
| Solved a problem; want to extract and transfer its pattern      | [`pattern-transfer-coach`](./skills/pattern-transfer-coach/SKILL.md) |
| Want timed interview pressure rather than incremental coaching  | [`mock-interviewer`](./skills/mock-interviewer/SKILL.md)             |
| Have a vague feature, issue, or change request                  | [`specification-coach`](./skills/specification-coach/SKILL.md)       |
| Have existing non-DSA code, a diff, or a PR to review           | [`code-review-coach`](./skills/code-review-coach/SKILL.md)           |
| Want to understand a concept without a concrete task            | [`concept-coach`](./skills/concept-coach/SKILL.md)                   |

If you want a complete implementation or rewrite delivered to you, use your assistant without these coaching skills. The suite deliberately does not pretend that every request belongs in a coaching mode.

## Installation

`skills/` is the canonical source directory. Each subdirectory is a self-contained Agent Skill containing a `SKILL.md` with `name` and `description` frontmatter.

Copy or symlink the skill directory into the discovery path your tool expects. Exact paths and support depend on the tool, version, and configuration; check your tool's current documentation rather than assuming universal support.

### Common discovery paths

```text
Claude Code project
.claude/skills/<skill-name>/SKILL.md

Claude Code personal
~/.claude/skills/<skill-name>/SKILL.md

GitHub Copilot / VS Code project
.github/skills/<skill-name>/SKILL.md
.claude/skills/<skill-name>/SKILL.md
.agents/skills/<skill-name>/SKILL.md

GitHub Copilot personal
~/.copilot/skills/<skill-name>/SKILL.md
~/.agents/skills/<skill-name>/SKILL.md

Codex project
.agents/skills/<skill-name>/SKILL.md

Codex personal
~/.agents/skills/<skill-name>/SKILL.md
```

The commands below run from the repository root, so the source is `skills/dsa-tutor`, not `think-before-code/skills/dsa-tutor`.

### Bash — personal Claude Code installation

```bash
mkdir -p ~/.claude/skills
cp -R skills/dsa-tutor ~/.claude/skills/dsa-tutor
```

### PowerShell — personal Claude Code installation

```powershell
New-Item -ItemType Directory -Force "$HOME\.claude\skills" | Out-Null
Copy-Item -Recurse -Force ".\skills\dsa-tutor" "$HOME\.claude\skills\dsa-tutor"
```

A symlink keeps the installed copy in sync with the repository:

```bash
mkdir -p ~/.claude/skills
ln -s "$(pwd)/skills/dsa-tutor" ~/.claude/skills/dsa-tutor
```

On Windows, symbolic links may require Developer Mode or elevated permissions, so copying is the simpler default.

### GitHub CLI skill installation

The repository also documents GitHub CLI's `gh skill` workflow for Copilot. The commands below are optional and depend on your installed GitHub CLI version and current feature availability:

```bash
gh skill preview Far-200/think-before-code dsa-tutor
gh skill install Far-200/think-before-code dsa-tutor
```

Preview the skill before installing it. GitHub's skill-installation workflow may add provenance metadata, so an installed copy need not be byte-identical to the source. Check the current GitHub CLI documentation for supported commands, flags, and installation scope.

If your tool does not use a skill-discovery directory, you can usually paste the contents of `SKILL.md` into a supported custom-instructions, project-instructions, or system-prompt field instead.

## Skills in this repository

Each skill is self-contained and can be used independently.

| Skill                                                                | What it trains                                                                                                      |
| -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| [`dsa-tutor`](./skills/dsa-tutor/SKILL.md)                           | End-to-end DSA problem solving with progressive hints and learner-established reasoning.                            |
| [`problem-decoder`](./skills/problem-decoder/SKILL.md)               | Understanding inputs, outputs, constraints, and edge cases before solving.                                          |
| [`dry-run-coach`](./skills/dry-run-coach/SKILL.md)                   | Manually tracing an existing approach on one concrete input.                                                        |
| [`complexity-coach`](./skills/complexity-coach/SKILL.md)             | Deriving time and space complexity from actual operations.                                                          |
| [`mock-interviewer`](./skills/mock-interviewer/SKILL.md)             | Timed interview practice with scarce hints and feedback at the end.                                                 |
| [`debug-coach`](./skills/debug-coach/SKILL.md)                       | Isolating a concrete failure through expected versus actual, the first divergence, and the smallest repair.         |
| [`test-case-coach`](./skills/test-case-coach/SKILL.md)               | Designing compact, justified boundary, adversarial, and assumption-testing cases.                                   |
| [`pattern-transfer-coach`](./skills/pattern-transfer-coach/SKILL.md) | Extracting a reusable pattern, identifying recognition and rule-out signals, and adapting it to one cousin problem. |
| [`specification-coach`](./skills/specification-coach/SKILL.md)       | Turning a vague request into a learner-authored, implementation-ready specification.                                |
| [`code-review-coach`](./skills/code-review-coach/SKILL.md)           | Discovering and justifying review findings without a finding dump or rewrite.                                       |
| [`concept-coach`](./skills/concept-coach/SKILL.md)                   | Building a working mental model of a programming, DSA, systems, or architecture concept.                            |

These are complementary, not redundant. `dsa-tutor` coordinates the core DSA learning path; the specialists deepen particular stages. `specification-coach` and `code-review-coach` address the two sides of implementation. `concept-coach` is independent of that lifecycle. `mock-interviewer` deliberately uses a different interaction mode and should not be blended with scaffolded coaching during an interview attempt.

## Recommended learner prompt

```text
I want to solve this problem myself.
Give me one hint at a time. Do not reveal the full approach or complete
code until I have explained the algorithm in my own words, dry-run it
manually, and attempted an implementation.

Problem:
[paste the problem]

My attempt:
[paste your reasoning or code]
```

## Example interaction

> **You:** Solve Two Sum for me.
>
> **Tutor:** Walk me through the most direct way to check whether any pair reaches the target. What would its time cost be?
>
> **You:** I would check every pair, so it would be O(n²).
>
> **Tutor:** While scanning the array once, what information from earlier positions would be useful to remember?

What did not happen: no hash map was named immediately, no code appeared, and no finished explanation replaced the learner's reasoning.

For longer examples, see the [tutoring session](./examples/tutoring-session.md), [test-case session](./examples/test-case-session.md), [pattern-transfer session](./examples/pattern-transfer-session.md), [specification session](./examples/specification-session.md), [code-review session](./examples/code-review-session.md), and [concept-coach session](./examples/concept-coach-session.md).

## Mistake logs

Mistakes are classified by root cause rather than surface symptom:

- `reasoning-error` — the logic itself was wrong.
- `pattern-recognition-error` — the wrong problem-solving pattern was chosen.
- `implementation-error` — the idea was correct, but the code did not express it correctly.
- `reading-error` — the problem or constraints were misread.
- `math-error` — arithmetic or complexity reasoning was incorrect.
- `off-by-one`.
- `state-tracking-error` — the meaning of a variable, pointer, or state was lost.

A mistake is logged only when the learner can explain why they made the decision. Typos, fatigue, accidental omissions, and isolated syntax slips are not automatically meaningful learning entries.

Confirmed entries accumulate in [`mistake-logs/`](./mistake-logs/README.md), which currently starts empty. This assumes the AI tool has write access to the repository. Otherwise, the tutor should return a ready-to-paste entry rather than pretend it saved one.

```markdown
## Mistake — [pattern name] — [category]

**What happened:**
[what you actually did, not what you should have done]

**Why:**
[the belief or gap that caused it, in your own words]

**Antidote:**
[a concrete check-in question to ask before the moment you are likely
to repeat this, phrased so it is answerable in one line]
```

## Session continuity

> Stop the session, not the reasoning.

Nine of the eleven skills — every coaching skill except `mock-interviewer` and `complexity-coach` — support **Resume Packs**: portable Markdown checkpoints for unfinished sessions, generated only on explicit request.

A Resume Pack is not hidden persistent memory. Nothing in this repository stores or retrieves one automatically. The learner carries it into another chat, agent, or context window.

It preserves what the learner actually established, separating verified reasoning from hypotheses, hints already given, and unresolved questions. Summarizing must never advance the solution: no completed algorithm, undiscovered pattern, invented invariant or root cause, or future hint.

To resume, paste the pack into a session with a supporting skill. The coach orients to the recorded state rather than restarting, treats hypotheses as unverified, and continues from the recorded next step at the same hint level.

See the [session-state reference](./session-state/README.md), [checkpoint template](./session-state/checkpoint-template.md), and [interrupted-and-resumed example](./examples/session-continuity-example.md). Each supporting skill carries its own checkpoint behaviour, so a single copied skill directory remains self-contained.

## What dsa-tutor will not do

- Dump a complete solution immediately.
- Provide complete code before the reasoning process is ready.
- Stack multiple hints in one response.
- Accept a polished explanation without testing understanding.
- Invent a root cause for a mistake.
- Praise incorrect reasoning because it sounds confident.
- Replace productive struggle with near-complete pseudocode disguised as a hint.

`mock-interviewer` is an intentional exception to some of these rules: it simulates interview conditions rather than ordinary coaching.

## What dsa-tutor can do

- Help decompose unfamiliar problems and challenge assumptions.
- Help identify invariants and state.
- Review learner-written code and isolate bugs without rewriting the entire solution.
- Help analyze time and space complexity.
- Test understanding with small variations.
- Suggest one structurally similar cousin problem.
- Maintain a meaningful, learner-confirmed mistake log.

When a stage deserves a full specialist session, `dsa-tutor` hands off rather than improvising that specialist's entire protocol. Complete code is not forbidden forever: a reference implementation becomes appropriate after the learner has completed the reasoning process and explicitly requests one.

## Repository structure

```text
think-before-code/
├── .github/
│   └── workflows/
│       └── validate-skills.yml
├── demo/
│   └── index.html
├── evals/
│   ├── README.md
│   ├── activation-prompts.csv
│   ├── behavior-cases.md
│   ├── finder-cases.csv
│   └── harness/
│       ├── case_config.json
│       ├── case_parser.py
│       ├── checks.py
│       ├── providers.py
│       ├── report.py
│       ├── run_eval.py
│       ├── runner.py
│       └── fixtures/
│           └── example_run.json
├── examples/
│   ├── code-review-session.md
│   ├── concept-coach-session.md
│   ├── pattern-transfer-session.md
│   ├── session-continuity-example.md
│   ├── specification-session.md
│   ├── test-case-session.md
│   └── tutoring-session.md
├── find-your-coach/
│   ├── app.js
│   ├── index.html
│   ├── routes.json
│   └── styles.css
├── mistake-logs/
│   └── README.md
├── public/
│   ├── demo.gif
│   └── logo.png
├── scripts/
│   ├── validate_evals.py
│   ├── validate_finder.py
│   └── validate_skills.py
├── session-state/
│   ├── README.md
│   └── checkpoint-template.md
├── skills/
│   ├── code-review-coach/
│   ├── complexity-coach/
│   ├── concept-coach/
│   ├── debug-coach/
│   ├── dry-run-coach/
│   ├── dsa-tutor/
│   ├── mock-interviewer/
│   ├── pattern-transfer-coach/
│   ├── problem-decoder/
│   ├── specification-coach/
│   └── test-case-coach/
│       └── SKILL.md
├── tests/
│   ├── harness/
│   │   ├── test_case_parser.py
│   │   ├── test_checks.py
│   │   ├── test_providers.py
│   │   ├── test_report.py
│   │   ├── test_run_eval.py
│   │   └── test_runner.py
│   ├── test_validate_evals.py
│   ├── test_validate_finder.py
│   └── test_validate_skills.py
├── .gitignore
├── CHANGELOG.md
├── LICENSE
└── README.md
```

Each directory under `skills/` contains its own `SKILL.md`. The tree omits generated caches and reports.

### Key files

- [`evals/README.md`](./evals/README.md) — evaluation specifications, coverage, and the harness contract.
- [`evals/harness/`](./evals/harness/) — case configuration, provider adapters, execution, checks, fixtures, and report generation.
- [`find-your-coach/`](./find-your-coach/) — the deterministic routing UI; [`routes.json`](./find-your-coach/routes.json) is its source of truth.
- [`session-state/README.md`](./session-state/README.md) — portable checkpoint and resume behaviour.
- [`mistake-logs/README.md`](./mistake-logs/README.md) — learner-confirmed mistake-log format.
- [`tests/`](./tests/) — standard-library unit tests for validators and the evaluation harness.
- [`.github/workflows/validate-skills.yml`](./.github/workflows/validate-skills.yml) — CI validation on pushes and pull requests.
- [`CHANGELOG.md`](./CHANGELOG.md) — release history.

## Testing and validation

The repository separates **structural correctness**, **deterministic routing**, and **model behaviour**. Passing the first two does not prove that a model will teach well.

### Structural and evaluation-specification checks

```bash
python scripts/validate_skills.py --root .
python scripts/validate_evals.py --root .
python scripts/validate_finder.py --root .
```

- `validate_skills.py` checks skill packaging, frontmatter, expected directories, UTF-8, and relative Markdown links.
- `validate_evals.py` checks the activation CSV schema, IDs, skill references, and positive/negative activation coverage.
- `validate_finder.py` checks the routing graph, reachable results, skill links, and the expected outcomes of the finder cases.

### Unit tests

```bash
python -m unittest discover
```

The suite uses Python's built-in `unittest` and mocked or fixture-based model responses. The reviewed v1.8.0 snapshot passed **229 tests**. Running these tests does not require an Anthropic API key or paid model calls.

The CI workflow runs the unit tests and the three validators on pushes and pull requests. Live model evaluations are not part of that ordinary validation path.

### Behavioral evaluation harness

The harness in [`evals/harness/`](./evals/harness/) executes a selected subset of [`evals/behavior-cases.md`](./evals/behavior-cases.md). It loads the relevant real `SKILL.md`, constructs the configured conversation, obtains a response from a fixture or live provider, and writes an inspectable Markdown report.

The initial configuration contains **nine representative cases**. Cases that require prior learner state use fixed, reviewable setup turns. Those turns are replayed as history; the harness makes **one fresh model call for the final input**. It is not yet a fully live, multi-turn tutoring simulation.

The fixture path tests the harness machinery without network access or API cost:

```bash
python evals/harness/run_eval.py --fixtures evals/harness/fixtures/example_run.json
```

To run only selected configured cases:

```bash
python evals/harness/run_eval.py --fixtures evals/harness/fixtures/example_run.json --cases DT-1 DT-2
```

The default report is written to `evals/harness/reports/latest.md`. See [`evals/README.md`](./evals/README.md) for the full configuration and evaluation contract.

#### Optional live evaluation

Live execution requires the `anthropic` package and an Anthropic API key. Use a virtual environment rather than modifying the system Python.

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install anthropic
```

**Bash:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install anthropic
```

Configure `ANTHROPIC_API_KEY` through your usual secure environment-variable setup. Do not commit keys or include them in reports. Then run:

```bash
python evals/harness/run_eval.py --live --model <your-model-id> --judge
```

Replace `<your-model-id>` with a model available to your API account. `--judge` is optional and makes additional model requests. Live execution may incur API charges; an ordinary Claude web subscription is not a substitute for an API key.

#### Interpreting results

The report preserves the conversation, automated checks, optional judge opinion, and outcome for each case. The main outcomes are `needs_human_review`, `likely_met`, `likely_not_met`, and `execution_error`.

Automated checks are heuristics, not a complete semantic grader. The optional LLM judge receives the actual conversation, including setup turns and the final input, but its judgment remains an opinion. Execution errors stay visible and counted rather than silently disappearing.

The fixture-based harness completed all nine configured cases in the reviewed snapshot. **No live model baseline has been performed for v1.8.0.** Mocked results and judge opinions are not proof of educational effectiveness.

## Release

**Version: `v1.8.0` — Behavioral Evaluation Harness.**

This version adds the initial evaluation runner, nine configured behavioral cases, fixture-based execution, optional live Anthropic execution, inspectable reports, and regression coverage. See [`CHANGELOG.md`](./CHANGELOG.md) for the release history.

The eleven coaching skills remain portable instructions. The harness is development infrastructure for evaluating their observable behaviour, not a new tutoring mode or hosted application.

## Roadmap

### Completed

- [x] Package the coaching skills in the Agent Skills directory format.
- [x] Add the core Socratic DSA tutor and specialist decoding, dry-run, complexity, debugging, test-design, pattern-transfer, and mock-interview modes.
- [x] Add learner-confirmed mistake logging and example tutoring sessions.
- [x] Add activation, negative-activation, and behavior specifications with cross-skill boundary cases.
- [x] Add structural and evaluation-specification validators with unit tests and CI.
- [x] Add the interactive Find Your Coach router, routing cases, and validation.
- [x] Add `code-review-coach` and `specification-coach` for software-engineering judgment before and after implementation.
- [x] Add Resume Packs for nine supported coaching skills.
- [x] Add `concept-coach` for general concept learning, with routing, evaluation coverage, and an example session.
- [x] Add the initial behavioral evaluation harness with nine configured cases, fixtures, optional live execution, reports, and regression tests.

### Next

- [ ] Run a small, reviewed live model baseline and document the results.
- [ ] Extend automated behavioral coverage beyond the initial nine cases.
- [ ] Add fully live, multi-turn evaluation scenarios where they provide meaningful coverage.
- [ ] Add learner-confirmed mistake-log samples from real sessions.
- [ ] Add cross-agent installation helper scripts, beyond documented paths.
- [ ] Add progress tracking across patterns.
- [ ] Add spaced-revision prompts based on per-session transfer coaching.
- [ ] Build a curated cousin-problem mapping dataset, including near-miss problems.
- [ ] Document integrations with additional AI tools and IDEs.
- [ ] Validate `code-review-coach` and `specification-coach` with real SWE sessions and refine their boundaries before adding another broader SWE domain.

## Contributing

Contributions are welcome, especially those that improve tutoring behavior, add realistic activation-boundary cases, strengthen test-design and transfer exercises, add example transcripts, improve mistake classification, or identify places where a coach reveals too much too early.

For the evaluation harness, useful contributions include reviewed case configurations, reproducible behavioral regressions, provider adapters, and better reporting. Keep mocked tests separate from live model evidence, and do not change a coaching skill merely to make a test pass.

Every contribution should preserve the central rule:

> **One hint at a time. Think before code.**

## License

This project is licensed under the MIT License. See [`LICENSE`](./LICENSE) for details.

---

_The goal was never to become good at reading solutions. It was to become good at finding them._
