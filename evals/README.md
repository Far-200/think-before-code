# Evals

This directory is a human-readable, automation-ready specification for
how the skills in this repository should activate and behave, plus a
small harness (`harness/`) that can execute a representative subset of
`behavior-cases.md` against a configured model and produce an
inspectable report. The harness covers nine cases today, not the full
specification — see [Automated behavior evaluation](#automated-behavior-evaluation)
for exactly what it checks, what it doesn't, and how to run it.

## What's here

- **`activation-prompts.csv`** — a table of example learner prompts,
  each labeled with a `target_skill` (the skill being tested for that
  row) and whether it should activate for that prompt. Used for
  activation testing and negative activation testing.
- **`behavior-cases.md`** — detailed scenarios per skill describing
  expected behavior, forbidden behavior, and success criteria once a
  skill has activated. Used for behavior-constraint testing, by hand
  for the full specification and by `harness/` for the subset it runs.
- **`finder-cases.csv`** — routing cases for the
  [Find Your Coach](../find-your-coach/) page: a declared answer path
  and the skill (or honest no-match outcome) it must reach. Unlike the
  two files above, these are executed today, not just specified — see
  [Finder routing cases](#finder-routing-cases).
- **`harness/`** — the behavior-evaluation runner. See
  [Automated behavior evaluation](#automated-behavior-evaluation).

`activation-prompts.csv` and `behavior-cases.md` cover all eleven
skills, including the two software-engineering workflow skills that
sit outside the DSA lifecycle: `specification-coach` before
implementation, when the desired behaviour isn't defined yet, and
`code-review-coach` after code exists. `concept-coach` sits outside
artifact lifecycle entirely and teaches understanding rather than a
workflow. Their
boundaries against each other and against
`debug-coach`, `test-case-coach`, `complexity-coach`,
`problem-decoder`, and `dsa-tutor` are tested in the same
positive/negative pairing style as the DSA skills' boundaries.

## Activation testing

A prompt in `activation-prompts.csv` with `should_activate = true` is
a case where the skill named in `target_skill`'s frontmatter
`description` should cause an agent to select it over the other
skills in this repository, or over no skill at all.

## Negative activation testing

A row with `should_activate = false` is a case where the skill named
in `target_skill` should **not** activate for that prompt — either
because a different skill is the correct match, or because no skill
in this repository should engage at all (a generic programming
question, for instance). These rows exist specifically to catch
over-eager activation, which is just as much a defect as a skill
failing to activate when it should.

The same (or a very similar) user prompt may legitimately appear
twice: once as a positive row for the skill that should handle it,
and once as a negative row for a neighboring skill that shouldn't —
that pairing is what makes a routing boundary testable.

## Coverage requirement

Every skill directory under `skills/` must have at least one
`should_activate = true` row and at least one
`should_activate = false` row in `activation-prompts.csv` — a skill
with no negative cases has an untested activation boundary. Rows
with `target_skill = none` remain allowed (they test that _no_ skill
engages) but don't count toward any skill's coverage.

This rule, along with the CSV's shape, unique ids, and valid
`target_skill` values, is enforced by
[`scripts/validate_evals.py`](../scripts/validate_evals.py). CI runs
that script, so you can check the same rules before pushing:

```bash
python scripts/validate_evals.py
```

## Behavior constraints

Each case in `behavior-cases.md` assumes the correct skill has already
activated, and checks what happens next: does the tutor ask one
question at a time, withhold code appropriately, avoid inventing a
mistake's root cause, and so on. These are the rules a human reviewer
(or, eventually, an automated grader reading model output against
`expected behavior` / `forbidden behavior` pairs) should check for.

## Finder routing cases

`finder-cases.csv` tests a different thing from the two files above.
Activation and behavior cases describe what a _model_ should do;
finder cases describe what the deterministic router in
[`find-your-coach/`](../find-your-coach/) does. There is no model in
that path at all — the page walks a declared tree in
`find-your-coach/routes.json` — so these cases can be, and are,
checked automatically on every push.

The schema is fixed:

```text
id,path,expected_result,reason
```

- **`id`** — a stable case id (`F001`-style today; the format is not
  enforced, only uniqueness and non-emptiness).
- **`path`** — the option ids a visitor clicks, in order, separated by
  `>`. Option ids are unique across the whole tree, so a path reads as
  an unambiguous route: `o_start_dsa>o_dsa_stage_statement`.
- **`expected_result`** — the result id the path must land on. Skill
  results are named after the skill they recommend
  (`r_problem_decoder`); the two honest dead ends are
  `r_no_match_implementation` and `r_no_match_delivery`.
- **`reason`** — why that path belongs at that destination. Boundary
  cases say which neighbouring skill they are being distinguished
  from.

[`scripts/validate_finder.py`](../scripts/validate_finder.py) walks
every path through the real route data and fails if it stops early,
runs past a result, or arrives somewhere other than
`expected_result`. It also requires that every result and every option
in the tree is exercised by at least one case, so a new branch cannot
ship without a routing case behind it — the same spirit as the
activation coverage requirement above. Run it locally with:

```bash
python scripts/validate_finder.py
```

The cases deliberately include both no-match outcomes. A router that
can only ever recommend something is a router that will recommend
something wrong, and "Think Before Code does not do this" is a result
worth regression-testing.

## Regression testing

The activation and behavior files double as a regression baseline. If a future change to a
`SKILL.md` file causes a previously-passing case to fail — a skill
that used to correctly decline to activate now does, or a skill that
used to withhold code now reveals it early — that's a regression, and
the relevant case should be added to or checked against before merging
the change. For the harness's covered cases (see
[Automated behavior evaluation](#automated-behavior-evaluation)),
re-running it after a `SKILL.md` change is a direct way to check for
this.

## Running these checks locally today

For the 79 behavior cases the harness doesn't yet cover, and for every
activation case, a contributor can still check by hand:

1. Pick a row from `activation-prompts.csv`.
2. Paste the `prompt` into an agent configured with this repository's
   skills.
3. Confirm the skill named in `target_skill` activates (or doesn't,
   for `should_activate = false` rows) and that the reason in the
   `reason` column actually holds.
4. Pick a matching scenario from `behavior-cases.md` and confirm the
   `expected behavior` items happen and the `forbidden behavior` items
   don't, across a short simulated exchange.

## Automated behavior evaluation

[`harness/`](./harness/) is a small runner that executes a
representative subset of `behavior-cases.md`'s cases against a
configured model and writes an inspectable Markdown report. It exists
alongside the manual process above, not instead of it — 9 of the 88
cases in `behavior-cases.md` are wired into the harness today; the
rest are still checked by hand using the steps above until they're
added to [`harness/case_config.json`](./harness/case_config.json).

### What it checks

For each configured case, the harness:

1. Loads the target skill's actual `SKILL.md` (frontmatter stripped)
   as the system prompt — the same file a person would copy into their
   own agent.
2. Replays any scripted prior turns needed to establish the
   conversation state the case's `Relevant learner state` describes
   (see `case_config.json`'s `setup_turns`), then sends the case's own
   `Input`.
3. Runs cheap, deterministic checks against the response: whether a
   fenced code block appears, how many question marks are present, and
   whether a named hard-stop phrase from `dsa-tutor`'s own circuit
   breaker (e.g. "here's the solution") shows up.
4. Optionally asks an LLM judge whether the response met the case's
   `Expected behavior` / `Forbidden behavior`, and records the judge's
   own reasoning alongside its opinion.
5. Writes a Markdown report with the full transcript, both kinds of
   check, and a verdict per case.

### What it does not check

- **It does not prove educational effectiveness.** It checks whether
  one sampled response matches documented behavior in one turn (or
  short scripted exchange) — not whether a learner using the skill
  actually learns better.
- **The LLM judge is an opinion, not a verdict.** A `likely_met` or
  `likely_not_met` result reflects a judge model's classification of
  one response, shown with its own stated reasoning so a human can
  disagree with it. `needs_human_review` — the harness's default
  outcome whenever no judge is configured, the judge itself was
  unsure, or an automated check contradicts what the judge said — is
  not a failure state; it is most cases' expected outcome.
- **Automated checks are textual signals, not judgments.** A fenced
  code block appearing doesn't always mean a solution was leaked (it
  could be a small illustrative snippet after the reasoning was
  already done), and its absence doesn't guarantee compliance (a
  solution can be given entirely in prose). They exist to catch clear
  violations cheaply and to flag anything a judge's "met" verdict
  should be checked against — see `evaluate_case` in
  [`harness/checks.py`](./harness/checks.py) for exactly how the two
  are combined.
- **It samples one response per case.** Model outputs vary; a single
  run passing or failing a case is one data point, not a guarantee
  about every future response to that input.

### Running it

The harness never requires a paid API call to run — the mocked path
below is what CI and this repository's own tests use:

```bash
# Mocked: reads pre-recorded responses, no network access, no cost.
python evals/harness/run_eval.py --fixtures evals/harness/fixtures/example_run.json

# Live: calls the real Anthropic API. Requires the anthropic package,
# installed into a virtual environment rather than the system Python,
# and an API key.
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install anthropic
export ANTHROPIC_API_KEY=sk-...
python evals/harness/run_eval.py --live --model claude-sonnet-4-6

# Live, with an LLM judge opinion added to each case's report:
python evals/harness/run_eval.py --live --model claude-sonnet-4-6 --judge

# Run only specific cases:
python evals/harness/run_eval.py --fixtures evals/harness/fixtures/example_run.json --cases DT-1 DT-2
```

Never commit an API key. `ANTHROPIC_API_KEY` should be set as an
environment variable, and generated reports (which may reproduce
transcript content from a live run) are excluded from version control
via `.gitignore` — copy anything worth keeping into a reviewed
location rather than relying on the default output path.

### Reading a report

Each report opens with a summary count by verdict, then one section
per case: the case's own expected/forbidden behavior and success
criteria (quoted directly from `behavior-cases.md`, never
paraphrased into a competing description), the full transcript, the
automated-check findings, and the judge's opinion if one was
requested. A report is meant to be read, not just tallied — the
verdict counts in the summary are a starting point for a human
reviewer, not the harness's final word.

### Extending it

`harness/case_config.json` is the only file that needs an addition to
cover a new case: name the case id (it must already exist in
`behavior-cases.md`) and the skill to load, plus `setup_turns` if the
case's `Relevant learner state` describes prior conversation turns
that need to be scripted rather than a single-turn `Input`, or
`input_override` if the case's `Input` is prose describing something
(like a pasted Resume Pack) rather than literal text to send. See the
comments in `case_config.json` and the docstrings in `harness/runner.py`
for the exact contract.
